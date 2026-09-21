#!/usr/bin/env python3
"""Higiene semanal de las listas de envío de Brevo (lunes).

Saca de las listas de envío a los contactos que Brevo ya tiene en lista negra
(rebotes duros y bajas: no reciben nada, pero inflan las listas) y, si se pide,
a los que han rebotado blando en dos o más campañas. No borra contactos ni toca
la lista negra: solo quita pertenencias a lista, reversible con /contacts/lists/{id}/contacts/add.

Uso:
  python3 scripts/brevo_higiene.py                  # solo cuenta, no toca nada
  python3 scripts/brevo_higiene.py --hacer          # quita de las listas a los de lista negra
  python3 scripts/brevo_higiene.py --hacer --blandos leads/higiene_2026-09-11.json
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.brevo.com/v3"
LISTAS_ENVIO = [38, 30, 39, 40, 41, 43]


def clave():
    v = os.environ.get("BREVO_API_KEY") or os.environ.get("BREVO_KEY")
    if v:
        return v.strip()
    ruta = os.path.expanduser("~/.outbound/brevo_key")
    if not os.path.exists(ruta):
        sys.exit("Falta brevo_key")
    return open(ruta).read().strip()


def brevo(ruta, metodo="GET", cuerpo=None):
    req = urllib.request.Request(API + ruta, data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
                                 headers={"api-key": clave(), "accept": "application/json",
                                          "content-type": "application/json"}, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:200]}


def contactos(lista):
    out, off = [], 0
    while True:
        d = brevo("/contacts/lists/%d/contacts?limit=500&offset=%d" % (lista, off))
        cs = d.get("contacts", [])
        out += cs
        if len(cs) < 500:
            return out
        off += 500
        time.sleep(0.3)


def quitar(lista, emails):
    n = 0
    for i in range(0, len(emails), 150):
        r = brevo("/contacts/lists/%d/contacts/remove" % lista, "POST", {"emails": emails[i:i + 150]})
        if "_error" in r:
            print("  ERROR lista %d: %s" % (lista, r))
            break
        n += len(r.get("contacts", {}).get("success", []))
        time.sleep(0.3)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hacer", action="store_true", help="ejecuta las bajas de lista (sin esto solo cuenta)")
    ap.add_argument("--blandos", default="", help="json con clave soft_rep (leads/higiene_*.json) para sacar también a los blandos repetidos")
    a = ap.parse_args()
    blandos = set()
    if a.blandos:
        blandos = {e for e, _, _ in json.load(open(a.blandos)).get("soft_rep", [])}
    registro = {"fecha": datetime.datetime.now().isoformat(timespec="minutes"), "listas": {}}
    for L in LISTAS_ENVIO:
        cs = contactos(L)
        negros = [c["email"] for c in cs if c.get("emailBlacklisted")]
        sb = [c["email"] for c in cs if c["email"].lower() in blandos and not c.get("emailBlacklisted")]
        quitados = 0
        if a.hacer:
            quitados = quitar(L, negros + sb)
        print("lista %d: %d contactos · %d en lista negra · %d blandos repetidos · quitados %d"
              % (L, len(cs), len(negros), len(sb), quitados))
        registro["listas"][L] = {"total": len(cs), "lista_negra": negros, "blandos": sb, "quitados": quitados}
    os.makedirs("leads", exist_ok=True)
    ruta = "leads/higiene_ejecutada_%s.json" % datetime.date.today().isoformat()
    json.dump(registro, open(ruta, "w"), indent=1)
    print("registro (fuera del repo):", ruta, "· modo:", "EJECUTADO" if a.hacer else "solo recuento")


if __name__ == "__main__":
    main()
