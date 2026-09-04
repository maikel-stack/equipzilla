#!/usr/bin/env python3
"""Vuelca los leads del informe en el Sheet de mando, en una sola pestaña.

Pedido por Maikel (04/09): que todo viva en el Sheet que pasó David en vez de
crear una hoja suelta cada día. Los leads se AÑADEN al final de la pestaña
«Leads · entrantes»; nunca se reescribe una fila existente, así que las
columnas LLAMADO y RESULTADO que rellena el equipo quedan intactas.

Uso:  python3 scripts/leads_al_sheet.py [ruta_csv]
"""
import csv
import datetime as dt
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import SHEET_ID, clave, sheets, token_google  # noqa: E402

PESTANA = "Leads · entrantes"
CABECERA = ["Fecha", "Score", "Nivel", "Nombre", "Empresa", "Email", "Teléfono",
            "Origen", "Qué dice", "Acción", "LLAMADO", "RESULTADO"]


def cabeceras():
    return {"Authorization": "Bearer " + token_google(
        ["https://www.googleapis.com/auth/spreadsheets"]),
        "Content-Type": "application/json"}


def existentes(cab):
    """Emails ya volcados, para no duplicar entre los dos informes del día."""
    rng = urllib.parse.quote("%s!A1:L2000" % PESTANA)
    d = sheets("%s/values/%s" % (SHEET_ID, rng), cab=cab)
    filas = d.get("values") or []
    return filas, {f[5].strip().lower() for f in filas[1:] if len(f) > 5 and f[5]}


def main(ruta):
    if not clave("google_sa.json"):
        raise SystemExit("falta la credencial google_sa.json")
    if not os.path.exists(ruta):
        raise SystemExit("no existe %s" % ruta)

    with open(ruta) as fh:
        leads = list(csv.DictReader(fh))
    if not leads:
        print("sin leads que volcar")
        return

    cab = cabeceras()
    meta = sheets("%s?fields=sheets.properties" % SHEET_ID, cab=cab)
    if "_error" in meta:
        raise SystemExit("Sheets ERROR: %s" % meta)
    if PESTANA not in [x["properties"]["title"] for x in meta.get("sheets", [])]:
        sheets("%s:batchUpdate" % SHEET_ID, "POST",
               {"requests": [{"addSheet": {"properties": {"title": PESTANA}}}]}, cab)

    filas, ya = existentes(cab)
    if not filas:
        sheets("%s/values/%s?valueInputOption=RAW"
               % (SHEET_ID, urllib.parse.quote("%s!A1" % PESTANA)), "PUT",
               {"values": [CABECERA]}, cab)
        ya = set()

    hoy = dt.date.today().strftime("%d/%m/%Y")
    nuevas, saltados = [], 0
    for l in leads:
        email = (l.get("EMAIL") or "").strip().lower()
        if not email or email in ya:
            saltados += 1
            continue
        ya.add(email)
        nuevas.append([hoy, l.get("SCORE", ""), l.get("NIVEL", ""),
                       (l.get("NOMBRE") or "").strip(), l.get("EMPRESA", ""),
                       email, l.get("TELEFONO", ""), l.get("ORIGEN", ""),
                       (l.get("RESPUESTA") or "")[:400], l.get("ACCION", ""),
                       "", ""])
    if not nuevas:
        print("nada nuevo: los %d leads ya estaban en «%s»" % (saltados, PESTANA))
        return

    r = sheets("%s/values/%s:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS"
               % (SHEET_ID, urllib.parse.quote("%s!A1" % PESTANA)), "POST",
               {"values": nuevas}, cab)
    if "_error" in r:
        raise SystemExit("Sheets ERROR: %s" % r)
    print("%d leads añadidos a «%s» (%d ya estaban)"
          % (len(nuevas), PESTANA, saltados))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "leads/respuestas_hoy.csv")
