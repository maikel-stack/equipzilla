#!/usr/bin/env python3
"""Capta leads de frío del ICP de compra en toda España.

Dos fases, tal como está documentado en docs/PLAYBOOK-OUTBOUND-COMPRAVENTA.md:

  1. Google Maps (Apify) — negocios que USAN máquina pesada, por término y
     provincia. Da nombre, teléfono, web y ciudad.
  2. Contact Scraper (Apify) — rastrea cada web y saca los emails.

Filtra por el ICP de la sección 3 del playbook: fuera ingenierías,
consultoras, arquitectura, inmobiliarias y reformas de interior, que no
compran excavadoras.

Salida: leads/frio_espana.csv (la carpeta leads/ está en .gitignore; no se
sube información personal al repositorio).

Uso:
    python3 scripts/captar_leads.py mapas      # fase 1
    python3 scripts/captar_leads.py emails     # fase 2
    python3 scripts/captar_leads.py csv        # consolidar
"""
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

CLAVE = open(os.path.expanduser("~/.outbound/apify_key")).read().strip()
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS = os.path.join(RAIZ, "leads")
CRUDO = os.path.join(LEADS, "maps_crudo.json")
EMAILS = os.path.join(LEADS, "emails_crudo.json")
SALIDA = os.path.join(LEADS, "frio_espana.csv")

TERMINOS = ["movimiento de tierras", "excavaciones", "demoliciones",
            "constructora obra civil"]

PROVINCIAS = [
    "Madrid", "Barcelona", "Valencia", "Sevilla", "Zaragoza", "Málaga",
    "Murcia", "Palma de Mallorca", "Bilbao", "Alicante", "Córdoba",
    "Valladolid", "Vigo", "Gijón", "Granada", "A Coruña", "Vitoria",
    "Pamplona", "Santander", "Toledo", "Badajoz", "Albacete", "Logroño",
    "Castellón", "Tarragona", "Lleida", "Girona", "Almería", "Jaén",
    "Salamanca",
]

# Fuera del ICP: no compran máquina pesada por mucho que la palabra
# "construcción" aparezca en su ficha.
EXCLUIR = re.compile(
    r"arquitect|ingenier[ií]a|consultor|inmobiliari|promotor|reforma|"
    r"interiorismo|decoraci|abogad|asesor[ií]a|gestor[ií]a|seguros|"
    r"inmueble|tasaci|topograf|proyect[oa]s de ingenier", re.I)

# Correos que no son de la empresa o no sirven para vender.
EMAIL_MALO = re.compile(
    r"@(example|sentry|wixpress|godaddy|domain|squarespace|gmail\.com\.|"
    r"cloudflare|jimdo|wordpress)|noreply|no-reply|privacy|rgpd|dpo@|"
    r"\.png$|\.jpg$|\.webp$|\.gif$", re.I)


def apify(ruta, metodo="GET", cuerpo=None, espera=60):
    url = f"https://api.apify.com/v2/{ruta}"
    url += ("&" if "?" in url else "?") + "token=" + CLAVE
    req = urllib.request.Request(
        url, method=metodo,
        headers={"content-type": "application/json"},
        data=json.dumps(cuerpo).encode() if cuerpo else None)
    with urllib.request.urlopen(req, timeout=espera) as r:
        return json.load(r)


def esperar(run_id, etiqueta, minutos=25):
    """Sondea el run hasta que termina. Devuelve el id del dataset."""
    limite = time.time() + minutos * 60
    while time.time() < limite:
        d = apify(f"actor-runs/{run_id}")["data"]
        estado = d["status"]
        if estado in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            print(f"  {etiqueta}: {estado} · "
                  f"{d.get('stats', {}).get('computeUnits', 0):.3f} CU")
            return d["defaultDatasetId"] if estado == "SUCCEEDED" else None
        time.sleep(20)
    print(f"  {etiqueta}: sigue corriendo pasados {minutos} min")
    return None


def descargar(dataset_id):
    salida, offset = [], 0
    while True:
        lote = apify(f"datasets/{dataset_id}/items?clean=true"
                     f"&offset={offset}&limit=1000", espera=120)
        if not lote:
            break
        salida.extend(lote)
        offset += len(lote)
        if len(lote) < 1000:
            break
    return salida


