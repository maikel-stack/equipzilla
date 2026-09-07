#!/usr/bin/env python3
"""Escribe la pestaña «Resumen semanal» del Sheet de mando, con formato.

Pedido por Maikel (07/09) para revisarlo con el equipo. Es una foto para
humanos, no un volcado: cada bloque lleva su lectura y las cifras salen de
Pipedrive, Smartlead, Google Ads y Search Console. Lo que no se puede medir
se dice, no se rellena.
"""
import sys, os, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import SHEET_ID, sheets, token_google

PESTANA = "Resumen semanal"
TINTA   = {"red": 0.09, "green": 0.20, "blue": 0.23}   # verde petróleo Equipzilla
ALERTA  = {"red": 0.70, "green": 0.23, "blue": 0.16}
SUAVE   = {"red": 0.93, "green": 0.95, "blue": 0.96}
CREMA   = {"red": 0.99, "green": 0.96, "blue": 0.89}
BLANCO  = {"red": 1, "green": 1, "blue": 1}

filas, formatos = [], []


def bloque(titulo):
    filas.append([""])
    filas.append([titulo])
    formatos.append(("seccion", len(filas)))


def cabecera(*celdas):
    formatos.append(("cabecera", len(filas) + 1))
    filas.append(list(celdas))


def fila(*celdas, marca=None):
    if marca:
        formatos.append((marca, len(filas) + 1))
    filas.append(list(celdas))


# ─────────────────────────────────────────────────────────────────────
fila("EQUIPZILLA · COMPRAVENTA — ESTADO Y PLAN", "", "", "",
     "actualizado 07/09/2026 · 11:30 (Madrid)")
fila("Objetivo: 25 operaciones · 500.000 € GMV · 31/12/2026")

bloque("0 · EL DIAGNÓSTICO — dónde se rompe de verdad")
fila("He medido el histórico completo de compraventa en Pipedrive: 195 leads desde enero.", marca="destacado")
fila("Generar leads NO es el problema. Cerrarlos, sí.", marca="destacado")
fila("")
cabecera("Paso del embudo", "Real medido", "Lo que asumía el plan", "Veredicto")
fila("Lead → oferta enviada", "48 %  (94 de 195)", "37 %", "MEJOR de lo previsto")
fila("Oferta enviada → venta", "2,1 %  (2 de 94)", "19,5 %", "9 VECES PEOR ← aquí está el cuello", marca="alerta")
fila("")
fila("Traducido: enviamos ofertas y no se cierran — 75 muertas contra 2 ganadas. Y esas 2 son de "
     "febrero de 2025, con importe 0 €, y parecen la misma operación duplicada.")

bloque("0b · POR QUÉ SE PIERDEN (178 operaciones perdidas)")
cabecera("Motivo registrado", "Nº", "%", "Qué significa")
fila("OTRAS - General", "52", "29 %", "SIN DIAGNÓSTICO. Casi un tercio no sabemos por qué murió.", marca="alerta")
fila("Falta de respuesta tras varios intentos", "22", "12 %", "Contactamos tarde o pocas veces")
fila("No tiene interés real", "17", "10 %", "Lead mal cualificado")
fila("Interés inicial bajo o nulo", "16", "9 %", "Lead mal cualificado")
fila("Cliente gestionó por su cuenta", "13", "7 %", "Le dimos la info y compró en otro sitio")
fila("Proveedor no tiene ese equipo", "11", "6 %", "Hueco de sourcing")
fila("No podemos contactar", "10", "6 %", "Datos malos o llamada tardía")
fila("Precio no competitivo", "5", "3 %", "El precio NO es el problema principal")
fila("No tenemos alquilador para dar servicio", "4", "2 %", "Hueco de sourcing")
fila("Solo estaba comparando precios", "4", "2 %", "")
fila("")
fila("Suma la lectura: 18 % se pierde por no llegar a tiempo al cliente, 19 % por leads que nunca "
     "fueron reales, 8 % porque no teníamos la máquina — y solo un 3 % por precio.")

