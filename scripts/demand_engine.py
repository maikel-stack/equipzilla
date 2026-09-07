#!/usr/bin/env python3
"""EQUIPZILLA · DEMAND ENGINE · CONTROL — sistema de medición.

Construye y refresca el Sheet central del Demand Engine desde las fuentes
vivas: Pipedrive (verdad comercial), Brevo, Smartlead, Google Ads y Search
Console. Pipedrive manda; el Sheet es la capa de análisis, nunca al revés.

Regla que atraviesa todo el fichero: lo que no se puede medir se marca
NO DETERMINADO y se levanta una alerta. No se rellena con estimaciones.

Uso:  python3 scripts/demand_engine.py [--crear]
      --crear  imprime el ID de un Sheet nuevo en vez de escribir en el actual
"""
import collections
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import (brevo, clave, maquina_de_url, pipedrive,  # noqa: E402
                           sheets, smartlead, token_google)

# El Sheet central. Se rellena al crearlo con --crear.
SHEET = os.environ.get("SHEET_DEMAND_ENGINE", "")
CONF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                    "data", "demand_engine.json")

PIPE_TRANSACCIONAL = 6      # donde vive HOY la compraventa, mezclada con alquiler
PIPE_COMPRAVENTA = 16       # el pipeline correcto, creado y VACÍO
ETAPAS_T = {45: "Lead recibido", 33: "Enviar oferta - Validado",
            37: "Oferta enviada", 38: "Oferta aceptada",
            28: "Alquilador asignado", 46: "Entrega de equipo"}
ETAPA_OFERTA = (37, 38, 28, 46)     # de aquí en adelante hay oferta enviada

OBJETIVOS = [("Septiembre", 45, 18, 3, 60000), ("Octubre", 85, 32, 5, 100000),
             ("Noviembre", 105, 38, 8, 160000), ("Diciembre", 115, 40, 9, 180000)]
META_OPS, META_GMV = 25, 500000
CIERRE_OBJ, OFERTA_OBJ = 0.20, 0.40

CAMPOS_CLAVE = {
    "01c76a4a15cddb48bdcd2d86": "First Click Channel",
    "3bd25ecaf00bcbf98a676b16": "Funnel", "fae1b99b60227391b0701e09": "Utm",
    "19b176b9f5d584da36c0cd87": "Gclid", "d0a90608ec6ae27b44b57bac": "precioTrato",
    "5024b9159be1a9a26340928a": "Puntuación", "ebd8ad2c7f5522a5146d21d3": "LeadScoring",
    "8a4171415b4177f4b7b15d0b": "assetType", "98bda3ea4fc70a079f03240b": "Provincia",
    "edd096dfc336cf98fc95fcb1": "Cliente o Alquilador",
    "4a1ea15f14959d4d677962eb": "Sector", "6667853eaf0cb035d184d87d": "profesional"}

ND = "NO DETERMINADO"
alertas = []          # (prioridad, area, texto, accion)


def alerta(prio, area, texto, accion):
    alertas.append((prio, area, texto, accion))


# ── FUENTES ──────────────────────────────────────────────────────────
def deals_compraventa():
    """Todos los tratos de compraventa, con sus campos.

    Hoy viven en el pipeline 6 (Transaccional) mezclados con alquiler y sólo
    se distinguen por el título. El pipeline 16 «Compraventa», que tiene las
    etapas correctas, está vacío: es el hallazgo nº1 de la auditoría.
    """
    fuera, start = [], 0
    while True:
        d = pipedrive("/deals", start=start, limit=500, status="all_not_deleted")
        items = d.get("data") or []
        if not items:
            break
        for x in items:
            if x.get("pipeline_id") == PIPE_COMPRAVENTA:
                fuera.append(x)
            elif (x.get("pipeline_id") == PIPE_TRANSACCIONAL
                  and re.search(r"compra", x.get("title") or "", re.I)):
                fuera.append(x)
        if not d.get("additional_data", {}).get("pagination", {}).get(
                "more_items_in_collection"):
            break
        start += 500
    return fuera


def campanas_brevo():
    d = brevo("/emailCampaigns?type=classic&status=sent&limit=50&sort=desc")
    if "_error" in d:
        alerta("🔴 CRÍTICA", "MARKETING",
               "Brevo no responde (%s): sin datos de reactivación" % d["_error"],
               "Revisar la clave y las IPs autorizadas en Brevo")
        return []
    prefijos = ("Compraventa ·", "Plataformas Elevación ·", "Lanzamiento ·",
                "Contenedores ·")
    fuera = []
    for c in d.get("campaigns", []):
        if not (c.get("name") or "").startswith(prefijos):
            continue          # blasts masivos antiguos: no son comparables
        st = c.get("statistics", {}).get("campaignStats") or []
        env = ent = ab = cl = clt = reb = baja = 0
        for s in st:
            if s.get("listId") == 34:      # copia interna del equipo
                continue
            env += s.get("sent") or 0
            ent += s.get("delivered") or 0
            ab += s.get("uniqueViews") or 0
            cl += s.get("uniqueClicks") or 0
            clt += s.get("clickers") or 0
            reb += (s.get("softBounces") or 0) + (s.get("hardBounces") or 0)
            baja += s.get("unsubscriptions") or 0
        if env:
            fuera.append(dict(nombre=c.get("name", ""), fecha=(c.get("sentDate") or "")[:10],
                              env=env, ent=ent, ab=ab, cl=cl, clt=clt, reb=reb, baja=baja))
    return fuera


