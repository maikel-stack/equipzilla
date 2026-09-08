#!/usr/bin/env python3
"""Empaqueta las guías SEO como sitio estático listo para Vercel.

Maikel (08/09): el blog de WordPress sigue comprometido (sirve spam a
Googlebot), así que "de mientras" las guías se publican en Vercel. Este
script deja en site/ todo lo que hace falta: índice con la marca, los
artículos de seo/articulos/, sitemap.xml, robots.txt que deja pasar a los
bots de IA (GEO) y vercel.json con URLs limpias.

El dominio final se pasa por BASE: primero el *.vercel.app que exista, y
cuando esté el CNAME, ocasion.equipzilla.com. Sitemap y canonicals se
regeneran con él; no se deja nada a mano.

Uso:  BASE=https://equipzilla-guias.vercel.app python3 scripts/publicar_guias.py
      luego:  npx vercel deploy site --prod --token $VERCEL_TOKEN
"""
import datetime as dt
import html
import json
import os
import re
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(RAIZ, "seo", "articulos")
SITE = os.path.join(RAIZ, "site")
BASE = os.environ.get("BASE", "https://equipzilla-guias.vercel.app").rstrip("/")
HOY = dt.date.today().isoformat()


def leer_meta(ruta):
    t = open(ruta, encoding="utf-8").read()
    titulo = re.search(r"<title>(.*?)</title>", t, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', t)
    fecha = re.search(r'"datePublished":"([\d-]+)"', t)
    return dict(
        titulo=html.unescape(titulo.group(1)).replace(" · Equipzilla", "").strip() if titulo else "",
        desc=html.unescape(desc.group(1)) if desc else "",
        fecha=fecha.group(1) if fecha else HOY, html=t)


def con_canonical(t, url):
    """Canonical al dominio de publicación. Si ya había uno, se sustituye."""
    t = re.sub(r'<link rel="canonical"[^>]*>\n?', "", t)
    return t.replace("</title>", '</title>\n<link rel="canonical" href="%s">' % url, 1)


def main():
    if os.path.isdir(SITE):
        shutil.rmtree(SITE)
    os.makedirs(SITE)
    guias = []
    for f in sorted(os.listdir(ORIGEN)):
        if not f.endswith(".html"):
            continue
        slug = f[:-5]
        m = leer_meta(os.path.join(ORIGEN, f))
        url = "%s/%s" % (BASE, slug)
        open(os.path.join(SITE, f), "w", encoding="utf-8").write(con_canonical(m["html"], url))
        guias.append(dict(slug=slug, url=url, **{k: m[k] for k in ("titulo", "desc", "fecha")}))

    # índice con la misma marca que los artículos
    tarjetas = "".join(
        '<a class="g" href="/%s"><h2>%s</h2><p>%s</p></a>' %
        (g["slug"], html.escape(g["titulo"]), html.escape(g["desc"][:150])) for g in guias)
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guías de compra de maquinaria de ocasión · Equipzilla</title>
<meta name="description" content="Precios reales, qué revisar antes de comprar y cómo elegir: guías de Equipzilla sobre miniexcavadoras, excavadoras, plataformas, casetas, contenedores, generadores y dumpers de segunda mano.">
<link rel="canonical" href="{BASE}/">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=IBM+Plex+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--teal:#387E7F;--oscuro:#17323A;--tinta:#14181C;--gris:#4A5560;--linea:#D9DEE4;--fondo:#FBFCFD}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--fondo);color:var(--tinta);font-family:'IBM Plex Sans',system-ui,sans-serif;line-height:1.6}}
header{{background:var(--oscuro);padding:18px 20px}}header .marca{{max-width:900px;margin:0 auto;font-family:'Archivo',sans-serif;font-weight:700;font-size:22px;color:#FF5A36}}
main{{max-width:900px;margin:0 auto;padding:36px 20px 60px}}
h1{{font-family:'Archivo',sans-serif;font-size:32px;margin:0 0 8px}}.sub{{color:var(--gris);margin:0 0 30px;font-size:17px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px}}
.g{{display:block;background:#fff;border:1px solid var(--linea);border-radius:12px;padding:20px;text-decoration:none;color:inherit}}
.g:hover{{border-color:var(--teal)}}.g h2{{font-family:'Archivo',sans-serif;font-size:17px;margin:0 0 8px;color:var(--tinta)}}.g p{{margin:0;color:var(--gris);font-size:14.5px}}
footer{{border-top:1px solid var(--linea);padding:24px 20px;text-align:center;font-size:13.5px;color:#8A94A0}}
</style>
<script type="application/ld+json">{json.dumps({"@context":"https://schema.org","@type":"CollectionPage","name":"Guías de compra de maquinaria de ocasión","publisher":{"@type":"Organization","name":"Equipzilla"},"inLanguage":"es","hasPart":[{"@type":"Article","headline":g["titulo"],"url":g["url"]} for g in guias]}, ensure_ascii=False)}</script>
</head><body><header><div class="marca">EQUIPZILLA</div></header>
<main><h1>Guías de compra de maquinaria de ocasión</h1>
<p class="sub">Precios reales de unidades en venta, qué revisar antes de comprar y cómo elegir sin equivocarte. Sin datos inventados.</p>
<div class="grid">{tarjetas}</div></main>
<footer>Equipzilla · maquinaria de ocasión revisada · <a href="mailto:clientes@equipzilla.com">clientes@equipzilla.com</a></footer>
</body></html>""")

    open(os.path.join(SITE, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "<url><loc>%s/</loc><lastmod>%s</lastmod></url>\n" % (BASE, HOY)
        + "".join("<url><loc>%s</loc><lastmod>%s</lastmod></url>\n" % (g["url"], g["fecha"]) for g in guias)
        + "</urlset>\n")
    # GEO: que ChatGPT, Claude y Gemini puedan leer y citar las guías
    open(os.path.join(SITE, "robots.txt"), "w").write(
        "User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\n"
        "User-agent: Google-Extended\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % BASE)
    json.dump({"cleanUrls": True, "trailingSlash": False,
               "headers": [{"source": "/(.*)", "headers": [
                   {"key": "Cache-Control", "value": "public, max-age=3600"}]}]},
              open(os.path.join(SITE, "vercel.json"), "w"), indent=2)
    print("site/ listo · %d guías · base %s" % (len(guias), BASE))
    for g in guias:
        print("   /%s" % g["slug"])


if __name__ == "__main__":
    main()
