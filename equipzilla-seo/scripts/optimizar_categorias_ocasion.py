#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimiza SEO de las PÁGINAS DE CATEGORÍA de maquinaria de ocasión.
Salida: output/categorias_ocasion_optimizadas.csv
Conteos de producto reales, cruzando con las fichas descargadas. No inventa datos.
"""
import json, csv, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CATS = os.environ.get("CATS_JSON")
URLMAP = os.environ.get("URL_MAP", os.path.join(ROOT, "data", "ocasion_urls.tsv"))
OUT = os.path.join(ROOT, "output", "categorias_ocasion_optimizadas.csv")
SUFIJO = " · Equipzilla"
TMAX, MDMIN, MDMAX = 60, 140, 160

def limpiar(name):
    if not name: return ""
    return re.sub(r"\s+de\s+segunda\s+mano\s*$", "", name, flags=re.I).strip()

def title(cat):
    core = f"{cat} de ocasión"
    if len(core) + len(SUFIJO) <= TMAX:
        return core + SUFIJO
    core = cat
    if len(core) + len(SUFIJO) <= TMAX:
        return core + SUFIJO
    return (cat[:TMAX - len(SUFIJO) - 1].rstrip() + "…") + SUFIJO

def meta(cat, n):
    """Metadescripción neutra (sin adjetivos ligados al nombre de categoría, para
    evitar problemas de concordancia) de 140-160 caracteres."""
    head = f"{cat} de ocasión"
    cnt = f" {n} unidades disponibles." if n and n > 0 else ""
    cta = "Compara marcas y pide precio sin compromiso en Equipzilla."
    fillers = ["Máquinas revisadas y listas para trabajar.",
               "De vendedores profesionales verificados.",
               "Distintas marcas, modelos y años.",
               "Precio a consultar."]
    md = f"{head}.{cnt}"
    for fc in fillers:
        cand = md + " " + fc
        if len(cand) + 1 + len(cta) <= MDMAX:
            md = cand
        if len(md) + 1 + len(cta) >= MDMIN:
            break
    md = md + " " + cta
    if len(md) > MDMAX:
        md = md[:MDMAX].rsplit(" ", 1)[0]
    return md

def keywords(cat):
    c = cat.lower()
    ks = [f"{c} segunda mano", f"{c} de ocasión", f"comprar {c}",
          f"{c} usada", f"{c} baratas"]
    seen, out = set(), []
    for k in ks:
        if k not in seen:
            seen.add(k); out.append(k)
    return ", ".join(out)

def main():
    cats = json.load(open(CATS, encoding="utf-8"))
    # counts per slug prefix from fichas urls
    urls = [l.split("\t", 1)[1].strip() for l in open(URLMAP, encoding="utf-8") if "\t" in l]
    def count(slug):
        base = "https://equipzilla.com" + slug if slug.startswith("/") else slug
        return sum(1 for u in urls if u.startswith(base.rstrip("/") + "/"))
    out = []
    for c in cats:
        name = limpiar(c.get("name"))
        slug = c.get("slug") or ""
        n = count(slug)
        url = "https://equipzilla.com" + slug if slug.startswith("/") else slug
        subs = c.get("nsub") or 0
        intro = (f"Descubre nuestra selección de {name.lower()} de ocasión. "
                 f"{'Explora '+str(subs)+' subcategorías y ' if subs else ''}"
                 f"{n} máquinas disponibles de vendedores profesionales, revisadas y "
                 f"listas para trabajar. Compara marcas, modelos y años, y pide precio "
                 f"sin compromiso.") if name else ""
        out.append({
            "slug": slug, "url": url, "name": c.get("name"),
            "n_productos": n, "n_subcategorias": subs,
            "MetaTagTitle": title(name),
            "MetaTagDescription": meta(name, n),
            "keywords": keywords(name),
            "H1": f"{name} de ocasión" if name else c.get("name"),
            "intro_text": re.sub(r"\s+", " ", intro).strip(),
            "estado": "OK" if n > 0 else ("hub" if subs > 0 else "VACIA-revisar-noindex"),
        })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cols = ["slug", "url", "name", "n_productos", "n_subcategorias", "estado",
            "MetaTagTitle", "MetaTagDescription", "keywords", "H1", "intro_text"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in out: w.writerow(r)
    print(f"OK: {len(out)} categorías -> {OUT}")

if __name__ == "__main__":
    main()