def frio_smartlead():
    try:
        cs = smartlead("/campaigns")
        cs = cs if isinstance(cs, list) else cs.get("data", [])
    except Exception as err:
        alerta("🔴 CRÍTICA", "MARKETING", "Smartlead no responde (%s)" % err,
               "Revisar la clave de Smartlead")
        return []
    ent = lambda v: int(v) if str(v).isdigit() else 0
    fuera = []
    for c in cs:
        a = smartlead("/campaigns/%s/analytics" % c["id"])
        if not isinstance(a, dict):
            continue
        fuera.append(dict(nombre=c.get("name", ""), estado=c.get("status"),
                          env=ent(a.get("sent_count")), resp=ent(a.get("reply_count")),
                          cl=ent(a.get("click_count")), reb=ent(a.get("bounce_count")),
                          leads=ent(a.get("campaign_lead_stats", {}).get("total")
                                    if isinstance(a.get("campaign_lead_stats"), dict) else 0)))
    return fuera


def bloque_externo(script, args=()):
    """Ejecuta uno de los scripts que ya miden Ads o SEO y devuelve su salida."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
    try:
        r = subprocess.run([sys.executable, ruta, *args], capture_output=True,
                           text=True, timeout=300,
                           env={**os.environ, "PYTHONPATH": "pylibs"})
        return r.stdout
    except Exception as err:
        return "ERROR: %s" % err


# ── ANÁLISIS ─────────────────────────────────────────────────────────
def embudo(deals):
    """El embudo real, medido sobre los tratos de Pipedrive."""
    e = dict(leads=len(deals), ofertas=0, ganadas=0, perdidas=0, abiertas=0,
             gmv=0.0, con_importe=0)
    for x in deals:
        st = x.get("status")
        if st == "won":
            e["ganadas"] += 1
            e["gmv"] += float(x.get("value") or 0)
        elif st == "lost":
            e["perdidas"] += 1
        else:
            e["abiertas"] += 1
        if x.get("stage_id") in ETAPA_OFERTA or st == "won":
            e["ofertas"] += 1
        if x.get("value"):
            e["con_importe"] += 1
    e["lead_oferta"] = e["ofertas"] / e["leads"] if e["leads"] else 0
    e["oferta_venta"] = e["ganadas"] / e["ofertas"] if e["ofertas"] else 0
    e["lead_venta"] = e["ganadas"] / e["leads"] if e["leads"] else 0
    return e


def por_mes(deals):
    m = collections.defaultdict(lambda: dict(leads=0, ofertas=0, ventas=0, gmv=0.0))
    for x in deals:
        k = (x.get("add_time") or "")[:7]
        if not k:
            continue
        m[k]["leads"] += 1
        if x.get("stage_id") in ETAPA_OFERTA or x.get("status") == "won":
            m[k]["ofertas"] += 1
        if x.get("status") == "won":
            m[(x.get("won_time") or k)[:7]]["ventas"] += 1
            m[(x.get("won_time") or k)[:7]]["gmv"] += float(x.get("value") or 0)
    return m


def por_comercial(deals):
    c = collections.defaultdict(lambda: dict(leads=0, ofertas=0, ventas=0,
                                             gmv=0.0, abiertas=0, sin_actividad=0,
                                             estancadas=0))
    hoy = dt.date.today()
    for x in deals:
        u = x.get("user_id")
        nom = u.get("name") if isinstance(u, dict) else str(u)
        d = c[nom or ND]
        d["leads"] += 1
        if x.get("stage_id") in ETAPA_OFERTA or x.get("status") == "won":
            d["ofertas"] += 1
        if x.get("status") == "won":
            d["ventas"] += 1
            d["gmv"] += float(x.get("value") or 0)
        if x.get("status") == "open":
            d["abiertas"] += 1
            if not x.get("next_activity_date"):
                d["sin_actividad"] += 1
            ult = (x.get("last_activity_date") or x.get("update_time") or "")[:10]
            try:
                if ult and (hoy - dt.date.fromisoformat(ult)).days > 21:
                    d["estancadas"] += 1
            except ValueError:
                pass
    return c


def motivos_perdida(deals):
    m = collections.Counter()
    for x in deals:
        if x.get("status") == "lost":
            m[(x.get("lost_reason") or "(sin motivo)")[:58]] += 1
    return m


def relleno_campos(deals):
    n = len(deals)
    return [(nom, sum(1 for x in deals if x.get(k) not in (None, "", 0)), n)
            for k, nom in CAMPOS_CLAVE.items()]


def atribucion(deals):
    """Canal de cada trato. Hoy no se puede: los campos están vacíos.

    First Click Channel, Utm y Gclid existen en Pipedrive pero están al 0 % en
    compraventa, así que la única atribución honesta es NO DETERMINADO. Se
    deja la función lista para cuando el campo empiece a rellenarse.
    """
    c = collections.Counter()
    for x in deals:
        canal = (x.get("01c76a4a15cddb48bdcd2d86") or x.get("3bd25ecaf00bcbf98a676b16")
                 or "").strip()
        c[canal or ND] += 1
    return c


# ── PESTAÑAS ─────────────────────────────────────────────────────────
def pct(x):
    return "%.1f %%" % (100 * x)


def eur(x):
    return format(int(x), ",d").replace(",", ".") + " €"


def tab_dashboard(deals, camp, frio, ads, seo):
    e = embudo(deals)
    mes_actual = dt.date.today().strftime("%Y-%m")
    m = por_mes(deals)
    obj_mes = dict((n, (l, o, v, g)) for n, l, o, v, g in OBJETIVOS)
    nombre_mes = {"09": "Septiembre", "10": "Octubre", "11": "Noviembre",
                  "12": "Diciembre"}.get(mes_actual[5:7], "")
    f = [["01 · DASHBOARD — EQUIPZILLA DEMAND ENGINE", "", "", "",
          "actualizado " + dt.datetime.now().strftime("%d/%m/%Y %H:%M")],
         ["Pipedrive es la verdad comercial. Este Sheet es la capa de análisis."], [],
         ["OBJETIVO ANUAL", "Real", "Objetivo", "% cumplimiento", "Gap"],
         ["Operaciones", e["ganadas"], META_OPS,
          pct(e["ganadas"] / META_OPS), META_OPS - e["ganadas"]],
         ["GMV", eur(e["gmv"]), eur(META_GMV), pct(e["gmv"] / META_GMV),
          eur(META_GMV - e["gmv"])],
         ["Margen", ND, ND, ND, "No existe campo de margen en Pipedrive"],
         ["Ticket medio", eur(e["gmv"] / e["ganadas"]) if e["ganadas"] else ND,
          "20.000 €", "", ""],
         [],
         ["EMBUDO (histórico completo)", "Real", "Objetivo", "Veredicto"],
         ["Leads", e["leads"], 350, ""],
         ["Ofertas enviadas", e["ofertas"], 128, ""],
         ["Ventas", e["ganadas"], 25, ""],
         ["Conversión lead → oferta", pct(e["lead_oferta"]), "≥ 40 %",
          "OK" if e["lead_oferta"] >= OFERTA_OBJ else "por debajo"],
         ["Conversión oferta → venta", pct(e["oferta_venta"]), "≥ 20 %",
          "OK" if e["oferta_venta"] >= CIERRE_OBJ else "CUELLO DE BOTELLA"],
         ["Conversión lead → venta", pct(e["lead_venta"]), "7 %", ""],
         [],
         ["RITMO MENSUAL", "Leads real/obj", "Ofertas real/obj", "Ventas real/obj",
          "GMV real/obj"]]
    for n, l, o, v, g in OBJETIVOS:
        clave_mes = {"Septiembre": "2026-09", "Octubre": "2026-10",
                     "Noviembre": "2026-11", "Diciembre": "2026-12"}[n]
        r = m.get(clave_mes, dict(leads=0, ofertas=0, ventas=0, gmv=0))
        f.append([n, "%d / %d" % (r["leads"], l), "%d / %d" % (r["ofertas"], o),
                  "%d / %d" % (r["ventas"], v),
                  "%s / %s" % (eur(r["gmv"]), eur(g))])
    f += [["TOTAL", "%d / 350" % e["leads"], "%d / 128" % e["ofertas"],
           "%d / 25" % e["ganadas"], "%s / %s" % (eur(e["gmv"]), eur(META_GMV))], []]
    f += [["CANALES", "Leads", "Oportunidades", "Ofertas", "Ventas", "GMV", "Margen"]]
    for canal, n in atribucion(deals).most_common():
        f.append([canal, n, ND, ND, ND, ND, ND])
    f += [["", "", "", "", "", "", ""],
          ["La atribución por canal NO se puede calcular: los campos First Click "
           "Channel, Utm y Gclid están al 0 % en los tratos de compraventa."], []]
    f += [["ACTIVIDAD DE MARKETING (no es negocio, es señal)", "Volumen", "Resultado"]]
    if camp:
        te = sum(c["ent"] for c in camp)
        ta = sum(c["ab"] for c in camp)
        tc = sum(c["cl"] for c in camp)
        f.append(["Brevo · reactivación", "%d entregados" % te,
                  "%s apertura · %d personas clican" % (pct(ta / te if te else 0), tc)])
    for c in frio:
        f.append(["Smartlead · %s" % c["nombre"][:34], "%d enviados" % c["env"],
                  "%d respuestas (%s)" % (c["resp"], pct(c["resp"] / c["env"] if c["env"] else 0))])
    if ads:
        f.append(["Google Ads", "%s invertidos" % eur(ads["coste"]),
                  "%d conversiones · CPL %s" % (ads["conv"],
                  eur(ads["coste"] / ads["conv"]) if ads["conv"] else ND)])
    if seo:
        f.append(["SEO · Search Console", "%s impresiones" % seo["impr"],
                  "%s clics" % seo["clics"]])
    return f


def tab_funnel(deals):
    m = por_mes(deals)
    e = embudo(deals)
    f = [["02 · FUNNEL"],
         ["Medido sobre Pipedrive. 'Cualificado' y 'Negociación' no existen como "
          "etapa en el pipeline que se usa hoy, así que van como NO DETERMINADO."], [],
         ["Mes", "Leads", "Cualificados", "Oportunidades", "Ofertas", "Negociación",
          "Ventas", "GMV", "Margen"]]
    for k in sorted(m):
        r = m[k]
        f.append([k, r["leads"], ND, r["leads"], r["ofertas"], ND, r["ventas"],
                  eur(r["gmv"]), ND])
    f += [[], ["CONVERSIONES ACUMULADAS", "Real", "Objetivo"],
          ["Lead → Cualificado", ND, "—"],
          ["Cualificado → Oportunidad", ND, "—"],
          ["Lead → Oferta", pct(e["lead_oferta"]), "≥ 40 %"],
          ["Oferta → Venta", pct(e["oferta_venta"]), "≥ 20 %"],
          ["Lead → Venta", pct(e["lead_venta"]), "7 %"],
          [], ["POR ETAPA (tratos abiertos y perdidos)", "Nº"]]
    et = collections.Counter()
    for x in deals:
        et[ETAPAS_T.get(x.get("stage_id"), "etapa %s" % x.get("stage_id"))] += 1
    for k, v in et.most_common():
        f.append([k, v])
    f += [[], ["POR QUÉ SE PIERDEN", "Nº", "%"]]
    mp = motivos_perdida(deals)
    tot = sum(mp.values())
    for k, v in mp.most_common(15):
        f.append([k, v, pct(v / tot) if tot else ""])
    return f


def tab_comercial(deals):
    c = por_comercial(deals)
    f = [["05 · COMERCIAL"],
         ["Responsable del trato en Pipedrive. Ojo: la mayoría siguen asignados a "
          "personas que ya no están activas en el CRM."], [],
         ["Comercial", "Leads", "Ofertas", "Ventas", "GMV", "Abiertas",
          "Sin próxima acción", "Estancadas >21 días"]]
    for nom, d in sorted(c.items(), key=lambda x: -x[1]["leads"]):
        f.append([nom, d["leads"], d["ofertas"], d["ventas"], eur(d["gmv"]),
                  d["abiertas"], d["sin_actividad"], d["estancadas"]])
    f += [[], ["SLA DE PRIMERA RESPUESTA", "Estado"],
          ["Objetivo septiembre", "< 60 minutos"],
          ["Objetivo desde octubre", "< 15 minutos"],
          ["Real medido", ND],
          ["Por qué", "Pipedrive no registra la hora de la primera llamada. Hace "
                      "falta que el equipo registre la actividad al llamar."]]
    return f


def tab_pipeline(deals):
    hoy = dt.date.today()
    f = [["04 · PIPELINE — espejo de Pipedrive"],
         ["Sincronizado desde Pipedrive en cada refresco. NO editar aquí: "
          "Comercial trabaja en Pipedrive, esto es sólo lectura."], [],
         ["ID", "Empresa", "Contacto", "Origen", "ICP", "Categoría", "Presupuesto",
          "Ubicación", "Score", "Estado", "Etapa", "Responsable", "Importe",
          "Margen", "Última actividad", "Próxima acción", "Días abierta",
          "Motivo de pérdida"]]
    for x in sorted(deals, key=lambda d: d.get("status") != "open"):
        org = x.get("org_id")
        per = x.get("person_id")
        u = x.get("user_id")
        try:
            dias = (hoy - dt.date.fromisoformat((x.get("add_time") or "")[:10])).days
        except ValueError:
            dias = ""
        f.append([
            x.get("id"),
            (org.get("name") if isinstance(org, dict) else "") or ND,
            (per.get("name") if isinstance(per, dict) else "") or ND,
            x.get("01c76a4a15cddb48bdcd2d86") or ND,
            ND,                                    # ICP: no existe el campo
            x.get("8a4171415b4177f4b7b15d0b") or ND,
            x.get("8044eea73a8dfc7de631787f") or ND,
            x.get("98bda3ea4fc70a079f03240b") or ND,
            x.get("5024b9159be1a9a26340928a") or ND,
            x.get("status"),
            ETAPAS_T.get(x.get("stage_id"), x.get("stage_id")),
            (u.get("name") if isinstance(u, dict) else "") or ND,
            eur(x.get("value") or 0) if x.get("value") else "0 €",
            ND,
            (x.get("last_activity_date") or "")[:10] or ND,
            (x.get("next_activity_date") or "")[:10] or "SIN PRÓXIMA ACCIÓN",
            dias,
            (x.get("lost_reason") or "") if x.get("status") == "lost" else ""])
    return f


def tab_marketing(camp, frio, ads):
    f = [["07 · MARKETING"], [], ["BREVO · reactivación de nuestra base",
          "", "", "", "", "", "", ""],
         ["Campaña", "Fecha", "Enviados", "Entregados", "Aperturas", "% apertura",
          "Personas que clican", "% clic", "Bajas"]]
    te = ta = tc = tenv = 0
    for c in camp:
        f.append([c["nombre"][:50], c["fecha"], c["env"], c["ent"], c["ab"],
                  pct(c["ab"] / c["ent"] if c["ent"] else 0), c["cl"],
                  pct(c["cl"] / c["ent"] if c["ent"] else 0), c["baja"]])
        tenv += c["env"]; te += c["ent"]; ta += c["ab"]; tc += c["cl"]
    f.append(["TOTAL", "", tenv, te, ta, pct(ta / te if te else 0), tc,
              pct(tc / te if te else 0), ""])
    f += [["Objetivo", "", "", "", "", "≥ 20 % apertura",
           "OK" if te and ta / te >= 0.20 else "por debajo", "", ""],
          ["Leads / oportunidades / ventas atribuidas a Brevo", ND, "", "", "", "", "", "", ""],
          [], ["SMARTLEAD · captación en frío", "", "", "", "", "", ""],
          ["Campaña", "Estado", "Enviados", "Respuestas", "% respuesta", "Clics",
           "Rebotes", "Objetivo septiembre"]]
    for c in frio:
        r = c["resp"] / c["env"] if c["env"] else 0
        f.append([c["nombre"][:50], c["estado"], c["env"], c["resp"], pct(r),
                  c["cl"], c["reb"],
                  "OK" if r >= 0.025 else "POR DEBAJO de 2,5 %"])
    f += [["Respuestas positivas / leads / ofertas / ventas", ND, "", "", "", "", "", ""],
          [], ["GOOGLE ADS", "", "", "", "", "", ""]]
    if ads:
        f += [["Métrica", "Valor"],
              ["Inversión (30 días)", eur(ads["coste"])],
              ["Impresiones", ads["impr"]], ["Clics", ads["clics"]],
              ["CTR", pct(ads["clics"] / ads["impr"]) if ads["impr"] else ND],
              ["CPC medio", "%.2f €" % (ads["coste"] / ads["clics"]) if ads["clics"] else ND],
              ["Conversiones (leads)", ads["conv"]],
              ["CPL", eur(ads["coste"] / ads["conv"]) if ads["conv"] else ND],
              ["Oportunidades / coste por oportunidad", ND],
              ["Ventas / CAC / GMV / margen", ND],
              ["Por qué", "Las conversiones de Ads no se cruzan con Pipedrive: el "
                          "campo Gclid está vacío en el 100 % de los tratos."]]
    else:
        f.append(["Sin datos de Google Ads en este refresco", ""])
    return f


def tab_seo(seo, quickwins):
    f = [["08 · SEO"], [], ["SEARCH CONSOLE · 28 días", "Valor"],
         ["Impresiones", seo.get("impr", ND)], ["Clics", seo.get("clics", ND)],
         ["CTR", seo.get("ctr", ND)], ["Consultas", seo.get("consultas", ND)],
         ["Consultas con intención de compra", seo.get("comerciales", ND)],
         [], ["SEO → LEAD → OFERTA → VENTA", ND],
         ["Por qué", "El formulario web no marca el origen en Pipedrive. Hasta que "
                     "se rellene Utm o First Click Channel, el SEO no se puede medir "
                     "como canal de adquisición, sólo como tráfico."],
         [], ["OPORTUNIDADES · keywords en posición 4-20", "Posición", "Impresiones",
              "Clics", "Intención", "Acción"]]
    for k in quickwins:
        intencion = ("compra" if re.search(r"segunda mano|ocasi[oó]n|comprar|venta|precio",
                                           k[0], re.I)
                     else "alquiler" if re.search(r"alquil", k[0], re.I) else "informativa")
        f.append([k[0], k[1], k[2], k[3], intencion,
                  "Artículo + ficha de producto" if intencion == "compra"
                  else "Revisar: intención de alquiler, no de compra"])
    return f


def tab_auditoria(deals):
    n = len(deals)
    f = [["00 · AUDITORÍA DEL ECOSISTEMA"],
         ["Lo que hay, lo que falta y lo que está mal montado. Sin esto, la mitad "
          "del dashboard no se puede rellenar."], [],
         ["QUÉ TENEMOS", "Estado", "Detalle"],
         ["Pipedrive", "OK", "9 pipelines, 22 usuarios (5 activos)"],
         ["Brevo", "OK", "38.837 contactos, 13 campañas enviadas"],
         ["Smartlead", "OK", "996 leads cargados en la campaña de frío"],
         ["Google Ads", "OK", "2 campañas activas, cuenta 3057448284"],
         ["Search Console", "OK", "sc-domain:equipzilla.com"],
         ["DinoRank", "OK", "clave activa, research de keywords hecho"],
         ["Web / inbound", "PARCIAL", "Los formularios crean tratos, pero sin origen"],
         ["LinkedIn", "NO HAY", "Sin fuente conectada"],
         ["Llamadas / recuperación", "NO HAY", "No se registran actividades de llamada"],
         [], ["QUÉ ESTÁ MAL ESTRUCTURADO", "Impacto"],
         ["El pipeline 16 «Compraventa» existe, con las etapas correctas, y está VACÍO",
          "Toda la compraventa vive en el pipeline 6 mezclada con alquiler y sólo se "
          "distingue por el título del trato"],
         ["Las etapas que se usan son de alquiler («Alquilador asignado»)",
          "No hay etapa de negociación ni de cualificación: el funnel no se puede medir entero"],
         ["Sólo el %d %% de los tratos tiene importe" % (100 * sum(1 for x in deals if x.get("value")) // max(n, 1)),
          "Sin importes no hay GMV ni margen que medir"],
         ["No existe campo de margen", "El objetivo de margen no es medible hoy"],
         ["No existe campo de ICP", "El análisis ICP-A/B/C/D no se puede hacer"],
         [], ["RELLENO DE LOS CAMPOS QUE YA EXISTEN", "Relleno", "Para qué serviría"]]
    para = {"First Click Channel": "Atribución de canal (first touch)",
            "Funnel": "Atribución de canal", "Utm": "Campaña de origen",
            "Gclid": "Cruzar ventas con Google Ads", "precioTrato": "GMV",
            "Puntuación": "Scoring", "LeadScoring": "Scoring",
            "assetType": "Categoría de máquina", "Provincia": "Ubicación",
            "Cliente o Alquilador": "ICP-D (empresas de alquiler)",
            "Sector": "ICP", "profesional": "ICP-A (comprador profesional)"}
    for nom, v, tot in relleno_campos(deals):
        f.append([nom, "%d / %d  (%d %%)" % (v, tot, 100 * v // max(tot, 1)),
                  para.get(nom, "")])
    f += [[], ["QUÉ PUEDE AUTOMATIZARSE YA", "Estado"],
          ["Pipedrive → Sheets", "HECHO (este script)"],
          ["Brevo → Sheets", "HECHO"], ["Smartlead → Sheets", "HECHO"],
          ["Google Ads → Sheets", "HECHO"], ["Search Console → Sheets", "HECHO"],
          ["DinoRank → Sheets", "PENDIENTE"],
          ["Web / inbound → Sheets", "BLOQUEADO: el formulario no marca origen"],
          ["Alta automática de leads del frío en Pipedrive", "HECHO (informe_respuestas)"],
          ["Cola comercial priorizada", "HECHO (cola_comercial)"]]
    return f


def tab_alertas(deals, camp, frio, ads):
    """Máximo 5 críticas. Cada alerta dice qué hacer, no sólo qué pasa."""
    e = embudo(deals)
    c = por_comercial(deals)
    n = len(deals)
    sin_importe = sum(1 for x in deals if x.get("status") == "open" and not x.get("value"))
    sin_accion = sum(d["sin_actividad"] for d in c.values())
    estancadas = sum(d["estancadas"] for d in c.values())
    if e["oferta_venta"] < CIERRE_OBJ:
        alerta("🔴 CRÍTICA", "FUNNEL",
               "Oferta → venta al %s, objetivo ≥ 20 %%. Son %d ofertas perdidas "
               "contra %d ganadas." % (pct(e["oferta_venta"]), e["perdidas"], e["ganadas"]),
               "Autopsia de las últimas 20 ofertas perdidas con David")
    if sin_importe:
        alerta("🔴 CRÍTICA", "NEGOCIO",
               "%d de %d ofertas abiertas sin importe" % (sin_importe, e["abiertas"]),
               "Cargar los importes: sin ellos no hay GMV que medir")
    mp = motivos_perdida(deals)
    sin_motivo = mp.get("OTRAS - General", 0) + mp.get("(sin motivo)", 0)
    if sin_motivo > 0.15 * max(sum(mp.values()), 1):
        alerta("🔴 CRÍTICA", "FUNNEL",
               "%d de %d pérdidas sin motivo real ('OTRAS - General')"
               % (sin_motivo, sum(mp.values())),
               "Quitar 'OTRAS - General' como opción válida en Pipedrive")
    for cf in frio:
        r = cf["resp"] / cf["env"] if cf["env"] else 0
        if r < 0.025:
            alerta("🟠 IMPORTANTE", "MARKETING",
                   "Frío al %s de respuesta, por debajo del 2,5 %% de septiembre" % pct(r),
                   "Auditar la lista antes de gastar los envíos que quedan")
    if sin_accion:
        alerta("🟠 IMPORTANTE", "COMERCIAL",
               "%d oportunidades abiertas sin próxima acción" % sin_accion,
               "Asignar próxima acción a cada oportunidad abierta")
    if estancadas:
        alerta("🟠 IMPORTANTE", "COMERCIAL",
               "%d oportunidades sin actividad en más de 21 días" % estancadas,
               "Aplicar la regla de 5 toques / 21 días")
    if not any(x.get("01c76a4a15cddb48bdcd2d86") for x in deals):
        alerta("🟠 IMPORTANTE", "DATOS",
               "Atribución de canal al 0 %: no sabemos de dónde viene el negocio",
               "Rellenar First Click Channel al crear el trato")
    alerta("🟢 INFORMATIVA", "DATOS",
           "El pipeline 16 «Compraventa» está vacío; se usa el 6 (Transaccional)",
           "Decidir si se migra la compraventa a su pipeline")
    orden = {"🔴 CRÍTICA": 0, "🟠 IMPORTANTE": 1, "🟢 INFORMATIVA": 2}
    alertas.sort(key=lambda a: orden.get(a[0], 3))
    f = [["10 · ALERTAS"],
         ["Máximo 5 críticas. Cada una dice qué hacer, no sólo qué pasa."], [],
         ["Prioridad", "Área", "Qué pasa", "Qué hacer"]]
    for a in alertas[:20]:
        f.append(list(a))
    return f


def tab_action_board():
    f = [["11 · ACTION BOARD"],
         ["Lo que hay que hacer, por urgencia. Rellenar Estado a mano."], [],
         ["Estado", "Acción", "Responsable", "Prioridad", "Por qué",
          "Impacto esperado", "Hecho"]]
    acciones = [
        ("🔥 NOW", "Autopsia de las últimas 20 ofertas perdidas", "Maikel + David",
         "🔴", "El 29 % de las pérdidas no tiene motivo real registrado",
         "Desbloquea el cuello de botella del embudo"),
        ("🔥 NOW", "Cargar los importes de las ofertas abiertas", "David",
         "🔴", "Están a 0 €", "Hace medible el GMV contra los 500.000 €"),
        ("TODAY", "Llamar a los leads HOT de «Cola comercial»", "David",
         "🔴", "Tienen máquina y presupuesto señalados", "Ofertas nuevas esta semana"),
        ("TODAY", "Quitar 'OTRAS - General' de los motivos de pérdida", "Maikel",
         "🟠", "Sin diagnóstico no hay mejora", "Poder arreglar el cierre"),
        ("THIS WEEK", "Rellenar First Click Channel al crear cada trato", "Equipo",
         "🟠", "Atribución al 0 %", "Saber qué canal genera negocio"),
        ("THIS WEEK", "Decidir presupuesto de Shopping (20 → 50 €/día)", "Maikel",
         "🟠", "Pierde el 59,5 % de impresiones por presupuesto",
         "~2,5x volumen al mismo coste por clic"),
        ("THIS WEEK", "Auditar la lista de frío antes de gastar los envíos restantes",
         "Claude", "🟠", "Han clicado centros culturales y un competidor",
         "Dejar de quemar lista"),
        ("BLOCKED", "Publicar los 8 artículos SEO", "Maikel",
         "🟠", "Faltan accesos del hosting; el blog sirve spam a Googlebot",
         "Tráfico de intención de compra"),
        ("BLOCKED", "Medir margen", "Maikel",
         "🟠", "No existe el campo en Pipedrive", "Objetivo de margen medible"),
        ("BLOCKED", "Medir SLA de primera respuesta", "Equipo",
         "🟠", "No se registran las llamadas en Pipedrive",
         "Saber si llegamos tarde a los leads"),
    ]
    for a in acciones:
        f.append(list(a) + [""])
    return f


def tab_learning():
    return [["08 · LEARNING LOG"],
            ["Todo aprendizaje que cambie una decisión se registra aquí."], [],
            ["Fecha", "Observación", "Hipótesis", "Acción", "Resultado", "Decisión"],
            ["07/09/2026",
             "Lead → oferta va al 48 % (mejor que el 37 % previsto) pero "
             "oferta → venta al 2,1 % (previsto 19,5 %)",
             "El cuello de botella no es generar demanda sino cerrarla",
             "Dejar de optimizar captación; autopsia de ofertas perdidas",
             "pendiente", "pendiente"],
            ["07/09/2026",
             "8 'clics' del frío con apertura y clic en el mismo segundo, "
             "de centros culturales y una administración de lotería",
             "Son antivirus de correo, y además la lista está mal segmentada",
             "Filtro escaner() en el clasificador + auditar la lista",
             "Filtro funcionando: bloqueó los 8, dejó pasar los humanos",
             "Auditar los 996 contactos antes de seguir enviando"],
            ["07/09/2026",
             "Shopping pierde el 59,5 % de impresiones por presupuesto a 0,21 €/clic",
             "Hay demanda sin capturar al precio de clic más barato que tenemos",
             "Proponer subir de 20 a 50 €/día", "pendiente", "pendiente"]]


def tab_experimentos():
    return [["09 · EXPERIMENTOS"],
            ["Nunca lanzar un experimento sin escribir antes qué queremos aprender."], [],
            ["Experimento", "Canal", "Hipótesis", "Variable", "KPI", "Antes",
             "Después", "Resultado", "Decisión"],
            ["Seguimiento f2 de los lanzamientos", "Brevo",
             "Un segundo toque con las máquinas en una línea recupera abridores "
             "que no clicaron", "Formato: lista escueta vs ficha completa",
             "Personas que clican", "3 y 2", "pendiente", "🟡 En curso", ""],
            ["Campaña de carretillas a la lista de 288", "Brevo",
             "Carretillas es nuestra mejor categoría (0,88 % de clic y quick win "
             "en Google)", "Categoría", "% clic", "0,52 % media del motor",
             "pendiente", "🟡 En curso", ""],
            ["Subir Shopping a 50 €/día", "Google Ads",
             "Recuperamos el 59,5 % de impresiones perdidas manteniendo el CPC",
             "Presupuesto diario", "Conversiones y CPL", "2 conv · CPL 232 €",
             "pendiente", "🟡 En curso", ""]]


# ── ESCRITURA ────────────────────────────────────────────────────────
TINTA = {"red": 0.09, "green": 0.20, "blue": 0.23}
SUAVE = {"red": 0.93, "green": 0.95, "blue": 0.96}
BLANCO = {"red": 1, "green": 1, "blue": 1}
ROJO = {"red": 0.99, "green": 0.91, "blue": 0.89}


def cabeceras():
    return {"Authorization": "Bearer " + token_google(
        ["https://www.googleapis.com/auth/spreadsheets"]),
        "Content-Type": "application/json"}


def escribir(sid_libro, pestana, filas, cab):
    meta = sheets("%s?fields=sheets.properties" % sid_libro, cab=cab)
    if "_error" in meta:
        raise SystemExit("Sheets ERROR: %s" % meta)
    hojas = {x["properties"]["title"]: x["properties"] for x in meta.get("sheets", [])}
    if pestana not in hojas:
        sheets("%s:batchUpdate" % sid_libro, "POST",
               {"requests": [{"addSheet": {"properties": {"title": pestana}}}]}, cab)
        meta = sheets("%s?fields=sheets.properties" % sid_libro, cab=cab)
        hojas = {x["properties"]["title"]: x["properties"] for x in meta.get("sheets", [])}
    sid = hojas[pestana]["sheetId"]
    ancho = max((len(f) for f in filas), default=1)
    rng = urllib.parse.quote("%s!A1:%s2000" % (pestana, chr(64 + min(ancho + 2, 26))))
    sheets("%s/values/%s:clear" % (sid_libro, rng), "POST", {}, cab)
    r = sheets("%s/values/%s?valueInputOption=RAW"
               % (sid_libro, urllib.parse.quote("%s!A1" % pestana)), "PUT",
               {"values": filas}, cab)
    if "_error" in r:
        raise SystemExit("Sheets ERROR en %s: %s" % (pestana, r))

    def rango(f0, f1=None, c0=0, c1=None):
        return {"sheetId": sid, "startRowIndex": f0, "endRowIndex": f1 or f0 + 1,
                "startColumnIndex": c0, "endColumnIndex": c1 or ancho}

    reqs = [
        {"repeatCell": {"range": rango(0, 2000), "cell": {"userEnteredFormat": {
            "backgroundColor": BLANCO,
            "textFormat": {"bold": False, "fontSize": 10},
            "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP",
            "padding": {"top": 3, "bottom": 3, "left": 8, "right": 8}}},
            "fields": "userEnteredFormat"}},
        {"unmergeCells": {"range": rango(0, 2000)}},
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties":
            {"frozenRowCount": 1, "hideGridlines": True}},
            "fields": "gridProperties(frozenRowCount,hideGridlines)"}},
        {"mergeCells": {"range": rango(0, 1), "mergeType": "MERGE_ALL"}},
        {"repeatCell": {"range": rango(0, 1), "cell": {"userEnteredFormat": {
            "backgroundColor": TINTA, "textFormat": {"bold": True, "fontSize": 14,
            "foregroundColor": BLANCO}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS",
            "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 42},
            "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS",
            "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 260},
            "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS",
            "startIndex": 1, "endIndex": ancho}, "properties": {"pixelSize": 150},
            "fields": "pixelSize"}},
    ]
    # cabeceras de tabla: fila cuya 1ª celda es corta y la 2ª existe
    for n, f in enumerate(filas):
        if n == 0 or len(f) < 3:
            continue
        primera = str(f[0])
        if primera.isupper() and len(primera) > 3:
            reqs.append({"repeatCell": {"range": rango(n), "cell": {"userEnteredFormat": {
                "backgroundColor": SUAVE, "textFormat": {"bold": True}}},
                "fields": "userEnteredFormat(backgroundColor,textFormat)"}})
        if "🔴" in primera or "CUELLO" in " ".join(str(x) for x in f):
            reqs.append({"repeatCell": {"range": rango(n), "cell": {"userEnteredFormat": {
                "backgroundColor": ROJO, "textFormat": {"bold": True}}},
                "fields": "userEnteredFormat(backgroundColor,textFormat)"}})
    sheets("%s:batchUpdate" % sid_libro, "POST", {"requests": reqs}, cab)
    print("   %-28s %d filas" % (pestana, len(filas)))


def metricas_ads():
    """Totales de Google Ads. Se leen de la línea TOTAL de ads_metricas.py."""
    txt = bloque_externo("ads_metricas.py")
    for l in txt.splitlines():
        if not l.startswith("TOTAL"):
            continue
        n = re.findall(r"[\d.]+", l.replace("€", " "))
        try:
            return dict(impr=int(n[0]), clics=int(n[1]), coste=float(n[2]),
                        conv=int(float(n[4])))
        except (IndexError, ValueError):
            break
    alerta("🟠 IMPORTANTE", "MARKETING", "Sin datos de Google Ads en este refresco",
           "Revisar ads_metricas.py y el token de desarrollador")
    return None


def metricas_seo():
    """Totales y quick wins de Search Console, de la salida de gsc_metricas.py."""
    txt = bloque_externo("gsc_metricas.py")
    seo, quick = {}, []
    m = re.search(r"(\d+) clics · (\d+) impresiones · (\d+) consultas", txt)
    if m:
        cl, im, co = int(m.group(1)), int(m.group(2)), int(m.group(3))
        seo = dict(clics=cl, impr=im, consultas=co,
                   ctr="%.2f %%" % (100 * cl / im) if im else ND)
    m = re.search(r"intenci[oó]n de compra[^\d]*(\d+)", txt, re.I)
    if m:
        seo["comerciales"] = int(m.group(1))
    for l in txt.splitlines():
        g = re.match(r"\s*pos\s+([\d.]+)\s+·\s+(\d+) impr\s+·\s+(\d+) clics\s+·\s+(.+)", l)
        if g:
            quick.append((g.group(4).strip(), g.group(1), g.group(2), g.group(3)))
    if not seo:
        alerta("🟠 IMPORTANTE", "SEO", "Sin datos de Search Console en este refresco",
               "Revisar gsc_metricas.py y los permisos de la cuenta de servicio")
    return seo, quick[:20]


def main():
    libro = SHEET
    if not libro and os.path.exists(CONF):
        libro = json.load(open(CONF)).get("sheet_id", "")
    if not libro:
        raise SystemExit(
            "Falta el ID del Sheet central. Ponlo en data/demand_engine.json "
            '{"sheet_id": "..."} o en la variable SHEET_DEMAND_ENGINE.')

    print("Leyendo fuentes...")
    deals = deals_compraventa()
    print("   Pipedrive      %d tratos de compraventa" % len(deals))
    camp = campanas_brevo()
    print("   Brevo          %d campañas" % len(camp))
    frio = frio_smartlead()
    print("   Smartlead      %d campañas" % len(frio))
    ads = metricas_ads()
    print("   Google Ads     %s" % ("OK" if ads else "sin datos"))
    seo, quick = metricas_seo()
    print("   Search Console %s" % ("OK" if seo else "sin datos"))

    cab = cabeceras()
    print("\nEscribiendo pestañas...")
    escribir(libro, "01 · DASHBOARD", tab_dashboard(deals, camp, frio, ads, seo), cab)
    escribir(libro, "02 · FUNNEL", tab_funnel(deals), cab)
    escribir(libro, "04 · PIPELINE", tab_pipeline(deals), cab)
    escribir(libro, "05 · COMERCIAL", tab_comercial(deals), cab)
    escribir(libro, "07 · MARKETING", tab_marketing(camp, frio, ads), cab)
    escribir(libro, "08 · SEO", tab_seo(seo, quick), cab)
    escribir(libro, "09 · LEARNING LOG", tab_learning(), cab)
    escribir(libro, "09b · EXPERIMENTOS", tab_experimentos(), cab)
    escribir(libro, "10 · ALERTAS", tab_alertas(deals, camp, frio, ads), cab)
    escribir(libro, "11 · ACTION BOARD", tab_action_board(), cab)
    escribir(libro, "00 · AUDITORÍA", tab_auditoria(deals), cab)

    e = embudo(deals)
    print("\nRESUMEN")
    print("   ventas %d/%d · GMV %s/%s" % (e["ganadas"], META_OPS, eur(e["gmv"]),
                                           eur(META_GMV)))
    print("   lead→oferta %s · oferta→venta %s" % (pct(e["lead_oferta"]),
                                                   pct(e["oferta_venta"])))
    print("   alertas: %d críticas, %d importantes"
          % (sum(1 for a in alertas if a[0].startswith("🔴")),
             sum(1 for a in alertas if a[0].startswith("🟠"))))
    print("   https://docs.google.com/spreadsheets/d/%s/edit" % libro)


if __name__ == "__main__":
    main()
