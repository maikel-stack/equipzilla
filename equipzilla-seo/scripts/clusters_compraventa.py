#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyword research + clustering para COMPRAVENTA de maquinaria (compra/ocasión + nuevo).

Fuente principal: datos REALES de Search Console (output/gsc_queries.csv) — las
consultas por las que el dominio ya aparece, con impresiones como proxy de volumen.
Se enriquece con semillas del catálogo (familias de máquina).

Clasifica cada keyword por:
  - familia    (plataforma, carretilla, transpaleta, excavadora, dumper, ...)
  - intencion  (TRANSACCIONAL / PRECIO / COMERCIAL / INFORMACIONAL)
Y agrupa en clusters (familia × intención) con métricas agregadas.

Salidas (output/):
  keyword_clusters_compraventa.csv   keyword, familia, intencion, impresiones, posicion, clics, pagina
  clusters_resumen_compraventa.csv   familia, intencion, n_keywords, impresiones, pos_media, top_keyword
"""
import csv, re, os
from pathlib import Path
from collections import defaultdict

OUT = Path(os.environ.get("OUT_DIR", Path(__file__).resolve().parent.parent / "output"))

# Familias de máquina (orden = prioridad de match; primera que casa gana)
FAMILIAS = [
    ("Plataformas elevadoras", r"plataforma|elevador(a|es)|tijera|articulad|telescópic|telescopic|nacela|manlift"),
    ("Carretillas elevadoras", r"carretill|toro elevador|forklift|montacargas"),
    ("Transpaletas",           r"transpalet|traspalet|pallet truck"),
    ("Apiladores",             r"apilador"),
    ("Manipuladores telescópicos", r"manipulador|telehandler|manitou"),
    ("Excavadoras",            r"excavador|miniexcavad|retroexcavad|retro\b"),
    ("Dumpers",                r"dumper|dúmper"),
    ("Grupos electrógenos",    r"electr[oó]gen|generador(a|es)?\b|electrogeno"),
    ("Compresores",            r"compresor"),
    ("Casetas y contenedores", r"caseta|contenedor|módulo|modulo|vallas|aseo portát"),
    ("Palas cargadoras",       r"pala cargador|cargadora|bobcat|minicargador"),
    ("Compactación",           r"compactad|rodillo|pisón|pison|placa vibr|bandeja"),
    ("Hormigón",               r"hormigoner|hormigón|dumper hormig"),
    ("Camiones y vehículos",   r"camión|camion|furgon|vehículo|tractor"),
    ("Martillos y herramienta",r"martillo|radial|taladr|amoladora|generador herramient"),
    ("Limpieza industrial",    r"karcher|kärcher|carcher|kartcher|barredora|fregadora|hidrolimpiad"),
    ("Torres de iluminación",  r"torre.*iluminaci|foco.*obra"),
]

INTENCION = [
    ("TRANSACCIONAL", r"segunda mano|2ª mano|2 mano|ocasi[oó]n|comprar|en venta|venta de|vender|usad[ao]s?|de ocasion"),
    ("PRECIO",        r"precio|cu[aá]nto (cuesta|vale)|coste|cotizaci|presupuesto|barat[ao]"),
    ("COMERCIAL",     r"mejor|comparativa|compar[ao]|opiniones|marcas|alquiler o compra|renting|leasing|financ"),
    ("INFORMACIONAL", r"qu[eé] es|c[oó]mo|tipos de|para qu[eé]|cu[aá]l|ventajas|mantenimiento|diferencia|manual|ficha t[eé]cnica|caracter"),
]

# Filtro: keyword pertenece a compraventa si tiene intención de compra o precio,
# o es claramente de producto (familia) con modificador de venta/uso.
COMPRAVENTA_RE = re.compile(
    r"segunda mano|2ª mano|seminuev|ocasi[oó]n|de ocasion|comprar|comprad|"
    r"en venta|venta de|vender|usad[ao]s?|renting|leasing|financ", re.I)
# Alquiler puro (sin señal de compra) se descarta del scope de compraventa.
ALQUILER_RE = re.compile(r"alquil|arrend|\brenta\b|rentar", re.I)

SPAM_RE = re.compile(r"slot|gacor|situs|judi|togel|rajadewa|maxwin|scatter|\bbola\b|thailand|pragmatic", re.I)


def clasifica(regexlist, texto, default=None):
    for etiqueta, pat in regexlist:
        if re.search(pat, texto, re.I):
            return etiqueta
    return default


def num(x):
    try: return float(str(x).replace(",", "."))
    except: return 0.0


def main():
    src = OUT / "gsc_queries.csv"
    if not src.exists():
        raise SystemExit(f"Falta {src}. Ejecuta antes scripts/gsc_pull.py")
    rows = list(csv.DictReader(open(src, encoding="utf-8")))

    keep = []
    for r in rows:
        q = r["query"]
        if SPAM_RE.search(q):
            continue
        if not COMPRAVENTA_RE.search(q):
            continue
        # descarta alquiler puro (tiene "alquiler" pero ninguna señal de compra fuerte)
        if ALQUILER_RE.search(q) and not re.search(r"segunda mano|ocasi[oó]n|comprar|usad|vender|en venta|renting|leasing|financ", q, re.I):
            continue
        fam = clasifica(FAMILIAS, q, default="Otros / genérico")
        intent = clasifica(INTENCION, q, default="TRANSACCIONAL")
        keep.append({
            "keyword": q, "familia": fam, "intencion": intent,
            "impresiones": int(num(r.get("impresiones"))),
            "posicion": round(num(r.get("posicion")), 1),
            "clics": int(num(r.get("clics"))),
        })

    keep.sort(key=lambda r: (r["familia"], -r["impresiones"]))
    with open(OUT / "keyword_clusters_compraventa.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["keyword", "familia", "intencion",
                                          "impresiones", "posicion", "clics"])
        w.writeheader(); w.writerows(keep)

    # Resumen por familia × intención
    agg = defaultdict(lambda: {"n": 0, "imp": 0, "clk": 0, "pos": [], "top": ("", 0)})
    for r in keep:
        k = (r["familia"], r["intencion"])
        a = agg[k]
        a["n"] += 1; a["imp"] += r["impresiones"]; a["clk"] += r["clics"]
        a["pos"].append(r["posicion"])
        if r["impresiones"] > a["top"][1]:
            a["top"] = (r["keyword"], r["impresiones"])
    resumen = []
    for (fam, intent), a in agg.items():
        resumen.append({
            "familia": fam, "intencion": intent, "n_keywords": a["n"],
            "impresiones": a["imp"], "clics": a["clk"],
            "pos_media": round(sum(a["pos"]) / len(a["pos"]), 1),
            "top_keyword": a["top"][0],
        })
    resumen.sort(key=lambda r: r["impresiones"], reverse=True)
    with open(OUT / "clusters_resumen_compraventa.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["familia", "intencion", "n_keywords",
                                          "impresiones", "clics", "pos_media", "top_keyword"])
        w.writeheader(); w.writerows(resumen)

    # Resumen por familia (para pillars)
    fam_agg = defaultdict(lambda: {"n": 0, "imp": 0})
    for r in keep:
        fam_agg[r["familia"]]["n"] += 1; fam_agg[r["familia"]]["imp"] += r["impresiones"]
    print(f"Keywords compraventa clusterizadas: {len(keep)}")
    print(f"Impresiones totales: {sum(r['impresiones'] for r in keep)}\n")
    print(f"{'FAMILIA (pillar)':32} {'kw':>4} {'impresiones':>12}")
    for fam, a in sorted(fam_agg.items(), key=lambda x: x[1]["imp"], reverse=True):
        print(f"{fam:32} {a['n']:>4} {a['imp']:>12}")


if __name__ == "__main__":
    main()
