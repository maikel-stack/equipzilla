#!/usr/bin/env python3
"""Crea el email de seguimiento de una campaña, excluyendo a quien ya actuó.

Uso:
    python3 scripts/followup_campana.py <id_campana> <html_f2> <asunto> [clickers|abridores]

Qué hace:
 1. Exporta de Brevo los clickers (o abridores) de la campaña original.
 2. Los mete en una lista de exclusión propia de esa campaña.
 3. Crea el seguimiento como BORRADOR apuntando a las mismas listas
    con la exclusión aplicada. El envío sigue necesitando OK humano.

Por defecto excluye sólo a los CLICKERS: quien clicó ya está en la cola de
llamadas del informe de las 8:00 y no debe recibir otro email; quien abrió
sin clicar sí recibe el seguimiento, que trae un ángulo distinto.
"""
import csv
import io
import json
import os
import sys
import time
import urllib.request

K = open(os.path.expanduser("~/.outbound/brevo_key")).read().strip()
NAVEGADOR = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")


def brevo(ruta, metodo="GET", cuerpo=None):
    req = urllib.request.Request("https://api.brevo.com/v3" + ruta, method=metodo,
        headers={"api-key": K, "accept": "application/json",
                 "content-type": "application/json"},
        data=json.dumps(cuerpo).encode() if cuerpo else None)
    with urllib.request.urlopen(req, timeout=90) as r:
        b = r.read()
        return json.loads(b) if b else {}


def exportar(cid, tipo):
    proc = brevo(f"/emailCampaigns/{cid}/exportRecipients", "POST",
                 {"recipientsType": tipo})
    pid = proc.get("processId")
    for _ in range(40):
        time.sleep(4)
        p = brevo(f"/processes/{pid}")
        if p.get("status") == "completed":
            req = urllib.request.Request(p["export_url"],
                                         headers={"user-agent": NAVEGADOR})
            with urllib.request.urlopen(req, timeout=90) as r:
                texto = r.read().decode("utf-8", "replace")
            return [fila.get("EMAIL") or fila.get("email") or ""
                    for fila in csv.DictReader(io.StringIO(texto), delimiter=";")]
    return []


def main():
    cid = int(sys.argv[1])
    html = open(sys.argv[2]).read()
    asunto = sys.argv[3]
    tipo = {"clickers": "clickers", "abridores": "openers"}.get(
        sys.argv[4] if len(sys.argv) > 4 else "clickers", "clickers")

    original = brevo(f"/emailCampaigns/{cid}")
    listas = (original.get("recipients") or {}).get("lists") or []
    print(f"campaña original #{cid} «{original.get('name')}» · listas {listas}")

    excluidos = [e for e in exportar(cid, tipo) if e]
    print(f"{tipo} a excluir: {len(excluidos)}")

    lista_exc = brevo("/contacts/lists", "POST", {
        "name": f"Exclusión · f2 de campaña {cid}", "folderId": 16})["id"]
    for i in range(0, len(excluidos), 100):
        brevo("/contacts/import", "POST", {
            "listIds": [lista_exc], "updateExistingContacts": True,
            "emptyContactsAttributes": False,
            "jsonBody": [{"email": e} for e in excluidos[i:i + 100]]})
        time.sleep(0.6)

    f2 = brevo("/emailCampaigns", "POST", {
        "name": f"{original.get('name', '')[:40]} · seguimiento",
        "subject": asunto, "sender": {"id": 10},
        "replyTo": "clientes@equipzilla.com", "htmlContent": html,
        "recipients": {"listIds": listas, "exclusionListIds": [lista_exc]}})
    print(f"seguimiento creado en BORRADOR: campaña #{f2.get('id')} "
          f"(exclusión: lista {lista_exc}). Enviar requiere OK.")


if __name__ == "__main__":
    main()
