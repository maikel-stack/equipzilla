#!/usr/bin/env python3
"""Pestaña «Demanda sin stock» del Sheet de mando, para David y compras.

Pedida por el Director el 16/09. Cruza los tratos de compraventa abiertos de
Pipedrive con la hoja de stock de David y marca qué pide cada cliente que hoy
no podemos servir, con su presupuesto y su trato.

Es una vista derivada: se borra y se regenera. Las fuentes siguen siendo
Pipedrive (lo que pide el cliente) y la hoja de David (lo que tenemos). Este
script no escribe en ninguna de las dos.

Uso:  python3 scripts/demanda_sin_stock.py
"""
import datetime as dt
import os
import re
import sys
import urllib.parse
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import SHEET_ID, pipedrive, sheets, token_google  # noqa: E402
import aviso_stock_leads as asl  # noqa: E402
import cola_comercial as cc  # noqa: E402

PESTANA = "Demanda sin stock"
TINTA = {"red": 0.09, "green": 0.20, "blue": 0.23}
ALERTA = {"red": 0.70, "green": 0.23, "blue": 0.16}
SUAVE = {"red": 0.93, "green": 0.95, "blue": 0.96}
CREMA = {"red": 0.99, "green": 0.96, "blue": 0.89}
BLANCO = {"red": 1, "green": 1, "blue": 1}

# margen de precio que aceptamos al buscar encaje: el cliente que pide 9.000 €
# mira una máquina de 10.000 €, no una de 23.500 €.
MARGEN = 1.25


def limpia(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    t = (t.replace("&nbsp;", " ").replace("&amp;", "&")
          .replace("&quot;", '"').replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">"))
    return re.sub(r"\s+", " ", t).strip()


# Texto que escribimos nosotros, no el cliente: plantillas del formulario y
# respuestas del equipo. Si se cuela aquí, la tabla enseña nuestras palabras
# como si fueran la petición del cliente (mismo error que el email de Tirri).
NUESTRO = re.compile(
    r"rellenar este formulario|hemos estado revisando|buenas tardes|buenos d[ií]as|"
    r"te (env|adjunt)|le (env|adjunt)|adjunto|oferta enviada|\[CRM|https?://|"
    r"^\*\*|delegaciones|trabajan con equipzilla|protocolo|procedimiento interno", re.I)


def que_pide(x):
    """Lo que pide el cliente, con su origen. assetUse primero; si está vacío,
    la primera nota que NO sea texto nuestro. Nunca se inventa: si no hay nada,
    se dice que solo tenemos el título."""
    uso = limpia(x.get(cc.campo("assetUse").get("key")) or "")
    if uso:
        return uso[:150], "campo assetUse"
    n = pipedrive("/notes", deal_id=x["id"], limit=5, sort="add_time ASC").get("data") or []
    for z in n:
        t = limpia(z.get("content"))
        if len(t) > 25 and not NUESTRO.search(t):
            return t[:150], "nota del %s" % str(z.get("add_time"))[:10]
    titulo = re.sub(r"^[0-9a-f-]{36} ?-\s*", "", x.get("title") or "")
    return titulo[:150], "SOLO EL TÍTULO · falta cualificar"


def encaje(cat, presupuesto, inv):
    """Máquinas de la hoja de David en esa categoría dentro de presupuesto."""
    etiqueta = cc.ETIQUETA.get(cat, "")
    misma = [f for f in inv if f["categoria"] == etiqueta] if etiqueta else []
    if not misma:
        return [], misma
    if not presupuesto:
        return sorted(misma, key=lambda f: f["precio"] or 0)[:3], misma
    dentro = [f for f in misma if f["precio"] and f["precio"] <= presupuesto * MARGEN]
    return sorted(dentro, key=lambda f: f["precio"] or 0)[:3], misma


