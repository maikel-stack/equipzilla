#!/usr/bin/env python3
"""
Generador de páginas SEO programáticas para Equipzilla.

Lee data/directorio.csv y crea una landing page por cada combinación
(categoría de máquina x ciudad) que tenga proveedores reales.

Cada página incluye: <title> y meta description optimizados, un único <h1>,
intro localizada, tabla de proveedores reales, FAQ, JSON-LD (Service + BreadcrumbList)
y enlaces internos. También genera sitemap.xml e index.html.

Uso:
    python scripts/generar_paginas_seo.py
    python scripts/generar_paginas_seo.py --data data/directorio.csv --out output
"""
import argparse
import csv
import html
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

BASE_URL = "https://www.equipzilla.com"


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text


def cat_label(especialidad: str) -> str:
    """Normaliza la especialidad a una categoría legible."""
    e = especialidad.strip().lower()
    mapping = {
        "generalista": "maquinaria",
        "construcción": "maquinaria de construcción",
        "construccion": "maquinaria de construcción",
        "elevación": "plataformas elevadoras",
        "elevacion": "plataformas elevadoras",
        "plataformas elevadoras": "plataformas elevadoras",
        "grúas": "grúas",
        "gruas": "grúas",
        "industrial": "maquinaria industrial",
        "agrícola": "maquinaria agrícola",
        "agricola": "maquinaria agrícola",
    }
    return mapping.get(e, especialidad.strip().lower())


def build_faq(categoria: str, ciudad: str, n_proveedores: int):
    return [
        (
            f"¿Cuánto cuesta el alquiler de {categoria} en {ciudad}?",
            f"El precio del alquiler de {categoria} en {ciudad} depende del modelo, la "
            f"duración y los servicios incluidos (transporte, operario, seguro). Compara "
            f"presupuestos de los {n_proveedores} proveedores listados para encontrar la "
            f"mejor tarifa.",
        ),
        (
            f"¿Puedo alquilar {categoria} por días en {ciudad}?",
            f"Sí. La mayoría de empresas de {ciudad} ofrecen alquiler por día, semana o mes, "
            f"con tarifas más ventajosas en periodos largos.",
        ),
        (
            f"¿Incluye transporte el alquiler en {ciudad}?",
            f"Muchos proveedores de {ciudad} incluyen entrega y recogida en obra dentro de su "
            f"área de servicio. Confírmalo al pedir presupuesto.",
        ),
        (
            "¿Necesito formación u operario?",
            "Según el equipo, puede requerirse carnet o un operario cualificado. Varios "
            "proveedores ofrecen el servicio con operario incluido.",
        ),
    ]


