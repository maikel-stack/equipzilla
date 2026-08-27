#!/usr/bin/env python3
"""Parte diario del sistema de captación — estado en una pantalla.

Responde cada mañana a "¿cómo vamos?": qué se ha movido en las últimas 24 h,
qué números llevamos y qué está esperando una decisión.

No envía nada por su cuenta: imprime un informe en Markdown por stdout para
que lo lea quien lo ejecute (persona o agente). Guarda una foto del día en
scripts/state_update_diario.json para poder mostrar variaciones al día siguiente.

Env: BREVO_API_KEY (imprescindible), PIPEDRIVE_TOKEN, SMARTLEAD_API_KEY.
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BREVO_KEY = os.environ.get("BREVO_API_KEY", "")
PD_TOKEN = os.environ.get("PIPEDRIVE_TOKEN", "")
SL_KEY = os.environ.get("SMARTLEAD_API_KEY", "")

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(AQUI, "state_update_diario.json")

# Pipeline "Transaccional" → etapa "Lead - Recibido": donde caen los leads del
# quiz, el chatbot, la calculadora y la tasación.
PIPELINE_ID = 6

# Las campañas del motor ABM se nombran siempre con uno de estos prefijos.
# Clasificar por prefijo y no por palabras sueltas evita que un blast masivo
# antiguo ("Nuevo stock Kubota", 22.396 envíos) se cuele en la media y la
# falsee.
PREFIJOS_ABM = ("compraventa ·", "plataformas elevación ·")


def pedir(url, cabeceras, cuerpo=None, metodo="GET"):
    req = urllib.request.Request(
        url, method=metodo, headers=cabeceras,
        data=json.dumps(cuerpo).encode() if cuerpo else None)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def brevo(ruta):
    return pedir("https://api.brevo.com/v3" + ruta,
                 {"api-key": BREVO_KEY, "accept": "application/json"})


def pipedrive(ruta, **params):
    params["api_token"] = PD_TOKEN
    url = "https://api.pipedrive.com/v1" + ruta + "?" + urllib.parse.urlencode(params)
    return pedir(url, {"accept": "application/json"})


def smartlead(ruta):
    sep = "&" if "?" in ruta else "?"
    return pedir("https://server.smartlead.ai/api/v1" + ruta + sep + "api_key=" + SL_KEY,
                 {"accept": "application/json"})


def es_abm(nombre):
    return (nombre or "").lower().startswith(PREFIJOS_ABM)


def campanas():
    """Campañas enviadas con sus totales. campaignStats por lista, porque
    globalStats devuelve 0 por un bug de la API."""
    datos = brevo("/emailCampaigns?limit=50&sort=desc")
    filas, borradores = [], []
    for c in datos.get("campaigns", []):
        if c.get("status") in ("draft", "suspended"):
            # Sólo los borradores del motor ABM: la cuenta arrastra restos
            # antiguos ("dsadsad", copias de newsletters) que son ruido.
            if es_abm(c.get("name")):
                borradores.append((c["id"], c["status"], c.get("name", "")))
            continue
        # "rejected" son envíos que Brevo abortó: contabilizan destinatarios
        # pero no llegaron a nadie. Sólo cuenta lo realmente enviado.
        if c.get("status") != "sent":
            continue
        st = c.get("statistics", {}).get("campaignStats", [])
        t = dict(enviados=0, entregados=0, aperturas=0, clics=0, bajas=0, rebotes=0)
        for s in st:
            t["enviados"] += s.get("sent", 0)
            t["entregados"] += s.get("delivered", 0)
            # trackableViews excluye la inflación de Apple Mail Privacy.
            t["aperturas"] += s.get("trackableViews", 0)
            t["clics"] += s.get("uniqueClicks", 0)
            t["bajas"] += s.get("unsubscriptions", 0)
            t["rebotes"] += s.get("hardBounces", 0) + s.get("softBounces", 0)
        if not t["enviados"]:
            continue
        filas.append(dict(id=c["id"], nombre=c.get("name", ""),
                          fecha=(c.get("sentDate") or "")[:16],
                          abm=es_abm(c.get("name")), **t))
    filas.sort(key=lambda r: r["fecha"], reverse=True)
    return filas, borradores


def leads_recientes(horas=24):
    """Deals creados en el pipeline transaccional en las últimas N horas."""
    desde = dt.datetime.utcnow() - dt.timedelta(hours=horas)
    salida, inicio = [], 0
    while True:
        r = pipedrive("/deals", filter_id="", status="all_not_deleted",
                      start=inicio, limit=100, sort="add_time DESC")
        lote = r.get("data") or []
        if not lote:
            break
        parar = False
        for d in lote:
            if d.get("pipeline_id") != PIPELINE_ID:
                continue
            add = (d.get("add_time") or "")[:19]
            if not add:
                continue
            cuando = dt.datetime.strptime(add, "%Y-%m-%d %H:%M:%S")
            if cuando < desde:
                parar = True
                break
            salida.append(dict(titulo=d.get("title", ""), cuando=add,
                               persona=(d.get("person_id") or {}).get("name", "")))
        if parar or not r.get("additional_data", {}).get("pagination", {}).get("more_items_in_collection"):
            break
        inicio += 100
    return salida


def pct(parte, total):
    return (parte / total * 100) if total else 0.0


def bloque_delta(actual, previo, clave, sufijo=""):
    if not previo or clave not in previo:
        return ""
    d = actual - previo[clave]
    if d == 0:
        return ""
    return f" ({'+' if d > 0 else ''}{d:g}{sufijo} desde ayer)"


def main():
    hoy = dt.date.today()
    lineas = [f"# Parte diario · sistema de captación Equipzilla",
              f"_{hoy.strftime('%d/%m/%Y')}_", ""]

    if not BREVO_KEY:
        print("\n".join(lineas + [
            "**BLOQUEADO** — falta `BREVO_API_KEY`. Sin ella no hay métricas de "
            "email ni se pueden crear campañas.", ""]))
        return 1

    previo = {}
    if os.path.exists(ESTADO):
        try:
            previo = json.load(open(ESTADO))
        except Exception:
            previo = {}

    filas, borradores = campanas()
    cv = [f for f in filas if f["abm"]]
    tot = {k: sum(f[k] for f in cv) for k in
           ("enviados", "entregados", "aperturas", "clics", "bajas", "rebotes")}
    ap = pct(tot["aperturas"], tot["entregados"])
    cl = pct(tot["clics"], tot["entregados"])

    lineas += ["## Números acumulados (motor ABM compraventa)", ""]
    lineas += [
        f"- **{tot['enviados']:,}** enviados"
        f"{bloque_delta(tot['enviados'], previo, 'enviados')}".replace(",", "."),
        f"- **{tot['aperturas']:,}** aperturas · **{ap:.1f}%**"
        f"{bloque_delta(tot['aperturas'], previo, 'aperturas')}".replace(",", "."),
        f"- **{tot['clics']}** clics · **{cl:.2f}%**"
        f"{bloque_delta(tot['clics'], previo, 'clics')}",
        f"- {tot['bajas']} bajas · {tot['rebotes']} rebotes",
        f"- {len(cv)} campañas enviadas", "",
    ]

    lineas += ["## Últimos envíos", "",
               "| # | Fecha | Enviados | Aperturas | Clics | Campaña |",
               "|---|---|---:|---:|---:|---|"]
    for f in cv[:6]:
        lineas.append(
            f"| {f['id']} | {f['fecha'][:10]} | {f['enviados']} | "
            f"{f['aperturas']} ({pct(f['aperturas'], f['entregados']):.1f}%) | "
            f"{f['clics']} ({pct(f['clics'], f['entregados']):.2f}%) | {f['nombre'][:44]} |")
    lineas.append("")

    if borradores:
        lineas += ["## Esperando decisión", ""]
        for cid, estado, nombre in borradores:
            lineas.append(f"- **#{cid}** [{estado}] {nombre}")
        lineas.append("")

    if PD_TOKEN:
        try:
            nuevos = leads_recientes(24)
            lineas += ["## Leads entrados en 24 h", ""]
            if nuevos:
                for n in nuevos:
                    quien = f" — {n['persona']}" if n["persona"] else ""
                    lineas.append(f"- {n['cuando'][11:16]} · {n['titulo']}{quien}")
            else:
                lineas.append("- Ninguno. El embudo web no ha traído leads hoy.")
            lineas.append("")
        except Exception as e:
            lineas += [f"_Pipedrive no responde: {e}_", ""]

    if SL_KEY:
        try:
            camps = smartlead("/campaigns")
            activas = [c for c in camps if c.get("status") == "ACTIVE"]
            lineas += ["## Frío (Smartlead)", ""]
            for c in activas[:5]:
                a = smartlead(f"/campaigns/{c['id']}/analytics")
                lineas.append(
                    f"- {c.get('name', '')[:40]}: {a.get('sent_count', 0)} enviados · "
                    f"{a.get('open_count', 0)} aperturas · {a.get('reply_count', 0)} respuestas")
            if not activas:
                lineas.append("- Sin campañas activas.")
            lineas.append("")
        except Exception as e:
            lineas += [f"_Smartlead no responde: {e}_", ""]

    print("\n".join(lineas))

    foto = dict(fecha=hoy.isoformat(), **tot)
    try:
        json.dump(foto, open(ESTADO, "w"), indent=1)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
