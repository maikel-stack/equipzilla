#!/usr/bin/env python3
"""Keyword research de compraventa de maquinaria con DinoRank.

Lanza las semillas del nicho contra /api/v1/keyword-research, agrega el máximo
volumen por keyword, filtra al nicho de maquinaria y agrupa variantes que
pedirían el mismo artículo (mismo conjunto de tokens sin stopwords).

Salida:
  seo/dino_cache.json        — agregado crudo (cache: no repite llamadas)
  seo/keywords_master.csv    — maestro con las columnas del Sheet de mando

Uso:
    python3 scripts/seo_research.py            # usa cache si existe
    python3 scripts/seo_research.py --fresco   # fuerza llamadas nuevas
"""
import csv
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request

K = open(os.path.expanduser("~/.outbound/dinorank_key")).read().strip()
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEO = os.path.join(RAIZ, "seo")
CACHE = os.path.join(SEO, "dino_cache.json")
SALIDA = os.path.join(SEO, "keywords_master.csv")

SEMILLAS = [
    "miniexcavadora usada", "excavadora segunda mano", "comprar excavadora",
    "retroexcavadora usada", "plataforma elevadora segunda mano",
    "tijera elevadora", "carretilla elevadora segunda mano",
    "manipulador telescopico usado", "dumper segunda mano",
    "minicargadora usada", "generador electrico segunda mano",
    "caseta de obra", "contenedor maritimo comprar",
    "vender maquinaria usada", "maquinaria de obra segunda mano",
    "precio excavadora",
]

# Solo keywords del nicho: máquina + compraventa. Fuera juguetes, alquiler puro
# (lo lleva otra parte del negocio) y cosas sin relación.
NICHO = ["excavadora", "retro", "miniexcavadora", "mini excavadora", "giratoria",
         "plataforma elevadora", "tijera", "articulada", "carretilla",
         "telescopic", "telescóp", "manipulador", "dumper", "minicargadora",
         "bobcat", "kubota", "manitou", "genie", "jlg", "caterpillar", "komatsu",
         "generador", "grupo electrogeno", "grupo electrógeno", "caseta",
         "contenedor", "maquinaria", "pala cargadora", "martillo hidraulico",
         "martillo hidráulico", "rodillo compactador"]
EXCLUIR = re.compile(r"juguete|rc |teledirigid|playmobil|lego|dibujo|infantil|"
                     r"disfraz|pelicula|película|cancion|canción|"
                     # falsos positivos: el "generador de precios" de CYPE, texto
                     r"generador de precios|letras aleatorias|correos aleatorios|"
                     r"generador de ahorros|"
                     # tijeras que no son plataformas ni canciones nuestras
                     r"manos de tijera|rosario tijeras|tijeras makita|"
                     r"tijeras para cortar|"
                     # otros nichos ajenos (viviendas, mascotas, marcas locales)
                     r"casa contenedor|casas con contenedores|vivienda|"
                     r"caseta.{0,12}perro|caseta de feria|esparrago|espárrago|"
                     r"carnet de maquinista|lois|murat|margareto|villarrobledo|"
                     r"pedroñeras|skyscanner|losa de escalera|fregadero|tabique|"
                     r"solera generador", re.I)

STOP = {"de", "la", "el", "los", "las", "en", "un", "una", "para", "por",
        "con", "del", "y", "a", "se", "que", "o"}


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def clave_grupo(kw):
    """Variantes con los mismos tokens (sin stopwords) → mismo artículo."""
    toks = sorted(set(w for w in norm(kw).split() if w not in STOP))
    # unifica singular/plural burdo y las dos grafías de miniexcavadora
    toks = [re.sub(r"s$", "", t) if len(t) > 4 else t for t in toks]
    if "mini" in toks and "excavadora" in toks:
        toks = [t for t in toks if t not in ("mini", "excavadora")]
        toks.append("miniexcavadora")
    return " ".join(sorted(set(toks)))


def dino(seed):
    body = json.dumps({"keyword": seed, "country": "es", "language": "es"}).encode()
    req = urllib.request.Request(
        "https://api.dinorank.com/api/v1/keyword-research", data=body,
        headers={"X-API-Key": K, "Content-Type": "application/json"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=90).read())
    except Exception as e:
        print("  semilla", seed, "ERROR", e)
        return {}
    out = {}
    for v in d.get("data", {}).get("data", {}).get("keywords", {}).values():
        if not isinstance(v, dict) or "keyword" not in v:
            continue
        try:
            vol = int(v.get("vol") or 0)
        except (TypeError, ValueError):
            vol = 0
        try:
            comp = float(v.get("competencia") or 0)
        except (TypeError, ValueError):
            comp = 0.0
        kw = v["keyword"]
        if kw not in out or vol > out[kw][0]:
            out[kw] = (vol, comp)
    return out


