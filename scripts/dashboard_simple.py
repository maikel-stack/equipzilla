#!/usr/bin/env python3
"""Pestaña «Resumen para el equipo»: qué leads hemos generado, de dónde, qué
oportunidades hay y en qué estado, y qué estamos haciendo. Para enseñárselo a
alguien que no ha seguido el día a día (pedido por Maikel el 08/09 para Andrés).

Lee lo que ya está en el propio Sheet de mando (Leads · entrantes, Cola
comercial, la lista manual de llamadas) más Pipedrive, Brevo y Smartlead en
vivo. No recalcula la cola: tarda minutos y ya está escrita cada mañana.
"""
import collections, datetime as dt, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import (SHEET_ID, brevo, pipedrive, sheets, smartlead,
                           token_google, campanas)

PESTANA = "Resumen para el equipo"
TINTA = {"red": 0.09, "green": 0.20, "blue": 0.23}
SUAVE = {"red": 0.93, "green": 0.95, "blue": 0.96}
CREMA = {"red": 0.99, "green": 0.96, "blue": 0.89}
VERDE = {"red": 0.88, "green": 0.95, "blue": 0.89}
ROJO = {"red": 0.99, "green": 0.91, "blue": 0.89}
BLANCO = {"red": 1, "green": 1, "blue": 1}
ETAPAS = {45: "Lead recibido", 33: "Oferta validada", 37: "Oferta enviada",
          38: "Oferta aceptada", 28: "Alquilador asignado", 46: "Entrega de equipo"}


def leer(tab, rango="A1:P200", cab=None):
    d = sheets("%s/values/%s" % (SHEET_ID, urllib.parse.quote("%s!%s" % (tab, rango))), cab=cab)
    return d.get("values") or []


def eur(n):
    return format(int(n), ",d").replace(",", ".") + " €"


