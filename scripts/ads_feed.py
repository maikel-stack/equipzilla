#!/usr/bin/env python3
"""Cruce entre lo que Shopping anuncia y lo que la web publica de verdad.

Por qué. Un anuncio de Shopping lleva a la ficha de una máquina concreta. Si esa
máquina ya no está en la web, el clic está pagado y el comprador aterriza en un
listado donde no encuentra lo que vio en el anuncio. Medido el 23/09: cuatro de
las nueve máquinas anunciadas ya no estaban publicadas y se llevaban el 61 % del
gasto de Shopping.

Fuente de verdad del stock: la propia web (los datos que sirve la página de
listado), no data/machines.json, que es el catálogo de marketing y no coincide.

Uso: python3 scripts/ads_feed.py
"""
import json
import os
import re
import sys
import unicodedata
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ads_metricas import consulta  # noqa: E402

LISTADO = "https://equipzilla.com/compra/maquinaria/usada/maquinaria-construccion-segunda-mano"


def limpia(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def modelo(nombre):
    """Núcleo del nombre que identifica la máquina: marca y modelo, sin el tipo."""
    n = limpia(nombre)
    for palabra in ("miniexcavadora", "excavadora", "pala cargadora", "minicargadora", "dumper", "oruga"):
        n = n.replace(palabra, " ")
    return re.sub(r"\s+", " ", n).strip()


def en_la_web():
    """Productos publicados hoy en la web, leídos de los datos que sirve la página."""
    req = urllib.request.Request(LISTADO, headers={"User-Agent": "Mozilla/5.0 (equipzilla-ads-bot)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", "ignore")
    m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit("la página ya no trae __NEXT_DATA__: revisar cómo publica el stock")
    datos, prods = json.loads(m.group(1)), {}

    def recorre(o):
        if isinstance(o, dict):
            if "price" in o and any(k in o for k in ("name", "title", "model")):
                nombre = o.get("name") or o.get("title") or o.get("model")
                precio = o.get("price")
                prods[str(nombre)] = precio.get("amount") if isinstance(precio, dict) else precio
            for v in o.values():
                recorre(v)
        elif isinstance(o, list):
            for v in o:
                recorre(v)

    recorre(datos)
    return prods


def en_shopping(dias=30):
    rango = {7: "LAST_7_DAYS", 30: "LAST_30_DAYS"}.get(dias, "LAST_30_DAYS")
    out = {}
    for r in consulta(
            "SELECT segments.product_item_id, segments.product_title, metrics.impressions, "
            "metrics.clicks, metrics.cost_micros, metrics.conversions FROM shopping_performance_view "
            "WHERE segments.date DURING %s" % rango):
        s, m = r["segments"], r["metrics"]
        out[s.get("productTitle", "?")] = dict(
            id=s.get("productItemId", "?"), impresiones=int(m.get("impressions") or 0),
            clics=int(m.get("clicks") or 0), coste=int(m.get("costMicros") or 0) / 1e6,
            conv=float(m.get("conversions") or 0))
    return out


if __name__ == "__main__":
    web, shop = en_la_web(), en_shopping()
    modelos_web = {modelo(n) for n in web}
    print(f"Publicado en la web: {len(web)} productos · anunciado en Shopping (30 d): {len(shop)}\n")

    huerfanos, vivos = [], []
    for titulo, d in sorted(shop.items(), key=lambda x: -x[1]["coste"]):
        m = modelo(titulo)
        esta = any(m in w or w in m for w in modelos_web if w and m)
        (vivos if esta else huerfanos).append((titulo, d))

    print("ANUNCIADO Y SIN PUBLICAR EN LA WEB (el clic aterriza sin encontrar la máquina):")
    for t, d in huerfanos:
        print(f"  {t[:46]:<48} {d['clics']:4} clics {d['coste']:7.2f}€")
    if not huerfanos:
        print("  ninguno")
    gasto_h = sum(d["coste"] for _, d in huerfanos)
    gasto_t = sum(d["coste"] for _, d in shop.values()) if False else sum(d["coste"] for d in shop.values())
    if gasto_t:
        print(f"  → {gasto_h:.2f} € de {gasto_t:.2f} € ({gasto_h / gasto_t * 100:.0f} % del gasto de Shopping)")

    print("\nANUNCIADO Y PUBLICADO (correcto):")
    for t, d in vivos:
        print(f"  {t[:46]:<48} {d['clics']:4} clics {d['coste']:7.2f}€ conv {d['conv']:.0f}")

    print("\nPUBLICADO EN LA WEB Y SIN ANUNCIAR EN SHOPPING:")
    modelos_shop = {modelo(t) for t in shop}
    for n, p in sorted(web.items(), key=lambda x: -(x[1] or 0)):
        m = modelo(n)
        if not any(m in s or s in m for s in modelos_shop if s and m):
            print(f"  {n[:46]:<48} {p} €")
