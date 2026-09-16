#!/usr/bin/env python3
"""Tabla mensual de compraventa, al estilo de la tabla histórica de la empresa
pero con nuestros canales: Frío (Smartlead), Reactivación (Brevo), Google Ads
y Web. Pedida por Maikel el 08/09.

Con `--semanal` escribe la misma tabla por semanas ISO (últimas 14) en la
pestaña «Semanal · compraventa»; sin argumento, la mensual de siempre. Las
definiciones de cada columna son idénticas en ambas: solo cambia el periodo.

Columnas de datos: las escribe este script desde Pipedrive, Smartlead, Brevo
y Google Ads. Columnas económicas (comisión, inversión total, CPL, CAC, ROAS,
beneficio): fórmulas de Sheets que apuntan a tres celdas de entrada arriba
(% comisión, coste mensual de Brevo y de Smartlead), para que el equipo las
ajuste sin tocar el script. Lo que no se puede medir va como NO DETERMINADO.
"""
import collections, datetime as dt, os, re, sys, urllib.parse
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import (SHEET_ID, campanas, deals_todos, pipedrive, sheets, smartlead, token_google)
import ads_metricas as ADS
import cola_comercial as cc


def es_compraventa(titulo):
    """Mismo criterio que la cola comercial (título): 'compra', 'prospecto' (frío)
    y 'clic campaña' son compraventa; 'renting', 'alquiler' y 'solicitud por rent' no.
    Criterio provisional hasta que la etiqueta VENTA/RENTING de Pipedrive se rellene
    en el alta (ver reportes/crm-datos/2026-09-15.md)."""
    t = re.sub(r"^[0-9a-f-]{36} ?-\s*", "", titulo or "")
    return bool(cc.COMPRAVENTA.search(t)) and not cc.NO_COMPRAVENTA.search(t)

PESTANA = "Mensual · compraventa"
TINTA = {"red": 0.09, "green": 0.20, "blue": 0.23}; SUAVE = {"red": 0.93, "green": 0.95, "blue": 0.96}
CREMA = {"red": 0.99, "green": 0.96, "blue": 0.89}; BLANCO = {"red": 1, "green": 1, "blue": 1}
ETAPA_OFERTA = (37, 38, 28, 46)
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def mes_de(iso):
    return (iso or "")[:7]


def semana_de(iso):
    """Clave de semana ISO: '2026-W37' (lunes a domingo)."""
    try:
        y, w, _ = dt.date.fromisoformat((iso or "")[:10]).isocalendar()
        return "%d-W%02d" % (y, w)
    except ValueError:
        return ""


PERIODO = mes_de           # main() lo cambia a semana_de con --semanal


def etiqueta(k):
    if "W" in k:
        lunes = dt.date.fromisocalendar(int(k[:4]), int(k[6:]), 1)
        dom = lunes + dt.timedelta(days=6)
        return "'S%s · %02d %s - %02d %s" % (k[6:], lunes.day, MESES[lunes.month - 1], dom.day, MESES[dom.month - 1])
    return "'%s %s" % (MESES[int(k[5:]) - 1], k[:4])


def pipedrive_mensual():
    m = collections.defaultdict(lambda: dict(leads=0, ofertas=0, ventas=0, gmv_op=0.0, gmv_venta=0.0))
    for x in deals_todos():
        if x.get("pipeline_id") not in cc.PIPELINES or not es_compraventa(x.get("title")):
            continue
        k = PERIODO(x.get("add_time"))
        if not k:
            continue
        m[k]["leads"] += 1
        m[k]["gmv_op"] += float(x.get("value") or 0)
        if x.get("stage_id") in ETAPA_OFERTA or x.get("status") == "won":
            m[k]["ofertas"] += 1
        if x.get("status") == "won":
            kw = PERIODO(x.get("won_time")) or k
            m[kw]["ventas"] += 1
            m[kw]["gmv_venta"] += float(x.get("value") or 0)
    return m


