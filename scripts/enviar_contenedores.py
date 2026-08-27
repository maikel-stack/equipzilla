#!/usr/bin/env python3
"""Crea en Brevo las tres campañas de contenedores y módulos.

Por defecto sólo las deja en borrador. Con ENVIAR=1 las lanza.

Reglas fijas de la cuenta (docs/PLAYBOOK-ABM-CAMPANAS.md):
  - remitente id 10 (clientes@equipzilla.com), el único válido
  - replyTo explícito, o Brevo usa un buzón antiguo que nadie lee
  - añadir siempre la lista 34 para que el equipo reciba copia
"""
import json
import os
import time
import urllib.error
import urllib.request

from gen_contenedores import SEGMENTOS

CLAVE = open(os.path.expanduser("~/.outbound/brevo_key")).read().strip()
LISTA_EQUIPO = 34
REMITENTE_ID = 10
CAMPANAS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "campanas")
ENVIAR = os.environ.get("ENVIAR") == "1"


def brevo(ruta, metodo="GET", cuerpo=None):
    req = urllib.request.Request(
        "https://api.brevo.com/v3" + ruta, method=metodo,
        headers={"api-key": CLAVE, "accept": "application/json",
                 "content-type": "application/json"},
        data=json.dumps(cuerpo).encode() if cuerpo else None)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            b = r.read()
            return json.loads(b) if b else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:400]}


def main():
    for nombre, seg in SEGMENTOS.items():
        with open(os.path.join(CAMPANAS, f"contenedores-{nombre}.html")) as f:
            html = f.read()
        c = brevo("/emailCampaigns", "POST", {
            "name": f"Contenedores · {nombre.capitalize()} · 2026-08-27",
            "subject": seg["asunto"],
            "sender": {"id": REMITENTE_ID},
            "replyTo": "clientes@equipzilla.com",
            "htmlContent": html,
            "recipients": {"listIds": [seg["lista"], LISTA_EQUIPO]},
            "inlineImageActivation": False,
        })
        if "_error" in c:
            print(f"{nombre}: ERROR al crear -> {c['_error']} {c['_body'][:220]}")
            continue
        cid = c["id"]
        print(f"{nombre}: campaña #{cid} · listas {seg['lista']}+{LISTA_EQUIPO} "
              f"· «{seg['asunto']}»")
        if ENVIAR:
            r = brevo(f"/emailCampaigns/{cid}/sendNow", "POST")
            print(f"    envío -> {'OK' if '_error' not in r else r}")
            time.sleep(2)


if __name__ == "__main__":
    main()