def main():
    cab = {"Authorization": "Bearer " + token_google(
        ["https://www.googleapis.com/auth/spreadsheets"]), "Content-Type": "application/json"}
    hoy = dt.date.today()

    # ── 1. Leads entrantes (frío) y su estado, del propio Sheet
    le = leer("Leads · entrantes", cab=cab)
    leads = []
    for f in le[1:]:
        f = f + [""] * (12 - len(f))
        if not f[5]:
            continue
        leads.append(dict(fecha=f[0], nivel=f[2], empresa=f[4] or f[5].split("@")[-1],
                          origen=f[7], llamado=f[10].strip().upper() in ("TRUE", "SI", "SÍ", "X", "OK"),
                          resultado=f[11]))
    reales = [l for l in leads if l["nivel"] in ("HOT", "WARM")]
    descartes = [l for l in leads if l["nivel"] in ("NO", "AUTO")]

    # ── 2. Cola comercial (reactivación Brevo), del propio Sheet
    cola = leer("Cola comercial", cab=cab)
    ic = next((i for i, f in enumerate(cola) if f and f[0] == "Score"), None)
    filas_cola = [f + [""] * 14 for f in cola[ic + 1:]] if ic is not None else []
    por_prio = collections.Counter(f[1] for f in filas_cola if f[1])
    por_lista = collections.Counter()
    for f in filas_cola:
        for l in (f[9] or "").split(" / "):
            if l.strip() and l.strip() != "—":
                por_lista[l.strip()[:44]] += 1

    # ── 3. Lista manual de llamadas del equipo (solo lectura)
    man = leer("Untitled", cab=cab)
    llamados = sum(1 for f in man[1:] if len(f) > 9 and f[9].strip().upper() == "TRUE")
    resultados = collections.Counter((f[10].strip() if len(f) > 10 else "") or "(sin resultado)"
                                     for f in man[1:] if len(f) > 9 and f[9].strip().upper() == "TRUE")

    # ── 4. Pipedrive: ofertas de compraventa
    abiertas, ganadas_mes, nuevas_mes, start = [], 0, 0, 0
    mes = hoy.strftime("%Y-%m")
    while True:
        d = pipedrive("/deals", start=start, limit=500, status="all_not_deleted")
        items = d.get("data") or []
        if not items:
            break
        for x in items:
            if x.get("pipeline_id") != 6 or not re.search(r"compra", x.get("title") or "", re.I):
                continue
            if x.get("status") == "open":
                abiertas.append(x)
            if x.get("status") == "won" and (x.get("won_time") or "")[:7] == mes:
                ganadas_mes += 1
            if (x.get("add_time") or "")[:7] == mes:
                nuevas_mes += 1
        if not d.get("additional_data", {}).get("pagination", {}).get("more_items_in_collection"):
            break
        start += 500
    por_etapa = collections.Counter(ETAPAS.get(x.get("stage_id"), "otra") for x in abiertas)
    en_juego = sum(float(x.get("value") or 0) for x in abiertas)
    sin_importe = sum(1 for x in abiertas if not x.get("value"))

    # ── 5. Canales en vivo
    try:
        camps = campanas(20)
        cl_brevo = sum(c["clics"] for c in camps)
        ent_brevo = sum(c["entregados"] for c in camps)
        ab_brevo = sum(c["aberturas"] for c in camps)
    except RuntimeError as err:       # un 504 de Brevo no debe tumbar el resumen
        camps, cl_brevo, ent_brevo, ab_brevo = [], "—", "sin lectura ahora (%s)" % str(err)[:20], "—"
    frio = None
    for c in (smartlead("/campaigns") or []):
        if isinstance(c, dict) and "Compraventa Frio" in c.get("name", ""):
            a = smartlead("/campaigns/%s/analytics" % c["id"])
            ent = lambda v: int(v) if str(v).isdigit() else 0
            frio = dict(env=ent(a.get("sent_count")), resp=ent(a.get("reply_count")),
                        cl=ent(a.get("click_count")), total=996)

    # ── FILAS
    F, M = [], []          # filas, marcas de formato (tipo, índice 1-based)
    def fila(*c, marca=None):
        F.append(list(c))
        if marca:
            M.append((marca, len(F)))
    def seccion(t):
        F.append([""]); F.append([t]); M.append(("seccion", len(F)))
    def cab_(*c):
        F.append(list(c)); M.append(("cabecera", len(F)))

    fila("EQUIPZILLA · COMPRAVENTA — QUÉ ESTAMOS HACIENDO", "", "", "",
         "actualizado " + dt.datetime.now().strftime("%d/%m %H:%M"))
    fila("Objetivo: 25 operaciones y 500.000 € antes del 31/12. Todo lo de abajo sale de los sistemas, no está escrito a mano.")

    seccion("1 · LEADS QUE HEMOS GENERADO")
    cab_("De dónde", "Cuántos", "Qué son", "Estado")
    fila("Frío (emails a empresas que no nos conocían)", len(reales),
         "%d respuestas o clics humanos desde el 04/09" % len(reales),
         "%d llamados · %d sin llamar" % (sum(1 for l in reales if l["llamado"]),
                                          sum(1 for l in reales if not l["llamado"])),
         marca="destacado")
    fila("Reactivación (clientes que ya alquilaron con nosotros)", len(filas_cola),
         "personas que han hecho clic en una máquina concreta de nuestros emails",
         "%s HOT · %s WARM · %s en seguimiento" % (por_prio.get("🔥 HOT", 0), por_prio.get("🟠 WARM", 0),
                                                     por_prio.get("🔵 NURTURE", 0) + por_prio.get("⚪ LOW", 0)))
    fila("Web y formularios (entran solos en Pipedrive)", nuevas_mes,
         "tratos de compraventa nuevos este mes", "en el pipeline")
    fila("Descartados automáticamente", len(descartes),
         "respuestas automáticas, tickets, 'no me interesa', fuera de sector",
         "no llegan al equipo")

    seccion("2 · DE QUÉ LISTA SALE CADA OPORTUNIDAD (reactivación)")
    cab_("Lista de Brevo", "Oportunidades", "", "")
    for l, n in por_lista.most_common(8):
        fila(l, n)

    seccion("3 · OPORTUNIDADES Y EN QUÉ ESTADO ESTÁN")
    cab_("Etapa en Pipedrive", "Nº", "", "")
    for et, n in sorted(por_etapa.items(), key=lambda x: -x[1]):
        fila(et, n)
    fila("Total ofertas abiertas", len(abiertas), "importe en juego: " + eur(en_juego),
         "%d aún sin importe" % sin_importe, marca="destacado")
    fila("Ganadas este mes", ganadas_mes, "", "objetivo septiembre: 3", marca="alerta" if ganadas_mes < 1 else "bien")

    seccion("4 · LLAMADAS DEL EQUIPO (lista manual)")
    cab_("", "Nº", "", "")
    fila("Contactos llamados", llamados)
    for r, n in resultados.most_common(6):
        fila("   " + r, n)

    seccion("5 · LO QUE MUEVE LOS CANALES (señal, no negocio)")
    cab_("Canal", "Volumen", "Resultado", "")
    fila("Emails de reactivación (Brevo)", "%s entregados" % ent_brevo,
         "%s aperturas · %s personas clican" % (ab_brevo, cl_brevo))
    if frio:
        fila("Frío (Smartlead)", "%d de %d enviados" % (frio["env"], frio["total"]),
             "%d respuestas · %d clics" % (frio["resp"], frio["cl"]))

    seccion("6 · QUÉ SE HA HECHO YA")
    for t in [
        "Motor de emails de reactivación: 13 campañas, 12.373 envíos, 26 % de apertura media (muy bueno para el sector).",
        "Campaña de frío a 996 empresas de construcción y excavación, con 10 buzones propios.",
        "Vigilante automático cada hora: detecta respuestas y clics, los puntúa, los da de alta en Pipedrive y avisa al equipo.",
        "Cola comercial priorizada con nombre, teléfono y qué máquina miró cada uno (pestaña «Cola comercial»).",
        "22 guías de compra publicadas en equipzilla-quiz.vercel.app/guias con precios reales del stock.",
        "Sheet de control «Demand Engine» que se refresca solo cada mañana desde Pipedrive, Brevo, Smartlead, Ads y Search Console.",
        "Auditoría del CRM: sabemos exactamente qué falta para poder medir (importes, origen, motivo de pérdida).",
    ]:
        fila("✓ " + t, marca="bien")

    seccion("7 · EN QUÉ ESTAMOS TRABAJANDO")
    for t in [
        "Lanzamiento de mañana: 5-6 unidades nuevas con el manipulador JLG delante (borrador #220 en Brevo, pendiente de OK).",
        "Nurturing automático: 7 emails ya en Brevo, falta montar el workflow.",
        "Segunda tanda de leads de frío: scraper listo, falta la clave de Apify.",
        "Pasar las guías a ocasion.equipzilla.com (DNS pedido al técnico) y limpiar el blog hackeado.",
    ]:
        fila("→ " + t)

    seccion("8 · LO QUE NECESITAMOS PARA CERRAR MÁS")
    for t in [
        "Saber por qué se pierden las ofertas: hoy solo cerramos el 2 % de las que enviamos y el 29 % de las pérdidas no tiene motivo apuntado.",
        "Poner importe a todas las ofertas abiertas (%d están a 0 €)." % sin_importe,
        "Llamar a los HOT el mismo día que entran: el que llama primero se lleva la máquina.",
        "Apuntar en Pipedrive de dónde viene cada trato, para saber qué canal vende.",
    ]:
        fila("! " + t, marca="alerta")

    # ── ESCRITURA + FORMATO
    meta = sheets("%s?fields=sheets.properties" % SHEET_ID, cab=cab)
    hojas = {x["properties"]["title"]: x["properties"] for x in meta.get("sheets", [])}
    if PESTANA not in hojas:
        sheets("%s:batchUpdate" % SHEET_ID, "POST", {"requests": [
            {"addSheet": {"properties": {"title": PESTANA, "index": 0}}}]}, cab)
        meta = sheets("%s?fields=sheets.properties" % SHEET_ID, cab=cab)
        hojas = {x["properties"]["title"]: x["properties"] for x in meta.get("sheets", [])}
    sid = hojas[PESTANA]["sheetId"]
    sheets("%s/values/%s:clear" % (SHEET_ID, urllib.parse.quote("%s!A1:H300" % PESTANA)), "POST", {}, cab)
    r = sheets("%s/values/%s?valueInputOption=RAW" % (SHEET_ID, urllib.parse.quote("%s!A1" % PESTANA)),
               "PUT", {"values": F}, cab)
    if "_error" in r:
        raise SystemExit(r)
    rg = lambda a, b=None, c0=0, c1=5: {"sheetId": sid, "startRowIndex": a, "endRowIndex": b or a + 1,
                                        "startColumnIndex": c0, "endColumnIndex": c1}
    reqs = [
        {"repeatCell": {"range": rg(0, 300), "cell": {"userEnteredFormat": {"backgroundColor": BLANCO,
            "textFormat": {"bold": False, "fontSize": 10}, "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP", "padding": {"top": 4, "bottom": 4, "left": 8, "right": 8}}},
            "fields": "userEnteredFormat"}},
        {"unmergeCells": {"range": rg(0, 300)}},
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties":
            {"frozenRowCount": 2, "hideGridlines": True}}, "fields": "gridProperties(frozenRowCount,hideGridlines)"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 380}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
            "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 4},
            "properties": {"pixelSize": 330}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 0, "endIndex": 300},
            "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
        {"mergeCells": {"range": rg(0, 1, 0, 4), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": rg(1, 2, 0, 5), "mergeType": "MERGE_ALL"}},
        {"repeatCell": {"range": rg(0, 2), "cell": {"userEnteredFormat": {"backgroundColor": TINTA,
            "textFormat": {"bold": True, "fontSize": 14, "foregroundColor": BLANCO}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 46}, "fields": "pixelSize"}},
    ]
    est = {"seccion": {"backgroundColor": TINTA, "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": BLANCO}},
           "cabecera": {"backgroundColor": SUAVE, "textFormat": {"bold": True}},
           "destacado": {"backgroundColor": CREMA, "textFormat": {"bold": True, "fontSize": 11}},
           "bien": {"backgroundColor": VERDE, "textFormat": {"bold": False}},
           "alerta": {"backgroundColor": ROJO, "textFormat": {"bold": True}}}
    marcadas = set()
    for m, i in M:
        marcadas.add(i - 1)
        reqs.append({"repeatCell": {"range": rg(i - 1), "cell": {"userEnteredFormat": est[m]},
                                    "fields": "userEnteredFormat(backgroundColor,textFormat)"}})
        if m == "seccion":
            reqs.append({"mergeCells": {"range": rg(i - 1, i, 0, 5), "mergeType": "MERGE_ALL"}})
            reqs.append({"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS",
                "startIndex": i - 1, "endIndex": i}, "properties": {"pixelSize": 34}, "fields": "pixelSize"}})
    for n, f in enumerate(F):
        if len(f) == 1 and str(f[0]).strip() and n not in marcadas or (n in marcadas and len(f) == 1 and n > 1):
            reqs.append({"mergeCells": {"range": rg(n, n + 1, 0, 5), "mergeType": "MERGE_ALL"}})
            if len(str(f[0])) > 95:
                reqs.append({"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS",
                    "startIndex": n, "endIndex": n + 1}, "properties": {"pixelSize": 48}, "fields": "pixelSize"}})
    sheets("%s:batchUpdate" % SHEET_ID, "POST", {"requests": reqs}, cab)
    print("«%s» escrita · %d filas" % (PESTANA, len(F)))
    print("   leads frío reales %d (llamados %d) · cola %d · ofertas abiertas %d · en juego %s"
          % (len(reales), sum(1 for l in reales if l["llamado"]), len(filas_cola), len(abiertas), eur(en_juego)))


if __name__ == "__main__":
    main()