def frio_mensual():
    """Personas del frío con respuesta o clic humano, por mes."""
    m = collections.defaultdict(set)
    cs = smartlead("/campaigns")
    for c in (cs if isinstance(cs, list) else cs.get("data", [])):
        off = 0
        while True:
            st = smartlead("/campaigns/%s/statistics?offset=%d&limit=1000" % (c["id"], off))
            filas = st.get("data", []) if isinstance(st, dict) else []
            for f in filas:
                e = (f.get("lead_email") or "").lower()
                if f.get("reply_time"):
                    m[PERIODO(f["reply_time"])].add(e)
                elif f.get("click_time"):
                    ab, cl, env = f.get("open_time"), f.get("click_time"), f.get("sent_time")
                    escaner = False
                    if ab and env and ab[:19] == cl[:19]:
                        try:
                            t0 = dt.datetime.strptime(env[:19], "%Y-%m-%dT%H:%M:%S")
                            t1 = dt.datetime.strptime(cl[:19], "%Y-%m-%dT%H:%M:%S")
                            escaner = (t1 - t0).total_seconds() <= 180
                        except ValueError:
                            pass
                    if not escaner:
                        m[PERIODO(cl)].add(e)
            if len(filas) < 1000:
                break
            off += 1000
    return {k: len(v) for k, v in m.items()}


def brevo_mensual():
    m = collections.Counter()
    for c in campanas(50):
        m[PERIODO(c["fecha"])] += c["clics"]       # personas que clican
    return m


def ads_mensual():
    seg = "segments.week" if PERIODO is semana_de else "segments.month"
    q = ("SELECT %s, metrics.cost_micros, metrics.clicks, metrics.conversions "
         "FROM campaign WHERE segments.date BETWEEN '2026-01-01' AND '%s'" % (seg, dt.date.today()))
    m = collections.defaultdict(lambda: dict(coste=0.0, clics=0, conv=0.0))
    try:
        for r in ADS.consulta(q):
            k = PERIODO(r.get("segments", {}).get("week") or r.get("segments", {}).get("month") or "")
            me = r.get("metrics", {})
            m[k]["coste"] += int(me.get("costMicros", 0)) / 1e6
            m[k]["clics"] += int(me.get("clicks", 0))
            m[k]["conv"] += float(me.get("conversions", 0))
    except Exception as err:
        print("  aviso: Google Ads no responde (%s)" % err)
    return m