bloque("1 · ¿LLEGAMOS A 25 OPERACIONES EL 31/12?")
cabecera("Escenario", "Ofertas/mes", "% cierre", "Ventas a 31/12", "GMV estimado")
fila("Si todo sigue igual", "8", "2,1 %", "1", "20.000 €", marca="alerta")
fila("Si arreglamos el cierre", "8", "15 %", "6", "120.000 €")
fila("Si arreglamos cierre Y triplicamos ofertas", "24", "15 %", "16", "320.000 €", marca="bien")
fila("Lo que haría falta para los 25", "24", "24 %", "25", "500.000 €")
fila("")
fila("Quedan 16 semanas. Con los números de hoy, 25 operaciones no sale.", marca="destacado")
fila("Con el cierre arreglado y triplicando ofertas nos plantamos en 15-16 operaciones (~320.000 €). "
     "Prefiero decírtelo ahora que en diciembre: el objetivo no se salva metiendo más leads arriba, "
     "se salva arreglando la mitad de abajo del embudo.")

bloque("2 · LAS TRES PALANCAS, POR ORDEN DE EVIDENCIA")
cabecera("#", "Palanca", "Evidencia que la respalda", "Impacto esperado")
fila("1", "Autopsia de las ofertas perdidas",
     "52 de 178 sin motivo real registrado. No podemos arreglar lo que no medimos.",
     "Es la que desbloquea todo lo demás", marca="bien")
fila("2", "Subir presupuesto de Shopping",
     "Pierde el 59,5 % de las impresiones por presupuesto, a 0,21 € el clic",
     "De 20 a 50 €/día ≈ 2,5x volumen al mismo coste por clic", marca="bien")
fila("3", "Velocidad de primera llamada",
     "32 de 178 perdidas por 'no podemos contactar' o 'falta de respuesta'",
     "Llamar el mismo día, no a los tres")
fila("4", "Campaña de carretillas",
     "Mejor ratio de clic del motor (0,88 %) + quick win en Google (pos. 5-10)",
     "Lista de 288 contactos ya preparada")
fila("5", "Sourcing bajo pedido",
     "15 perdidas por no tener el equipo. Hoy mismo: sanfer pide carretilla eléctrica",
     "Recupera ~8 % de las perdidas")

bloque("3 · QUÉ NECESITO DE TI (por orden)")
cabecera("#", "Qué", "Por qué", "Cuánto cuesta")
fila("1", "30 min con David repasando las últimas 20 ofertas perdidas",
     "Es LO MÁS IMPORTANTE. Sin saber por qué mueren las ofertas, todo lo que automatizo "
     "está optimizando la mitad del embudo que ya funciona.", "30 min", marca="alerta")
fila("2", "Autorizar el rango 160.79.106.0/24 en Brevo",
     "app.brevo.com/security/authorised_ips — lleva 4 días bloqueándonos. Desbloquea métricas "
     "ABM, cola comercial, avisos al equipo y los seguimientos f2.", "2 min", marca="alerta")
fila("3", "Importes de las 15 ofertas vivas",
     "Están todas a 0 €. Sin ellos no hay forma de medir GMV contra los 500.000 €.", "20 min")
fila("4", "Decisión sobre el presupuesto de Google Ads",
     "Shopping da volumen a 0,21 €/clic y se queda corto de presupuesto el 60 % del tiempo. "
     "¿Subimos de 20 a 50 €/día? Son 900 €/mes más.", "tu decisión")
fila("5", "¿Podemos comprar bajo pedido?",
     "Sanfer quiere carretilla eléctrica urgente + otra en octubre y no la tenemos. "
     "15 operaciones perdidas por lo mismo.", "tu decisión")
fila("6", "Datos de la secuencia del frío",
     "Anuncia la Kubota KX016-4 con 1,5 t y 600 h; en stock son 0,8 t y 250 h. "
     "Sigue enviando: 571 emails ya.", "tu decisión")
fila("7", "Accesos del hosting del blog",
     "blog.equipzilla.com sirve spam de casino a Googlebot. Riesgo de penalización "
     "para todo el dominio. Bloquea 8 artículos ya escritos.", "los accesos")

bloque("4 · CÓMO VAN LOS CANALES")
cabecera("Canal", "Volumen", "Resultado", "Coste", "Lectura")
fila("ABM (Brevo)", "11.192 envíos", "25,8 % apertura · 56 clics", "—",
     "Apertura muy buena. SIN LECTURA desde el 04/09 por el bloqueo de IP.")
fila("Frío (Smartlead)", "571 de 996 leads", "16 respuestas · 2,80 %", "—",
     "BAJANDO: 3,13 → 3,01 → 2,90 → 2,80 %. Enviamos y no entran respuestas.", marca="alerta")
fila("Google Ads · Búsqueda", "4.630 impr · 611 clics", "3 conversiones", "514,30 €",
     "CPA 171 €. Pierde 19 % de impresiones por presupuesto.")