def render_page(categoria: str, ciudad: str, proveedores: list, related: list) -> str:
    cat_cap = categoria[0].upper() + categoria[1:]
    title = f"Alquiler de {categoria} en {ciudad} | Equipzilla"
    if len(title) > 60:
        title = f"Alquiler de {categoria} en {ciudad}"
    meta_desc = (
        f"Compara {len(proveedores)} empresas de alquiler de {categoria} en {ciudad}. "
        f"Precios, contacto directo y disponibilidad. Pide presupuesto gratis en Equipzilla."
    )[:160]
    slug = f"alquiler-{slugify(categoria)}-{slugify(ciudad)}"
    url = f"{BASE_URL}/{slug}/"

    rows = ""
    for p in proveedores:
        web = p["web"].strip()
        web_link = f'<a href="https://{web}" rel="nofollow">{html.escape(web)}</a>' if web else "—"
        tel = html.escape(p["telefono"].strip()) or "—"
        rows += (
            f"<tr><td>{html.escape(p['empresa'])}</td>"
            f"<td>{html.escape(p['especialidad'])}</td>"
            f"<td>{tel}</td><td>{web_link}</td></tr>\n"
        )

    faq = build_faq(categoria, ciudad, len(proveedores))
    faq_html = "".join(
        f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>\n"
        for q, a in faq
    )

    related_html = "".join(
        f'<li><a href="/alquiler-{slugify(c)}-{slugify(ci)}/">Alquiler de {html.escape(c)} en {html.escape(ci)}</a></li>'
        for c, ci in related
    )

    schema = {
        "@context": "https://schema.org",
        "@type": "Service",
        "serviceType": f"Alquiler de {categoria}",
        "areaServed": {"@type": "City", "name": ciudad},
        "provider": {"@type": "Organization", "name": "Equipzilla", "url": BASE_URL},
        "offers": {"@type": "AggregateOffer", "offerCount": len(proveedores)},
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": BASE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": cat_cap, "item": f"{BASE_URL}/alquiler-{slugify(categoria)}/"},
            {"@type": "ListItem", "position": 3, "name": ciudad, "item": url},
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(meta_desc)}">
<link rel="canonical" href="{url}">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False)}</script>
</head>
<body>
<nav aria-label="breadcrumb"><a href="/">Inicio</a> › <a href="/alquiler-{slugify(categoria)}/">{cat_cap}</a> › {html.escape(ciudad)}</nav>
<main>
<h1>Alquiler de {html.escape(categoria)} en {html.escape(ciudad)}</h1>
<p>¿Buscas {html.escape(categoria)} en {html.escape(ciudad)}? Hemos reunido {len(proveedores)}
empresas de alquiler con disponibilidad en la zona. Compara servicios y contacta directamente
para pedir tu presupuesto sin compromiso.</p>

<h2>Empresas de alquiler de {html.escape(categoria)} en {html.escape(ciudad)}</h2>
<table>
<thead><tr><th>Empresa</th><th>Especialidad</th><th>Teléfono</th><th>Web</th></tr></thead>
<tbody>
{rows}</tbody>
</table>

<h2>Preguntas frecuentes</h2>
{faq_html}

<h2>También te puede interesar</h2>
<ul>{related_html}</ul>
</main>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/directorio.csv")
    ap.add_argument("--out", default="output")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    data_path = (root / args.data) if not Path(args.data).is_absolute() else Path(args.data)
    out_dir = (root / args.out) if not Path(args.out).is_absolute() else Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Agrupar proveedores por (categoria, ciudad)
    groups = defaultdict(list)
    with open(data_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ciudad = row.get("ciudad", "").strip()
            cat = cat_label(row.get("especialidad", ""))
            if not ciudad or not cat:
                continue
            groups[(cat, ciudad)].append(row)

    # Para enlaces internos relacionados
    all_combos = list(groups.keys())
    pages, sitemap_urls = [], []

    for (cat, ciudad), provs in sorted(groups.items()):
        related = [c for c in all_combos if (c[1] == ciudad or c[0] == cat) and c != (cat, ciudad)][:5]
        page_html = render_page(cat, ciudad, provs, related)
        slug = f"alquiler-{slugify(cat)}-{slugify(ciudad)}"
        (out_dir / f"{slug}.html").write_text(page_html, encoding="utf-8")
        pages.append((cat, ciudad, slug, len(provs)))
        sitemap_urls.append(f"{BASE_URL}/{slug}/")

    # sitemap.xml
    urls_xml = "\n".join(f"  <url><loc>{u}</loc></url>" for u in sitemap_urls)
    (out_dir / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls_xml}\n</urlset>\n",
        encoding="utf-8",
    )

    # index.html
    items = "\n".join(
        f'<li><a href="{s}.html">Alquiler de {html.escape(c)} en {html.escape(ci)}</a> '
        f"({n} proveedores)</li>"
        for c, ci, s, n in pages
    )
    (out_dir / "index.html").write_text(
        f"<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
        f"<title>Páginas SEO generadas — Equipzilla</title></head><body>"
        f"<h1>{len(pages)} páginas generadas</h1><ul>{items}</ul></body></html>",
        encoding="utf-8",
    )

    print(f"OK — {len(pages)} páginas en {out_dir}")
    for c, ci, _, n in pages:
        print(f"  · {c} en {ci} ({n} proveedores)")


if __name__ == "__main__":
    main()
