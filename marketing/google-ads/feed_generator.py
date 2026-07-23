# -*- coding: utf-8 -*-
"""Genera el feed de Google Merchant Center a partir del catalogo de equipzilla.com.

Lee los datos embebidos (__NEXT_DATA__) de las paginas de categoria de "ocasion/usada",
recorre subcategorias y productos, y produce un TSV listo para subir a Merchant Center.

Uso:
  python feed_generator.py                # genera equipzilla_feed_shopping.tsv
  python feed_generator.py --url <cat>    # anade categorias de origen

Maquinaria usada = sin GTIN -> identifier_exists=no, con brand + mpn (reference).
"""
import re
import sys
import json
import csv
import urllib.request

BASE = "https://equipzilla.com"

# Categorias raiz de compra (ocasion + usada). Anade mas con --url.
DEFAULT_CATEGORIES = [
    "https://equipzilla.com/compra/maquinaria/ocasion/maquinaria-construccion-segunda-mano",
    "https://equipzilla.com/compra/maquinaria/usada",
    "https://equipzilla.com/compra/maquinaria/ocasion",
]

BRANDS = ["Doosan", "Develon", "Kubota", "Bobcat", "Caterpillar", "Cat", "Komatsu",
          "Hitachi", "JCB", "Volvo", "Case", "Hyundai", "Takeuchi", "Wacker", "Ausa",
          "Yanmar", "Liebherr", "Manitou", "Merlo", "Hamm", "Bomag"]

CONDITION_MAP = {"segunda_mano": "used", "usada": "used", "usado": "used",
                 "ocasion": "used", "nuevo": "new", "nueva": "new"}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def next_data(html):
    m = re.search(r'id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else None


def collect_products(node, acc):
    if not isinstance(node, dict):
        return
    for p in node.get("product", []) or []:
        acc[p["id"]] = p          # dedupe por id
    for s in node.get("subcategories", []) or []:
        collect_products(s, acc)


def brand_of(title, spec):
    hay = f"{title} {spec.get('Modelo','')}"
    for b in BRANDS:
        if re.search(rf"\b{re.escape(b)}\b", hay, re.I):
            return "Develon" if b.lower() == "doosan" and "develon" in hay.lower() else b
    return ""


def build_description(title, spec):
    parts = []
    order = ["Modelo", "Año", "Horas certificadas", "Peso operativo", "Cabina",
             "Enganche rápido", "Cazos incluidos"]
    for k in order:
        if spec.get(k) not in (None, "", 0):
            parts.append(f"{k}: {spec[k]}")
    base = title.strip()
    if parts:
        base += ". " + ". ".join(str(p) for p in parts)
    base += ". Maquinaria de segunda mano revisada y operativa. Envío a toda España."
    return base[:4900]


def product_url(p):
    slug = p.get("slugComplete", "").strip("/")
    ref = p.get("reference") or p.get("id")
    return f"{BASE}/compra/{slug}/{ref}"


def to_row(p):
    spec = p.get("spec") or {}
    title = (p.get("title") or "").strip()
    cond = CONDITION_MAP.get(str(p.get("condition", "")).lower().strip(), "used")
    ref = str(p.get("reference") or p.get("id"))
    brand = brand_of(title, spec)
    year = spec.get("Año")
    disp_title = title if not year else f"{title} ({year})"
    return {
        "id": ref,
        "title": disp_title[:150],
        "description": build_description(title, spec),
        "link": product_url(p),
        "image_link": p.get("image", ""),
        "availability": "in_stock",
        "price": f"{int(p['price'])} EUR",
        "condition": cond,
        "brand": brand or "Equipzilla",
        "mpn": ref,
        "identifier_exists": "no",
        "google_product_category": "Business & Industrial > Heavy Machinery",
        "product_type": p.get("slugComplete", "").replace("/", " > "),
    }


COLUMNS = ["id", "title", "description", "link", "image_link", "availability",
           "price", "condition", "brand", "mpn", "identifier_exists",
           "google_product_category", "product_type"]


def main():
    cats = list(DEFAULT_CATEGORIES)
    if "--url" in sys.argv:
        cats += sys.argv[sys.argv.index("--url") + 1:]

    products = {}
    for url in cats:
        try:
            data = next_data(fetch(url))
        except Exception as e:
            print(f"[!] No se pudo leer {url}: {e}")
            continue
        if not data:
            continue
        pp = data.get("props", {}).get("pageProps", {})
        icd = pp.get("initialCategoryData")
        if icd:
            collect_products(icd, products)
        # por si es una pagina de producto suelto
        if pp.get("initialProduct"):
            ip = pp["initialProduct"]
            if isinstance(ip, dict) and ip.get("id"):
                products[ip["id"]] = ip

    rows = [to_row(p) for p in products.values() if p.get("price")]
    out = "equipzilla_feed_shopping.tsv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"[OK] {len(rows)} productos escritos en {out}")
    for r in rows[:3]:
        print("   -", r["id"], "|", r["title"], "|", r["price"], "|", r["brand"])


if __name__ == "__main__":
    main()