fila("Google Ads · Shopping", "249.610 impr · 2.224 clics", "2 conversiones", "463,03 €",
     "CPA 232 € a 0,21 €/clic. PIERDE EL 59,5 % POR PRESUPUESTO.", marca="bien")
fila("SEO (Search Console)", "28.079 impresiones", "310 clics · 49 consultas de compra", "—",
     "Ya rankeamos en carretillas y transpaletas (pos. 5-10).")

bloque("5 · LEADS CALIENTES SIN LLAMAR")
cabecera("Quién", "Teléfono", "Qué quiere", "Qué tenemos que encaja")
fila("jordiexcava@gmail.com", "+34 620 243 972", "Miniexcavadora 2-3 t Y minicargadora 2-3 t",
     "Develon DX 27 Z-7 (2,7 t · 31.900 €) · Kubota KX 030-4 GL (3 t · 35.900 €) · Bobcat S70 (23.500 €)")
fila("sanferempresaconstructora@gmail.com", "—", "Carretilla eléctrica URGENTE + otra en octubre",
     "NO tenemos. Es sourcing, y son 2 unidades.")
fila("Excavaciones Olivas (Albacete)", "678 838 714", "Clic en el email de miniexcavadoras",
     "Gama Kubota / Doosan mini")
fila("9TERRA (Vacarisses)", "+34 661 541 796", "Clic en catálogo Kubota mini", "Gama Kubota mini")
fila("Soliman Global Service (Ocaña)", "+34 624 015 421", "Clic en el frío", "Por cualificar")
fila("")
fila("Más 13 oportunidades HOT en la pestaña «Cola comercial» (del 04/09, sin refrescar por lo de Brevo).")

bloque("6 · LISTO Y ESPERANDO LUZ VERDE")
fila("Seguimientos f2 de los dos lanzamientos",
     "Auditados: las 10 máquinas cuadran con el stock. Excluyen a quien ya clicó. Faltan Brevo + tu OK.")
fila("8 artículos SEO escritos",
     "Bloqueados por los accesos del blog.")
fila("Campaña de carretillas a 288 contactos",
     "Respaldada por datos: mejor ratio de clic del motor + quick win en Google.")

bloque("7 · RUTINAS AUTOMÁTICAS EN MARCHA")
cabecera("Rutina", "Cuándo", "Qué hace")
fila("Panel en vivo", "cada hora, 8:00-21:00", "Escribe «Panel · en vivo» y «Clics nuevos · auto»")
fila("Informe de respuestas", "8:00 y 15:00", "Clasifica, puntúa, da de alta en Pipedrive y vuelca en «Leads · entrantes»")
fila("Cola comercial", "8:00", "Cruza los clics con el stock y prioriza por probabilidad de venta")
fila("Parte diario", "8:30", "Resumen a los cuatro")


