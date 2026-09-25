#!/usr/bin/env python3
"""Monta una tanda de leads desde una lista de empresas de Apollo, sin gastar.

Por qué existe: el saldo de Apify se agotó el 14/09 y las 57 provincias de
Google Maps están exprimidas. La búsqueda de empresas de Apollo
(`apollo_organizations_lookup`) es **gratis** y devuelve nombre y dominio; el
correo no lo da, pero eso ya lo sacamos rastreando la web de cada empresa
(`emails_desde_webs.py`). Así la tanda sale a coste cero y no hay que esperar a
que alguien decida entre presupuesto de Apify y créditos de Apollo.

Entrada: un JSON con [{"name": ..., "domain": ...}, ...] (lo que devuelve la
búsqueda de Apollo, tal cual).

El embudo, y lo que descarta cada paso, sale por pantalla:
  candidatas → fuera de ICP (lista EXCLUIR) → sin correo en su web →
  correo que no sirve → ya en Smartlead → ya en Pipedrive → sin MX → CSV

Uso:
    python3 scripts/tanda_apollo.py leads/apollo_renovables.json tanda4_renovables
"""
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import captar_leads as cl          # noqa: E402  EXCLUIR, EMAIL_MALO, mejor_email
import emails_desde_webs as web    # noqa: E402  rastrear()
import verificar_correos as ver    # noqa: E402  defectuoso(), tiene_mx()


def en_pipedrive(dominios):
    """Dominios que ya tienen a alguien como persona en Pipedrive.

    Se cruza por DOMINIO, no por correo exacto: si ya hablamos con el jefe de
    obra de una empresa, escribirle en frío a info@ de la misma empresa es
    escribir dos veces a la misma casa.

    Dos cuidados aprendidos el 25/09, y son el mismo error que infló el
    análisis de empresas dormidas del 24/09:
      · en paralelo Pipedrive corta peticiones y el `except` se las tragaba en
        silencio: con 8 hilos salían 5 coincidencias, en serie con reintentos
        salen 47. Va en serie y con reintentos.
      · un fallo NO cuenta como «no está»; se avisa por pantalla, porque un
        dominio que no se pudo comprobar es un dominio que quizá duplicamos.
    """
    try:
        k = open(os.path.expanduser("~/.outbound/pipedrive_key")).read().strip()
    except OSError:
        print("  (sin clave de Pipedrive: no se puede cruzar)")
        return set()
    fuera, fallos = set(), []
    for dom in dominios:
        if dom in ver.LIBRES:
            continue              # gmail y compañía: el dominio no dice nada
        u = ("https://api.pipedrive.com/v1/persons/search?"
             + urllib.parse.urlencode({"term": "@" + dom, "fields": "email",
                                       "limit": 1, "api_token": k}))
        for intento in range(3):
            try:
                with urllib.request.urlopen(u, timeout=30) as r:
                    if ((json.load(r).get("data") or {}).get("items") or []):
                        fuera.add(dom)
                break
            except Exception:
                time.sleep(1.5 * (intento + 1))
        else:
            fallos.append(dom)
    if fallos:
        print(f"  ¡ojo! {len(fallos)} dominios no se pudieron comprobar "
              f"contra Pipedrive: {', '.join(fallos[:5])}")
    return fuera


def main(entrada, nombre_tanda, hilos=16):
    candidatas = json.load(open(entrada))
    if isinstance(candidatas, dict):
        candidatas = candidatas.get("organizations") or []
    vistas, limpias = set(), []
    for c in candidatas:
        dom = (c.get("domain") or "").lower().replace("www.", "")
        if not dom or dom in vistas:
            continue
        vistas.add(dom)
        if cl.EXCLUIR.search(c.get("name") or ""):
            continue
        limpias.append({"empresa": c["name"], "dominio": dom, "web": "https://" + dom})
    print(f"candidatas {len(candidatas)} → {len(limpias)} dentro de ICP")

    with ThreadPoolExecutor(max_workers=hilos) as p:
        rastreadas = [r for r in p.map(web.rastrear, limpias) if r]
    porweb = {r["domain"]: r["emails"] for r in rastreadas}
    print(f"con correo en su web: {len(porweb)}")

    ya = cl.ya_en_smartlead()
    filas = []
    for e in limpias:
        dom = e["dominio"]
        correos = porweb.get(dom)
        if not correos or dom in ya["dominios"]:
            continue
        correo = cl.mejor_email(sorted(correos), dom)
        if not correo or correo.lower() in ya["emails"]:
            continue
        motivo = ver.defectuoso(correo)
        if motivo:
            continue
        filas.append({"empresa": e["empresa"], "email": correo,
                      "telefono": "", "web": e["web"], "ciudad": "",
                      "provincia": "", "categoria": nombre_tanda,
                      "resenas": 0, "fuente": "apollo+web"})
    print(f"con correo que sirve y no está en Smartlead: {len(filas)}")

    repes = en_pipedrive(sorted({f["email"].split("@")[-1] for f in filas}))
    antes = len(filas)
    filas = [f for f in filas if f["email"].split("@")[-1] not in repes]
    print(f"ya en Pipedrive: {repes and len(repes) or 0} dominios · "
          f"{antes - len(filas)} leads descartados → quedan {len(filas)}")

    doms = sorted({f["email"].split("@")[-1] for f in filas})
    with ThreadPoolExecutor(max_workers=hilos) as p:
        list(p.map(ver.tiene_mx, doms))
    filas = [f for f in filas if ver._cache.get(f["email"].split("@")[-1], True)]
    print(f"con MX: {len(filas)}")

    os.makedirs(cl.LEADS, exist_ok=True)
    salida = os.path.join(cl.LEADS, nombre_tanda + ".csv")
    with open(salida, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()) if filas
                           else ["empresa", "email"])
        w.writeheader()
        w.writerows(filas)
    print(f"\n{len(filas)} leads → {salida}")
    return filas


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
