#!/usr/bin/env python3
"""Saca los emails de contacto rastreando las webs de los negocios de Maps.

Hace lo mismo que el Contact Scraper de Apify (`captar_leads.py emails`) pero
desde este contenedor y sin gastar saldo: el plan de Apify se agotó el 14/09
(5 de 5 $ del ciclo) y la fase de mapas ya estaba pagada, así que lo único que
faltaba era el paso barato.

Lee `leads/maps_crudo.json`, visita la home de cada web y, si no encuentra
correo, prueba las rutas de contacto habituales. Escribe `leads/emails_crudo.json`
con la MISMA forma que devuelve Apify ({domain, emails}), de modo que
`python3 scripts/captar_leads.py csv` funciona después sin tocar nada.

Uso:
    python3 scripts/emails_desde_webs.py [nº máximo de webs] [hilos]

No sube nada a ningún sitio: solo descarga páginas públicas y guarda el
resultado en `leads/`, que está en .gitignore.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import captar_leads as cl  # noqa: E402  (reutiliza EXCLUIR, EMAIL_MALO, rutas)

RUTAS = ("", "/contacto", "/contact", "/es/contacto", "/contactar",
         "/quienes-somos", "/aviso-legal", "/empresa")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
NAVEGADOR = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
# Basura que aparece en el HTML y parece un correo pero no lo es.
RUIDO = re.compile(r"\.(png|jpe?g|webp|gif|svg|css|js)$|^[0-9a-f]{16,}@|"
                   r"@(sentry|wix|2x|3x|sample|test)\b", re.I)


def bajar(url, timeout=12):
    req = urllib.request.Request(url, headers={
        "user-agent": NAVEGADOR,
        "accept": "text/html,application/xhtml+xml",
        "accept-language": "es-ES,es;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        # Muchas webs de obra son WordPress pesados: con 300 KB sobra para
        # el pie de página, que es donde vive el correo.
        return r.read(300_000).decode("utf-8", "replace")


def correos_de(html, dominio):
    fuera = set()
    for c in EMAIL.findall(html or ""):
        c = c.strip(".,;:)").lower()
        if RUIDO.search(c) or cl.EMAIL_MALO.search(c):
            continue
        if len(c) > 80:
            continue
        fuera.add(c)
    propios = {c for c in fuera if c.endswith("@" + dominio)}
    return sorted(propios or fuera)


def rastrear(negocio):
    """Devuelve {domain, emails} o None. Para en cuanto encuentra correo propio."""
    web, dom = negocio["web"], negocio["dominio"]
    if not web.startswith("http"):
        web = "https://" + web
    base = web.rstrip("/")
    hallados = set()
    for ruta in RUTAS:
        try:
            html = bajar(base + ruta)
        except Exception:
            continue
        nuevos = correos_de(html, dom)
        hallados.update(nuevos)
        if any(c.endswith("@" + dom) for c in hallados):
            break
    return {"domain": dom, "emails": sorted(hallados)} if hallados else None


def main(tope=1200, hilos=16):
    negocios = [n for n in cl.limpiar_mapas() if n["dominio"]]
    negocios.sort(key=lambda n: -n["resenas"])
    negocios = negocios[:tope]
    print(f"rastreando {len(negocios)} webs con {hilos} hilos")
    salida = []
    with ThreadPoolExecutor(max_workers=hilos) as pool:
        for i, r in enumerate(pool.map(rastrear, negocios), 1):
            if r:
                salida.append(r)
            if i % 50 == 0:
                print(f"  {i}/{len(negocios)} · {len(salida)} con correo")
    os.makedirs(cl.LEADS, exist_ok=True)
    json.dump(salida, open(cl.EMAILS, "w"), ensure_ascii=False)
    print(f"{len(salida)} webs con correo de {len(negocios)} → {cl.EMAILS}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1200,
         int(sys.argv[2]) if len(sys.argv) > 2 else 16)