def fase_mapas(por_busqueda=20):
    os.makedirs(LEADS, exist_ok=True)
    busquedas = [f"{t} {p}" for p in PROVINCIAS for t in TERMINOS]
    print(f"Google Maps: {len(busquedas)} búsquedas × {por_busqueda} sitios "
          f"= hasta {len(busquedas) * por_busqueda} negocios")
    r = apify("acts/compass~crawler-google-places/runs", "POST", {
        "searchStringsArray": busquedas,
        "maxCrawledPlacesPerSearch": por_busqueda,
        "language": "es",
        "countryCode": "es",
        "skipClosedPlaces": True,
        "scrapePlaceDetailPage": False,
    })
    run_id = r["data"]["id"]
    print("  run:", run_id)
    ds = esperar(run_id, "mapas", minutos=40)
    if not ds:
        return
    datos = descargar(ds)
    json.dump(datos, open(CRUDO, "w"), ensure_ascii=False)
    print(f"  guardados {len(datos)} negocios en {CRUDO}")


def limpiar_mapas():
    datos = json.load(open(CRUDO))
    vistos, salida = set(), []
    for d in datos:
        nombre = (d.get("title") or "").strip()
        cat = (d.get("categoryName") or "")
        web = (d.get("website") or "").strip()
        if not nombre or EXCLUIR.search(nombre + " " + cat):
            continue
        dominio = ""
        if web:
            dominio = re.sub(r"^https?://(www\.)?", "", web).split("/")[0].lower()
        clave = dominio or nombre.lower()
        if clave in vistos:
            continue
        vistos.add(clave)
        salida.append(dict(
            empresa=nombre, categoria=cat, web=web, dominio=dominio,
            telefono=(d.get("phoneUnformatted") or "").strip(),
            ciudad=(d.get("city") or "").strip(),
            provincia=(d.get("state") or "").strip(),
            resenas=d.get("reviewsCount") or 0))
    return salida


def fase_emails(tope=1200):
    negocios = [n for n in limpiar_mapas() if n["dominio"]]
    negocios.sort(key=lambda n: -n["resenas"])
    negocios = negocios[:tope]
    print(f"Contact Scraper: {len(negocios)} webs")
    r = apify("acts/vdrmota~contact-info-scraper/runs", "POST", {
        "startUrls": [{"url": n["web"]} for n in negocios],
        "maxDepth": 1,
        "maxRequestsPerStartUrl": 3,
        "sameDomain": True,
    })
    run_id = r["data"]["id"]
    print("  run:", run_id)
    ds = esperar(run_id, "emails", minutos=40)
    if not ds:
        return
    datos = descargar(ds)
    json.dump(datos, open(EMAILS, "w"), ensure_ascii=False)
    print(f"  guardados {len(datos)} registros en {EMAILS}")


def mejor_email(correos, dominio):
    """Prefiere una dirección del propio dominio y de perfil comercial."""
    propios = [c for c in correos
               if c.lower().endswith("@" + dominio) and not EMAIL_MALO.search(c)]
    otros = [c for c in correos if not EMAIL_MALO.search(c)]
    orden = ("comercial", "ventas", "info", "contacto", "administracion",
             "oficina", "gerencia", "direccion")
    for pref in orden:
        for c in propios:
            if c.lower().startswith(pref):
                return c
    return (propios or otros or [""])[0]


def fase_csv():
    negocios = {n["dominio"]: n for n in limpiar_mapas() if n["dominio"]}
    porweb = {}
    for reg in json.load(open(EMAILS)):
        url = reg.get("url") or ""
        dom = re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()
        porweb.setdefault(dom, set()).update(reg.get("emails") or [])

    filas, vistos = [], set()
    for dom, correos in porweb.items():
        n = negocios.get(dom)
        if not n:
            continue
        email = mejor_email(sorted(correos), dom)
        if not email or email.lower() in vistos:
            continue
        vistos.add(email.lower())
        filas.append(dict(
            empresa=n["empresa"], email=email, telefono=n["telefono"],
            web=n["web"], ciudad=n["ciudad"], provincia=n["provincia"],
            categoria=n["categoria"], resenas=n["resenas"], fuente="google_maps"))

    filas.sort(key=lambda f: -f["resenas"])
    os.makedirs(LEADS, exist_ok=True)
    with open(SALIDA, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()) if filas else
                           ["empresa", "email"])
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} leads con email en {SALIDA}")
    prov = {}
    for f in filas:
        prov[f["provincia"] or "?"] = prov.get(f["provincia"] or "?", 0) + 1
    for p, n in sorted(prov.items(), key=lambda x: -x[1])[:12]:
        print(f"   {n:>4}  {p}")


if __name__ == "__main__":
    orden = sys.argv[1] if len(sys.argv) > 1 else "csv"
    {"mapas": fase_mapas, "emails": fase_emails, "csv": fase_csv}[orden]()
