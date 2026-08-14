#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimiza el SEO de las fichas de MAQUINARIA DE OCASIÓN de equipzilla.com.

Entrada : catalogo_ocasion.json  (datos reales extraídos de cada ficha del sitio)
Salida  : fichas_ocasion_optimizadas.csv  (formato plantilla PrestaShop, 20 columnas)

Regla de oro: NO se inventa ningún dato. Precio, año y horas solo se usan si existen
en origen. El resto de campos SEO se derivan de nombre/marca/modelo/subcategoría/
ubicación/condición reales.

Determinista: sin llamadas a LLM, sin dependencias externas.
"""
import json, csv, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IN_JSON = os.environ.get("CAT_JSON", os.path.join(ROOT, "data", "catalogo_ocasion.json"))
URL_MAP = os.environ.get("URL_MAP", os.path.join(ROOT, "data", "ocasion_urls.tsv"))
OUT_CSV = os.path.join(ROOT, "output", "fichas_ocasion_optimizadas.csv")

SUFIJO = " · Equipzilla"
TITLE_MAX = 60
MD_MIN, MD_MAX = 140, 160

COLUMNS = ["id","name","machineCode","price","parentCategory","MetaTagTitle",
    "MetaTagDescription","keywords","canonical","description_short","description_long",
    "especificaciones","extended_info","title","title_carousel",
    "Photo1","Photo2","Photo3","Photo4","Photo5"]

def singular(frase):
    """Singulariza cada palabra significativa (heurística ES sencilla)."""
    out = []
    for w in frase.split():
        lw = w.lower()
        if len(w) > 4 and lw.endswith("es") and lw[-3] not in "aeiou":
            out.append(w[:-2])
        elif len(w) > 4 and lw.endswith("s") and lw[-2] in "aeiou":
            out.append(w[:-1])
        else:
            out.append(w)
    return " ".join(out)

def limpiar_cat(subcat):
    """'Miniexcavadoras de Segunda Mano' -> 'Miniexcavadoras'."""
    if not subcat:
        return ""
    c = re.sub(r"\s+de\s+(segunda\s+mano|ocasi[oó]n)\s*$", "", subcat, flags=re.I)
    c = re.sub(r"\s+(segunda\s+mano|ocasi[oó]n)\s*$", "", c, flags=re.I)
    return c.strip()

def clamp_title(cat_sing, marca, modelo, name):
    bm = " ".join(x for x in [marca, modelo] if x).strip()
    core_room = TITLE_MAX - len(SUFIJO)
    candidatos = []
    if cat_sing and bm:
        candidatos.append(f"{cat_sing} {bm} de ocasión")
    if bm:
        candidatos.append(f"{bm} de ocasión")
    if cat_sing and marca:
        candidatos.append(f"{cat_sing} {marca} de ocasión")
    if cat_sing:
        candidatos.append(f"{cat_sing} de ocasión")
    candidatos.append(f"{name} de ocasión")
    candidatos.append(name)
    fit = [c for c in candidatos if len(c) <= core_room]
    core = max(fit, key=len) if fit else (candidatos[0][:core_room-1].rstrip() + "…")
    return core + SUFIJO

def build_md(cat_sing, marca, modelo, ubicacion, anio, name):
    """Compone una metadescripción de 140-160 caracteres con cláusulas veraces
    genéricas, priorizando siempre el CTA final a Equipzilla."""
    cat = cat_sing or name
    bm = " ".join(x for x in [marca, modelo] if x).strip()
    sujeto = f"{cat} {bm}".strip() if bm else cat
    head = f"{sujeto} de ocasión"
    ctx = []
    if anio:
        ctx.append(f"año {anio}")
    if ubicacion:
        ctx.append(str(ubicacion).strip().capitalize())
    if ctx:
        head += " · " + " · ".join(ctx)
    cta = "Pide precio e información sin compromiso en Equipzilla."
    pool = [
        "Consulta la ficha técnica completa.",
        "Revisada y lista para trabajar.",
        "Compra con asesoramiento técnico.",
        "Factura y trato profesional.",
        "Máquina verificada.",
    ]
    md = head + "."
    used = set()
    # Añade greedily la cláusula más larga que quepa dejando hueco para el CTA,
    # hasta alcanzar el mínimo o quedarse sin cláusulas.
    while len(md) + 1 + len(cta) < MD_MIN:
        cand = [(len(c), c) for i, c in enumerate(pool) if i not in used
                and len(md) + 1 + len(c) + 1 + len(cta) <= MD_MAX]
        if not cand:
            break
        _, best = max(cand)
        used.add(pool.index(best))
        md += " " + best
    md += " " + cta
    if len(md) > MD_MAX:  # salvaguarda: recorta por palabra
        md = md[:MD_MAX].rsplit(" ", 1)[0]
    return md

def build_keywords(cat_clean, cat_sing, marca, modelo, ubicacion):
    kws, seen = [], set()
    def add(k):
        k = re.sub(r"\s+", " ", (k or "")).strip()
        if k and k.lower() not in seen:
            seen.add(k.lower()); kws.append(k)
    cl = cat_clean.lower() if cat_clean else ""
    cs = cat_sing.lower() if cat_sing else ""
    bm = " ".join(x for x in [marca, modelo] if x).strip()
    add(cl)
    add(f"{cs} segunda mano")
    add(f"{cs} de ocasión")
    add(f"comprar {cs}")
    if bm:
        add(bm); add(f"{bm} segunda mano"); add(f"{bm} ocasión")
    if marca:
        add(f"{marca.lower()} segunda mano")
    if ubicacion and cs:
        add(f"{cs} segunda mano {str(ubicacion).strip().lower()}")
    return ", ".join(kws[:10])

def build_especificaciones(spec):
    if not isinstance(spec, dict):
        return ""
    orden = ["Marca","Modelo","Año","Horas","Peso (kg)","Peso","Altura (mm)",
             "Anchura (mm)","Longitud (mm)","Ubicación","País","Nº de serie"]
    items = []
    for k in orden:
        if k in spec and spec[k] not in (None, "", []):
            items.append(f"{k}: {spec[k]}")
    for k, v in spec.items():
        if k not in orden and v not in (None, "", []):
            items.append(f"{k}: {v}")
    return " • ".join(items)

def main():
    rows = json.load(open(IN_JSON, encoding="utf-8"))
    urlmap = {}
    if os.path.exists(URL_MAP):
        for line in open(URL_MAP, encoding="utf-8"):
            if "\t" in line:
                i, u = line.rstrip("\n").split("\t", 1)
                urlmap[str(i)] = u
    out = []
    for r in rows:
        cat_clean = limpiar_cat(r.get("subcategory"))
        cat_sing = singular(cat_clean)
        marca = (r.get("brand") or "").strip() or None
        modelo = (r.get("model") or "").strip() or None
        name = (r.get("name") or "").strip()
        ubic = r.get("location")
        anio = r.get("year")
        spec = r.get("spec") or {}
        canonical = urlmap.get(str(r.get("id")), "")
        out.append({
            "id": r.get("id"),
            "name": name,
            "machineCode": r.get("reference") or "",
            "price": r.get("price") or "",
            "parentCategory": cat_clean,
            "MetaTagTitle": clamp_title(cat_sing, marca, modelo, name),
            "MetaTagDescription": build_md(cat_sing, marca, modelo, ubic, anio, name),
            "keywords": build_keywords(cat_clean, cat_sing, marca, modelo, ubic),
            "canonical": canonical,
            "description_short": r.get("desc_short") or "",
            "description_long": r.get("desc_long") or "",
            "especificaciones": build_especificaciones(spec),
            "extended_info": "",
            "title": name,
            "title_carousel": f"{cat_sing} de ocasión" if cat_sing else name,
            "Photo1": "", "Photo2": "", "Photo3": "", "Photo4": "", "Photo5": "",
        })
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for row in out:
            w.writerow(row)
    print(f"OK: {len(out)} fichas -> {OUT_CSV}")

if __name__ == "__main__":
    main()
