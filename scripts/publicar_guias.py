#!/usr/bin/env python3
"""Integra las guías de seo/articulos/ en el proyecto Vercel que YA está vivo.

Maikel (08/09): el WordPress sigue comprometido, así que las guías se
publican "de mientras" en Vercel. No en un proyecto nuevo: quiz/ ya es un
proyecto desplegado (equipzilla-quiz.vercel.app) con 12 guías, índice y la
misma marca. Este script mete las nuevas ahí dentro:

  - copia cada artículo a quiz/guias/<slug>.html con canonical al dominio
  - añade su tarjeta al índice quiz/guias/index.html (bloque marcado)
  - actualiza quiz/sitemap.xml
  - crea quiz/robots.txt dejando pasar a los bots de IA (GEO)

Vuelve a ejecutarse cada vez que haya artículos nuevos; es idempotente.
Cuando esté el CNAME, cambiar BASE a https://ocasion.equipzilla.com.

Uso:  python3 scripts/publicar_guias.py
      npx vercel deploy quiz --prod --token $VERCEL_TOKEN
"""
import datetime as dt
import html
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(RAIZ, "seo", "articulos")
QUIZ = os.path.join(RAIZ, "quiz")
GUIAS = os.path.join(QUIZ, "guias")
BASE = os.environ.get("BASE", "https://ocasion.equipzilla.com").rstrip("/")
HOY = dt.date.today().isoformat()
INICIO, FIN = "<!-- guias-seo:inicio -->", "<!-- guias-seo:fin -->"

# etiqueta de la tarjeta por slug (lo que el índice muestra en pequeño)
ETIQUETA = {"mini-excavadora": "miniexcavadora", "excavadora": "excavadora",
            "caseta": "casetas de obra", "contenedor": "contenedores",
            "generador": "generadores", "plataforma": "plataforma elevadora",
            "dumper": "dumper"}


def meta(t):
    tit = re.search(r"<title>(.*?)</title>", t, re.S)
    des = re.search(r'<meta name="description" content="([^"]*)"', t)
    fec = re.search(r'"datePublished":"([\d-]+)"', t)
    return (html.unescape(tit.group(1)).split(" · Equipzilla")[0].strip() if tit else "",
            html.unescape(des.group(1)) if des else "", fec.group(1) if fec else HOY)


def main():
    guias = []
    for f in sorted(os.listdir(ORIGEN)):
        if not f.endswith(".html"):
            continue
        t = open(os.path.join(ORIGEN, f), encoding="utf-8").read()
        url = "%s/guias/%s" % (BASE, f)
        t = re.sub(r'<link rel="canonical"[^>]*>\n?', "", t)
        t = t.replace("</title>", '</title>\n<link rel="canonical" href="%s">' % url, 1)
        open(os.path.join(GUIAS, f), "w", encoding="utf-8").write(t)
        titulo, desc, fecha = meta(t)
        etiqueta = next((v for k, v in ETIQUETA.items() if k in f), "guía")
        guias.append(dict(f=f, url=url, titulo=titulo, desc=desc, fecha=fecha, et=etiqueta))

    # índice: bloque propio entre marcas, para poder regenerarlo sin tocar el resto
    ruta_idx = os.path.join(GUIAS, "index.html")
    idx = open(ruta_idx, encoding="utf-8").read()
    tarjetas = "".join(
        '<a class="card" href="/guias/%s"><div class="ce mono">%s</div><b class="arx">%s</b>'
        '<span>%s…</span></a>' % (g["f"], g["et"], html.escape(g["titulo"]),
                                   html.escape(g["desc"][:110].rstrip()))
        for g in guias)
    bloque = "%s\n  %s\n  %s" % (INICIO, tarjetas, FIN)
    if INICIO in idx:
        idx = re.sub(re.escape(INICIO) + ".*?" + re.escape(FIN), bloque, idx, flags=re.S)
    else:
        # justo después del bloque de guías de precio (la última tarjeta de precios)
        pos = idx.rfind("</a>", 0, idx.find("precio-excavadora-usada.html") + 400)
        pos = idx.find("</a>", idx.find("precio-excavadora-usada.html")) + 4
        idx = idx[:pos] + "\n  " + bloque + idx[pos:]
    open(ruta_idx, "w", encoding="utf-8").write(idx)

    # sitemap: añadir las nuevas sin duplicar
    ruta_sm = os.path.join(QUIZ, "sitemap.xml")
    sm = open(ruta_sm, encoding="utf-8").read()
    nuevas = "".join("  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n" % (g["url"], g["fecha"])
                     for g in guias if g["url"] not in sm)
    sm = sm.replace("</urlset>", nuevas + "</urlset>")
    # dedupe por <loc> (conserva la primera aparición)
    vistos, limpio = set(), []
    for bloque_url in re.findall(r"\s*<url>.*?</url>", sm, flags=re.S):
        loc = re.search(r"<loc>(.*?)</loc>", bloque_url).group(1)
        if loc not in vistos:
            vistos.add(loc); limpio.append(bloque_url.strip())
    cab = sm[:sm.find("<url>")]
    sm = cab + "\n  ".join(limpio) + "\n</urlset>\n"
    open(ruta_sm, "w", encoding="utf-8").write(sm)

    # GEO: que ChatGPT, Claude, Gemini y Perplexity puedan leer y citar
    open(os.path.join(QUIZ, "robots.txt"), "w").write(
        "User-agent: *\nAllow: /\nDisallow: /crm/\nDisallow: /api/\nDisallow: /dashboard.html\nDisallow: /equipo-sistema.html\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\n"
        "User-agent: Google-Extended\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\n"
        "Sitemap: %s/sitemap.xml\n" % BASE)
    print("%d guías integradas en quiz/guias · base %s" % (len(guias), BASE))
    for g in guias:
        print("   /guias/%s" % g["f"])


if __name__ == "__main__":
    main()