def escribir():
    cab = {"Authorization": "Bearer " + token_google(
        ["https://www.googleapis.com/auth/spreadsheets"]),
        "Content-Type": "application/json"}
    meta = sheets("%s?fields=sheets.properties" % SHEET_ID, cab=cab)
    hojas = {x["properties"]["title"]: x["properties"] for x in meta.get("sheets", [])}
    if PESTANA not in hojas:
        sheets("%s:batchUpdate" % SHEET_ID, "POST",
               {"requests": [{"addSheet": {"properties": {"title": PESTANA, "index": 0}}}]}, cab)
        meta = sheets("%s?fields=sheets.properties" % SHEET_ID, cab=cab)
        hojas = {x["properties"]["title"]: x["properties"] for x in meta.get("sheets", [])}
    sid = hojas[PESTANA]["sheetId"]

    rng = urllib.parse.quote("%s!A1:H200" % PESTANA)
    sheets("%s/values/%s:clear" % (SHEET_ID, rng), "POST", {}, cab)
    r = sheets("%s/values/%s?valueInputOption=RAW"
               % (SHEET_ID, urllib.parse.quote("%s!A1" % PESTANA)), "PUT",
               {"values": filas}, cab)
    if "_error" in r:
        raise SystemExit("Sheets ERROR: %s" % r)

    def rango(f0, f1=None, c0=0, c1=8):
        return {"sheetId": sid, "startRowIndex": f0, "endRowIndex": f1 or f0 + 1,
                "startColumnIndex": c0, "endColumnIndex": c1}

    reqs = [
        # partir de un formato limpio: si no, quedan restos de versiones previas
        {"repeatCell": {"range": rango(0, 200), "cell": {"userEnteredFormat": {
            "backgroundColor": BLANCO, "textFormat": {"bold": False, "fontSize": 10,
            "foregroundColor": {"red": 0.1, "green": 0.1, "blue": 0.1}},
            "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP",
            "padding": {"top": 4, "bottom": 4, "left": 8, "right": 8}}},
            "fields": "userEnteredFormat"}},
        {"unmergeCells": {"range": rango(0, 200)}},
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties":
            {"frozenRowCount": 2, "hideGridlines": True}},
            "fields": "gridProperties(frozenRowCount,hideGridlines)"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS",
            "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 290}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS",
            "startIndex": 1, "endIndex": 4}, "properties": {"pixelSize": 150}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS",
            "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 420}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS",
            "startIndex": 0, "endIndex": 200}, "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
        # título
        {"mergeCells": {"range": rango(0, 1, 0, 5), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": rango(1, 2, 0, 5), "mergeType": "MERGE_ALL"}},
        {"repeatCell": {"range": rango(0, 2), "cell": {"userEnteredFormat": {
            "backgroundColor": TINTA, "textFormat": {"bold": True, "fontSize": 15,
            "foregroundColor": BLANCO}, "verticalAlignment": "MIDDLE",
            "padding": {"top": 6, "bottom": 6, "left": 12, "right": 8}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,padding)"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS",
            "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 46}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS",
            "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 32}, "fields": "pixelSize"}},
    ]

    estilos = {
        "seccion":   {"backgroundColor": TINTA, "textFormat": {"bold": True, "fontSize": 12,
                      "foregroundColor": BLANCO}},
        "cabecera":  {"backgroundColor": SUAVE, "textFormat": {"bold": True, "fontSize": 10},
                      "borders": {"bottom": {"style": "SOLID_MEDIUM", "color": TINTA}}},
        "alerta":    {"backgroundColor": {"red": 0.99, "green": 0.91, "blue": 0.89},
                      "textFormat": {"bold": True, "foregroundColor": ALERTA, "fontSize": 10}},
        "bien":      {"backgroundColor": {"red": 0.88, "green": 0.95, "blue": 0.89},
                      "textFormat": {"bold": True, "fontSize": 10}},
        "destacado": {"backgroundColor": CREMA, "textFormat": {"bold": True, "fontSize": 11}},
    }
    marcadas = set()
    for marca, i in formatos:
        marcadas.add(i - 1)
        e = estilos[marca]
        campos = ("userEnteredFormat(backgroundColor,textFormat,borders)"
                  if "borders" in e else "userEnteredFormat(backgroundColor,textFormat)")
        reqs.append({"repeatCell": {"range": rango(i - 1), "cell": {"userEnteredFormat": e},
                                    "fields": campos}})
        if marca == "seccion":
            reqs.append({"mergeCells": {"range": rango(i - 1, i, 0, 5), "mergeType": "MERGE_ALL"}})
            reqs.append({"updateDimensionProperties": {"range": {"sheetId": sid,
                "dimension": "ROWS", "startIndex": i - 1, "endIndex": i},
                "properties": {"pixelSize": 34}, "fields": "pixelSize"}})

    # Las frases sueltas ocupan una sola celda: si no se fusionan, el texto se
    # corta en la columna A y la hoja no hay quien la lea.
    for n, f in enumerate(filas):
        if n in marcadas or len(f) != 1 or not str(f[0]).strip():
            continue
        reqs.append({"mergeCells": {"range": rango(n, n + 1, 0, 5), "mergeType": "MERGE_ALL"}})

    # filas de tabla con texto largo en la última columna: que respiren
    for n, f in enumerate(filas):
        if len(f) >= 5 and len(str(f[-1])) > 90:
            reqs.append({"updateDimensionProperties": {"range": {"sheetId": sid,
                "dimension": "ROWS", "startIndex": n, "endIndex": n + 1},
                "properties": {"pixelSize": 58}, "fields": "pixelSize"}})

    r = sheets("%s:batchUpdate" % SHEET_ID, "POST", {"requests": reqs}, cab)
    if "_error" in r:
        raise SystemExit("Formato ERROR: %s" % r)
    print("«%s» escrita y formateada · %d filas" % (PESTANA, len(filas)))


if __name__ == "__main__":
    escribir()