def categoria(kw):
    k = norm(kw)
    for pat, cat in [
            ("miniexcavadora|mini excavadora", "Miniexcavadoras"),
            ("excavadora|retro|giratoria", "Excavadoras"),
            ("plataforma|tijera|articulada|genie|jlg|elevador", "Plataformas elevación"),
            ("carretilla|toro|fenwick", "Carretillas"),
            ("telescopic|manipulador|manitou", "Telescópicas"),
            ("dumper|minicargadora|bobcat|pala", "Dumpers y cargadoras"),
            ("generador|electrogeno", "Generadores"),
            ("caseta|contenedor|modulo", "Casetas y contenedores"),
            ("vender", "Venta (Want-to-Sell)")]:
        if re.search(pat, k):
            return cat
    return "Maquinaria general"


def intencion(kw):
    k = norm(kw)
    if re.search(r"segunda mano|usad|ocasion|comprar|venta|precio|barat", k):
        return "Comercial"
    if re.search(r"que es|como|cual|diferencia|tipos", k):
        return "Informacional"
    return "Comercial/Info"


def main():
    os.makedirs(SEO, exist_ok=True)
    if os.path.exists(CACHE) and "--fresco" not in sys.argv:
        agg = {k: tuple(v) for k, v in json.load(open(CACHE)).items()}
        print("cache:", len(agg), "keywords")
    else:
        agg = {}
        for s in SEMILLAS:
            r = dino(s)
            for kw, (vol, comp) in r.items():
                if kw not in agg or vol > agg[kw][0]:
                    agg[kw] = (vol, comp)
            print(f"  {s}: {len(r)} kw (acumulado {len(agg)})")
            time.sleep(1)
        json.dump(agg, open(CACHE, "w"), ensure_ascii=False)

    nicho = {kw: v for kw, v in agg.items()
             if any(t in norm(kw) for t in [norm(x) for x in NICHO])
             and not EXCLUIR.search(kw)}
    print(f"total {len(agg)} · nicho {len(nicho)}")

    # agrupar variantes → un artículo por grupo
    grupos = {}
    for kw, (vol, comp) in nicho.items():
        g = clave_grupo(kw)
        grupos.setdefault(g, []).append((kw, vol, comp))
    filas = []
    for g, kws in grupos.items():
        kws.sort(key=lambda x: -x[1])
        kw, vol, comp = kws[0]
        variantes = ", ".join(k for k, _, _ in kws[1:4])
        vol_grupo = sum(v for _, v, _ in kws)  # demanda total del grupo
        filas.append(dict(kw=kw, vol=vol, vol_grupo=vol_grupo, comp=comp,
                          variantes=variantes, n_var=len(kws)))
    filas.sort(key=lambda f: -f["vol_grupo"])
    # al Sheet solo lo accionable: grupos con demanda real
    filas = [f for f in filas if f["vol_grupo"] >= 40]

    with open(SALIDA, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Keyword / Tema", "Categoría", "Intención", "URL del artículo",
                    "Estado", "Volumen (DinoRank)", "Volumen grupo", "Competencia",
                    "Pos. media (GSC 90d)", "Clics (90d)", "Impresiones (90d)",
                    "Prioridad", "Notas"])
        for fl in filas:
            pr = ("🔴 Alta" if fl["vol_grupo"] >= 1000
                  else "🟠 Media" if fl["vol_grupo"] >= 250 else "🟢 Normal")
            nota = f"{fl['n_var']} variantes" + (f": {fl['variantes']}" if fl["variantes"] else "")
            w.writerow([fl["kw"], categoria(fl["kw"]), intencion(fl["kw"]), "",
                        "Pendiente", fl["vol"], fl["vol_grupo"],
                        round(fl["comp"], 2), "", "", "", pr, nota])
    print(f"{len(filas)} grupos de artículo → {SALIDA}")
    for fl in filas[:15]:
        print(f"  {fl['vol_grupo']:>6}  {fl['kw']}")


if __name__ == "__main__":
    main()