def main():
    hoy = dt.datetime.now(ZoneInfo("Europe/Madrid"))
    tk = token_google(["https://www.googleapis.com/auth/spreadsheets"])
    inv = asl.stock(tk)
    abiertos = cc.deals("open")

    filas_sin, filas_ok = [], []
    for x in sorted(abiertos, key=lambda z: -(z.get("value") or 0)):
        titulo = re.sub(r"^[0-9a-f-]{36} ?-\s*", "", x.get("title") or "")
        if titulo.startswith("Prospecto"):
            continue                      # el frío aún no ha dicho qué quiere
        persona = (x.get("person_id") or {}).get("name") or "—"
        pide, origen = que_pide(x)
        atype = cc.opcion("assetType", x.get(cc.campo("assetType").get("key")))
        cat = cc.categoria(" ".join((atype, titulo))) or cc.categoria(pide)
        presupuesto = float(x.get("value") or 0)
        ops, misma_cat = encaje(cat, presupuesto, inv)
        etiqueta_cat = cc.ETIQUETA.get(cat, "sin clasificar")
        if ops:
            estado, detalle = "CUBIERTA", " · ".join("%s %s (%s €)" % (f["titulo"], f["anio"], cc.eur(f["precio"] or 0)) for f in ops)
        elif misma_cat:
            barata = min((f["precio"] or 0) for f in misma_cat if f["precio"])
            estado = "FUERA DE PRECIO"
            detalle = "%d en esa categoría, la más barata %s €" % (len(misma_cat), cc.eur(barata))
        else:
            estado, detalle = "SIN STOCK", "nada en esa categoría en la hoja"
        fila = [x["id"], persona, pide, etiqueta_cat,
                presupuesto if presupuesto else "sin importe",
                estado, detalle, origen,
                (x.get("user_id") or {}).get("name") or "—",
                str(x.get("add_time"))[:10]]
        (filas_ok if estado == "CUBIERTA" else filas_sin).append(fila)

    cab = ["Trato", "Cliente", "Qué pide", "Categoría", "Presupuesto",
           "Estado", "Qué tenemos", "De dónde sale «qué pide»", "Propietario", "Alta"]
    F = [["DEMANDA SIN STOCK · compraventa abierta", "", "", "", "", "", "",
          "Pipedrive + hoja de stock de David · %s" % hoy.strftime("%d/%m %H:%M")],
         ["Para David y compras. Vista derivada: se regenera con "
          "scripts/demanda_sin_stock.py. No es fuente de verdad de nada."],
         [],
         ["LO QUE NO PODEMOS SERVIR HOY (%d)" % len(filas_sin)],
         cab] + filas_sin + [[], ["YA CUBIERTA CON STOCK ACTUAL (%d)" % len(filas_ok)], cab] + filas_ok + [
         [], ["CÓMO LEERLA"],
         ["SIN STOCK = no hay ninguna máquina de esa categoría en la hoja. "
          "FUERA DE PRECIO = sí la hay, pero por encima del presupuesto del cliente (margen del %d %%)." % int((MARGEN - 1) * 100)],
         ["«Presupuesto» es el importe del trato en Pipedrive. «sin importe» significa que nadie lo ha cargado: "
          "sin ese dato no se puede decir si lo que tenemos le encaja."],
         ["Los tratos de frío («Prospecto») no salen aquí: todavía no han dicho qué máquina quieren."]]

    cabecera = {"Authorization": "Bearer " + tk, "Content-Type": "application/json"}
    meta = sheets("%s?fields=sheets.properties" % SHEET_ID, cab=cabecera)
    hojas = {h["properties"]["title"]: h["properties"] for h in meta.get("sheets", [])}
    if PESTANA not in hojas:
        sheets("%s:batchUpdate" % SHEET_ID, "POST",
               {"requests": [{"addSheet": {"properties": {"title": PESTANA, "index": 2}}}]}, cabecera)
        meta = sheets("%s?fields=sheets.properties" % SHEET_ID, cab=cabecera)
        hojas = {h["properties"]["title"]: h["properties"] for h in meta.get("sheets", [])}
    sid = hojas[PESTANA]["sheetId"]
    sheets("%s/values/%s:clear" % (SHEET_ID, urllib.parse.quote("%s!A1:J200" % PESTANA)), "POST", {}, cabecera)
    r = sheets("%s/values/%s?valueInputOption=USER_ENTERED" % (SHEET_ID, urllib.parse.quote("%s!A1" % PESTANA)),
               "PUT", {"values": F}, cabecera)
    if "_error" in r:
        raise SystemExit(r)

    rg = lambda a, b=None, c0=0, c1=10: {"sheetId": sid, "startRowIndex": a, "endRowIndex": b or a + 1,
                                         "startColumnIndex": c0, "endColumnIndex": c1}
    fila_cab1 = 4                      # 0-based: la cabecera del primer bloque
    fila_cab2 = 4 + len(filas_sin) + 3
    reqs = [
        {"repeatCell": {"range": rg(0, 200), "cell": {"userEnteredFormat": {
            "backgroundColor": BLANCO, "textFormat": {"bold": False, "fontSize": 10},
            "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat"}},
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 5}},
                                   "fields": "gridProperties.frozenRowCount"}},
        {"repeatCell": {"range": rg(0, 1), "cell": {"userEnteredFormat": {
            "backgroundColor": TINTA, "textFormat": {"bold": True, "fontSize": 13, "foregroundColor": BLANCO}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"repeatCell": {"range": rg(3, 4), "cell": {"userEnteredFormat": {
            "backgroundColor": CREMA, "textFormat": {"bold": True, "foregroundColor": ALERTA}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"repeatCell": {"range": rg(fila_cab1, fila_cab1 + 1), "cell": {"userEnteredFormat": {
            "backgroundColor": SUAVE, "textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"repeatCell": {"range": rg(fila_cab2 - 1, fila_cab2), "cell": {"userEnteredFormat": {
            "backgroundColor": CREMA, "textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"repeatCell": {"range": rg(fila_cab2, fila_cab2 + 1), "cell": {"userEnteredFormat": {
            "backgroundColor": SUAVE, "textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"repeatCell": {"range": rg(fila_cab1 + 1, fila_cab1 + 1 + len(filas_sin), 4, 5),
                        "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0 €"}}},
                        "fields": "userEnteredFormat.numberFormat"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3},
                                       "properties": {"pixelSize": 320}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 6, "endIndex": 7},
                                       "properties": {"pixelSize": 300}, "fields": "pixelSize"}},
    ]
    sheets("%s:batchUpdate" % SHEET_ID, "POST", {"requests": reqs}, cabecera)

    print("«%s» escrita · %d sin servir · %d cubiertas · stock leído: %d máquinas"
          % (PESTANA, len(filas_sin), len(filas_ok), len(inv)))
    for f in filas_sin:
        print("  %-6s %-22s %-13s %-16s %s" % (f[0], f[1][:22], f[5], f[3][:16], str(f[2])[:60]))


if __name__ == "__main__":
    main()