def main(semanal=False):
    global PERIODO, PESTANA
    if semanal:
        PERIODO, PESTANA = semana_de, "Semanal · compraventa"
    pd_, fr, br, ads = pipedrive_mensual(), frio_mensual(), brevo_mensual(), ads_mensual()
    hoy = dt.date.today()
    if semanal:
        lunes = hoy - dt.timedelta(days=hoy.weekday())
        meses = [semana_de((lunes - dt.timedelta(weeks=13 - i)).isoformat()) for i in range(14)]
        titulo, col0, total = "SEMANAL · COMPRAVENTA (últimas 14 semanas ISO, lunes a domingo)", "Semana", "TOTAL 14 semanas"
        fijo = "($E$2+$G$2)*7/30"          # coste mensual prorrateado a la semana
    else:
        meses = ["2026-%02d" % i for i in range(1, hoy.month + 1)]
        titulo, col0, total = "MENSUAL · COMPRAVENTA", "Mes", "TOTAL 2026"
        fijo = "$E$2+$G$2"

    F = [[titulo, "", "", "", "", "", "", "",
          "datos: Pipedrive, Smartlead, Brevo, Google Ads · actualizado "
          + dt.datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m %H:%M")],
         ["ENTRADAS (edita aquí)", "% comisión", 0.10, "Coste Brevo €/mes", 0, "Coste Smartlead €/mes", 0,
          "", "Cambia estas tres celdas y toda la tabla se recalcula"],
         [],
         [col0, "Señales frío (Smartlead)", "Señales reactivación (Brevo)", "Leads Google Ads",
          "Tratos en Pipedrive", "Ofertas enviadas", "% oferta", "Ventas", "% venta a trato",
          "GMV oportunidad", "GMV venta", "Ticket medio", "Comisión", "Inversión Ads",
          "Inversión total", "CPL (señales)", "CAC", "ROAS", "Beneficio",
          "Sesiones web", "Particulares / Empresas / Autónomos"]]
    r0 = len(F) + 1            # primera fila de datos (1-based)
    for i, k in enumerate(meses):
        r = r0 + i
        p = pd_.get(k, dict(leads=0, ofertas=0, ventas=0, gmv_op=0.0, gmv_venta=0.0))
        a = ads.get(k, dict(coste=0.0, clics=0, conv=0.0))
        F.append([
            etiqueta(k) + (" (en curso)" if k == PERIODO(hoy.isoformat()) else ""),
            fr.get(k, 0), br.get(k, 0), int(a["conv"]),
            p["leads"], p["ofertas"], "=IF(E%d=0;\"\";F%d/E%d)" % (r, r, r),
            p["ventas"], "=IF(E%d=0;\"\";H%d/E%d)" % (r, r, r),
            round(p["gmv_op"]), round(p["gmv_venta"]),
            "=IF(H%d=0;\"\";K%d/H%d)" % (r, r, r),
            "=K%d*$C$2" % r,
            round(a["coste"], 2),
            "=N%d+%s" % (r, fijo),
            "=IF((B%d+C%d+D%d)=0;\"\";O%d/(B%d+C%d+D%d))" % (r, r, r, r, r, r, r),
            "=IF(H%d=0;\"\";O%d/H%d)" % (r, r, r),
            "=IF(O%d=0;\"\";M%d/O%d)" % (r, r, r),
            "=M%d-O%d" % (r, r),
            "NO DETERMINADO (GA4 sin conectar)", "NO DETERMINADO (sin campo en Pipedrive)"])
    r1 = r0 + len(meses) - 1
    F.append([total,
              "=SUM(B%d:B%d)" % (r0, r1), "=SUM(C%d:C%d)" % (r0, r1), "=SUM(D%d:D%d)" % (r0, r1),
              "=SUM(E%d:E%d)" % (r0, r1), "=SUM(F%d:F%d)" % (r0, r1),
              "=IF(E%d=0;\"\";F%d/E%d)" % (r1 + 1, r1 + 1, r1 + 1),
              "=SUM(H%d:H%d)" % (r0, r1), "=IF(E%d=0;\"\";H%d/E%d)" % (r1 + 1, r1 + 1, r1 + 1),
              "=SUM(J%d:J%d)" % (r0, r1), "=SUM(K%d:K%d)" % (r0, r1),
              "=IF(H%d=0;\"\";K%d/H%d)" % (r1 + 1, r1 + 1, r1 + 1),
              "=SUM(M%d:M%d)" % (r0, r1), "=SUM(N%d:N%d)" % (r0, r1), "=SUM(O%d:O%d)" % (r0, r1),
              "=IF((B%d+C%d+D%d)=0;\"\";O%d/(B%d+C%d+D%d))" % ((r1 + 1,) * 7),
              "=IF(H%d=0;\"\";O%d/H%d)" % (r1 + 1, r1 + 1, r1 + 1),
              "=IF(O%d=0;\"\";M%d/O%d)" % (r1 + 1, r1 + 1, r1 + 1),
              "=M%d-O%d" % (r1 + 1, r1 + 1), "", ""])
    F += [[], ["CÓMO LEERLA"],
          ["Señales de canal (B-D) no son tratos: son personas que respondieron o clicaron. Los tratos (E) son lo que entra en Pipedrive."],
          ["Trato de compraventa = título con «compra», «prospecto» (frío) o «clic campaña», sin «alquiler» ni «renting». Mismo criterio que la pestaña «Cola comercial» desde el 15/09; antes solo contaba «compra»."],
          ["GMV oportunidad = suma de importes de los tratos creados en el periodo (muchos están a 0 €: ver auditoría). GMV venta = importe de los ganados ese mes."],
          ["Frío empieza en agosto 2026 y reactivación en julio 2026: antes no había campañas. Google Ads, desde que hay cuenta."],
          ["Sesiones web y tipo de cliente no se pueden medir hoy: falta conectar GA4 y falta el campo en Pipedrive."]]

    cab = {"Authorization": "Bearer " + token_google(["https://www.googleapis.com/auth/spreadsheets"]),
           "Content-Type": "application/json"}
    meta = sheets("%s?fields=sheets.properties" % SHEET_ID, cab=cab)
    hojas = {x["properties"]["title"]: x["properties"] for x in meta.get("sheets", [])}
    if PESTANA not in hojas:
        sheets("%s:batchUpdate" % SHEET_ID, "POST", {"requests": [{"addSheet": {"properties": {"title": PESTANA, "index": 1}}}]}, cab)
        meta = sheets("%s?fields=sheets.properties" % SHEET_ID, cab=cab)
        hojas = {x["properties"]["title"]: x["properties"] for x in meta.get("sheets", [])}
    sid = hojas[PESTANA]["sheetId"]
    sheets("%s/values/%s:clear" % (SHEET_ID, urllib.parse.quote("%s!A1:V100" % PESTANA)), "POST", {}, cab)
    r = sheets("%s/values/%s?valueInputOption=USER_ENTERED" % (SHEET_ID, urllib.parse.quote("%s!A1" % PESTANA)),
               "PUT", {"values": F}, cab)
    if "_error" in r:
        raise SystemExit(r)
    rg = lambda a, b=None, c0=0, c1=21: {"sheetId": sid, "startRowIndex": a, "endRowIndex": b or a + 1,
                                         "startColumnIndex": c0, "endColumnIndex": c1}
    eur = {"numberFormat": {"type": "NUMBER", "pattern": "#,##0 €"}}
    pct = {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}
    reqs = [
        {"repeatCell": {"range": rg(0, 100), "cell": {"userEnteredFormat": {"backgroundColor": BLANCO,
            "textFormat": {"bold": False, "fontSize": 10}, "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}},
            "fields": "userEnteredFormat"}},
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 4, "frozenColumnCount": 1}},
            "fields": "gridProperties(frozenRowCount,frozenColumnCount)"}},
        {"repeatCell": {"range": rg(0, 1), "cell": {"userEnteredFormat": {"backgroundColor": TINTA,
            "textFormat": {"bold": True, "fontSize": 13, "foregroundColor": BLANCO}}}, "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"repeatCell": {"range": rg(1, 2), "cell": {"userEnteredFormat": {"backgroundColor": CREMA, "textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"repeatCell": {"range": rg(1, 2, 2, 3), "cell": {"userEnteredFormat": pct}, "fields": "userEnteredFormat.numberFormat"}},
        {"repeatCell": {"range": rg(1, 2, 4, 5), "cell": {"userEnteredFormat": eur}, "fields": "userEnteredFormat.numberFormat"}},
        {"repeatCell": {"range": rg(1, 2, 6, 7), "cell": {"userEnteredFormat": eur}, "fields": "userEnteredFormat.numberFormat"}},
        {"repeatCell": {"range": rg(3, 4), "cell": {"userEnteredFormat": {"backgroundColor": SUAVE, "textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 3, "endIndex": 4},
            "properties": {"pixelSize": 54}, "fields": "pixelSize"}},
        {"repeatCell": {"range": rg(r1, r1 + 1), "cell": {"userEnteredFormat": {"backgroundColor": SUAVE, "textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 110}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 21},
            "properties": {"pixelSize": 96}, "fields": "pixelSize"}},
    ]
    for c in (6, 8):                         # % oferta, % venta
        reqs.append({"repeatCell": {"range": rg(r0 - 1, r1 + 1, c, c + 1), "cell": {"userEnteredFormat": pct}, "fields": "userEnteredFormat.numberFormat"}})
    for c in (9, 10, 11, 12, 13, 14, 15, 16, 18):   # euros
        reqs.append({"repeatCell": {"range": rg(r0 - 1, r1 + 1, c, c + 1), "cell": {"userEnteredFormat": eur}, "fields": "userEnteredFormat.numberFormat"}})
    reqs.append({"repeatCell": {"range": rg(r0 - 1, r1 + 1, 17, 18), "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.0\"x\""}}}, "fields": "userEnteredFormat.numberFormat"}})
    sheets("%s:batchUpdate" % SHEET_ID, "POST", {"requests": reqs}, cab)
    print("«%s» escrita · %d meses" % (PESTANA, len(meses)))
    for k in meses:
        p = pd_.get(k, {}); a = ads.get(k, {})
        print("  %s  frío %2d  react %3d  ads %2d | tratos %2d ofertas %2d ventas %d | gmv_op %8.0f | ads %7.2f €"
              % (k, fr.get(k, 0), br.get(k, 0), int(a.get("conv", 0)), p.get("leads", 0), p.get("ofertas", 0),
                 p.get("ventas", 0), p.get("gmv_op", 0), a.get("coste", 0)))


if __name__ == "__main__":
    main(semanal="--semanal" in sys.argv)
