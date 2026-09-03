#!/usr/bin/env python3
"""Panel horario: estado en vivo de Brevo, Smartlead y Pipedrive.

Escribe dos pestañas en el Sheet de mando (el mismo de la lista de llamadas):
  · "Panel · en vivo"   — una fila por campaña + bloque de frío y CRM
  · "Clics nuevos"      — quién ha clicado en las campañas recientes, para llamar

NO toca la pestaña manual de llamadas: las columnas LLAMADO y RESULTADO son
del equipo y no se sobrescriben nunca.

Uso:
    python3 scripts/panel_horario.py            # imprime el panel
    python3 scripts/panel_horario.py --sheet    # además lo sube al Sheet

Credenciales: ~/.outbound/{brevo_key,smartlead_key,pipedrive_key} y, para
--sheet, ~/.outbound/google_sa.json (cuenta de servicio con acceso de editor
al Sheet).
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SHEET_ID = "1wyWmrmg_NlxhN0ZW4iIxE8ZG-y-zMBXfY4_agAl54vM"
CRED = os.path.expanduser("~/.outbound/")
NAVEGADOR = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
# Campañas del motor ABM de compraventa: el prefijo las distingue de los
# blasts masivos antiguos, que no son comparables (playbook ABM §métricas).
PREFIJOS = ("Compraventa ·", "Plataformas Elevación ·", "Lanzamiento ·",
            "Contenedores ·")


def clave(nombre):
    p = os.path.join(CRED, nombre)
    return open(p).read().strip() if os.path.exists(p) else ""


def pedir(url, cabeceras, timeout=90):
    req = urllib.request.Request(url, headers=cabeceras)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:200]}


def brevo(ruta):
    return pedir("https://api.brevo.com/v3" + ruta,
                 {"api-key": clave("brevo_key"), "accept": "application/json"})


def smartlead(ruta):
    sep = "&" if "?" in ruta else "?"
    return pedir("https://server.smartlead.ai/api/v1" + ruta + sep +
                 "api_key=" + clave("smartlead_key"),
                 {"accept": "application/json", "user-agent": NAVEGADOR,
                  "referer": "https://app.smartlead.ai/"})


def pipedrive(ruta, **params):
    params["api_token"] = clave("pipedrive_key")
    return pedir("https://api.pipedrive.com/v1" + ruta + "?" +
                 urllib.parse.urlencode(params), {"accept": "application/json"})


def campanas(limite=12):
    """Últimas campañas enviadas del motor ABM, con sus números reales."""
    d = brevo("/emailCampaigns?type=classic&status=sent&limit=50&sort=desc")
    filas = []
    for c in (d.get("campaigns") or []):
        nombre = c.get("name", "")
        if not nombre.startswith(PREFIJOS):
            continue
        st = c.get("statistics") or {}
        # globalStats viene a 0 en campañas multi-lista: hay que sumar por lista.
        env = ent = ab = cl = reb = 0
        for s in st.get("campaignStats") or []:
            env += s.get("sent") or 0
            ent += s.get("delivered") or 0
            ab += s.get("trackableViews") or 0
            cl += s.get("uniqueClicks") or 0
            reb += (s.get("softBounces") or 0) + (s.get("hardBounces") or 0)
        filas.append(dict(id=c.get("id"), nombre=nombre[:52],
                          fecha=(c.get("sentDate") or "")[:16].replace("T", " "),
                          enviados=env, entregados=ent, rebotes=reb,
                          aberturas=ab, clics=cl))
        if len(filas) >= limite:
            break
    return filas


def clickers(cid, tipo="clickers"):
    """Emails que han clicado (o abierto) una campaña, vía export de Brevo."""
    import csv
    import io
    import time
    cab = {"api-key": clave("brevo_key"), "accept": "application/json",
           "content-type": "application/json"}
    req = urllib.request.Request(
        "https://api.brevo.com/v3/emailCampaigns/%s/exportRecipients" % cid,
        data=json.dumps({"recipientsType": tipo}).encode(), headers=cab, method="POST")
    try:
        pid = json.loads(urllib.request.urlopen(req, timeout=60).read()).get("processId")
    except urllib.error.HTTPError:
        return []          # campaña sin destinatarios de ese tipo todavía
    for _ in range(15):
        time.sleep(3)
        pr = pedir("https://api.brevo.com/v3/processes/%s" % pid, cab)
        if pr.get("status") == "completed":
            r = urllib.request.Request(pr["export_url"], headers={"user-agent": NAVEGADOR})
            with urllib.request.urlopen(r, timeout=90) as f:
                texto = f.read().decode("utf-8", "replace")
            return [fila for fila in csv.DictReader(io.StringIO(texto), delimiter=";")]
    return []


def maquina_de_url(url):
    """El export trae una columna por enlace: de ahí sale qué máquina miró."""
    u = urllib.parse.unquote(url)
    for marca in ("interesado en la ", "interesa la "):
        if marca in u:
            return u.split(marca, 1)[1].strip()
    if "wa.me" in u:
        return "WhatsApp"
    if "equipzilla.com" in u:
        return "web"
    return ""


def cola_llamadas(campanas_recientes):
    """Quién ha clicado en las campañas recientes: la cola de llamadas del día.

    Va en su propia pestaña: la lista manual del equipo (con las columnas
    LLAMADO y RESULTADO) no se toca nunca.
    """
    filas = [["COLA DE LLAMADAS · clics en las campañas recientes"],
             ["Generado automáticamente cada hora. La lista manual de llamadas NO se toca."],
             [],
             ["Email", "Clics", "Aperturas", "Qué miró", "Campaña", "Enviada"]]
    vistos = {}
    for cid, nombre, fecha in campanas_recientes:
        for r in clickers(cid):
            em = (r.get("Email_ID") or "").strip().lower()
            if not em:
                continue
            miro = [maquina_de_url(k) for k, v in r.items()
                    if k.startswith("http") and (v or "").strip()]
            miro = " · ".join(x for x in dict.fromkeys(miro) if x)
            try:
                clics = int(r.get("Clicked_Links_Count") or 0)
            except ValueError:
                clics = 0
            if em in vistos:                      # mismo contacto en varias campañas
                vistos[em][1] += clics
                continue
            vistos[em] = [em, clics, ent(r.get("Total Opens")), miro, nombre, fecha]
    for v in sorted(vistos.values(), key=lambda x: -x[1]):
        filas.append(v)
    if len(filas) == 4:
        filas.append(["(todavía sin clics en estas campañas)"])
    return filas


def ent(v):
    """Smartlead devuelve los contadores como texto; Brevo como número."""
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def frio():
    c = smartlead("/campaigns")
    filas = []
    for x in (c if isinstance(c, list) else [])[:6]:
        a = smartlead("/campaigns/%s/analytics" % x.get("id"))
        st = a.get("campaign_lead_stats") or {}
        filas.append(dict(nombre=x.get("name", "")[:52], estado=x.get("status", "?"),
                          enviados=ent(a.get("sent_count")),
                          respuestas=ent(a.get("reply_count")),
                          clics=ent(a.get("click_count")),
                          rebotes=ent(a.get("bounce_count")),
                          leads=ent(st.get("total"))))
    return filas


def crm():
    """Estado real del funnel de COMPRAVENTA.

    El pipeline 6 mezcla alquiler y compraventa (el alquiler es ~95% del
    volumen), así que se filtra por título: sólo cuentan los tratos de compra.
    """
    import re
    compra = re.compile(r"compra", re.I)
    todos, start = [], 0
    while True:
        d = pipedrive("/deals", start=start, limit=500, status="all_not_deleted")
        datos = d.get("data") or []
        todos += [x for x in datos if x.get("pipeline_id") == 6]
        if not (d.get("additional_data", {}).get("pagination", {})
                .get("more_items_in_collection")):
            break
        start += 500
    et = {s["id"]: s["name"] for s in (pipedrive("/stages", pipeline_id=6).get("data") or [])}
    cv = [x for x in todos if compra.search(x.get("title") or "")]
    ab = [x for x in cv if x["status"] == "open"]
    mes = dt.date.today().strftime("%Y-%m")
    filas = [["Ofertas vivas (abiertas)", len(ab)],
             ["Nuevas este mes", len([x for x in cv if (x.get("add_time") or "").startswith(mes)])],
             ["Ganadas este mes", len([x for x in cv if (x.get("won_time") or "").startswith(mes)])],
             ["Leads nuevos 24 h (todo el pipeline)", leads_24h()],
             [], ["Abiertas por etapa", ""]]
    import collections
    for e, n in collections.Counter(et.get(x["stage_id"], "?") for x in ab).items():
        filas.append([e, n])
    return filas


def leads_24h():
    desde = (dt.datetime.utcnow() - dt.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    d = pipedrive("/deals", start=0, limit=100, status="all_not_deleted",
                  sort="add_time DESC")
    n = 0
    for x in (d.get("data") or []):
        if (x.get("add_time") or "") >= desde:
            n += 1
    return n


def construir():
    ahora = dt.datetime.now(dt.timezone(dt.timedelta(hours=2)))
    filas = [["PANEL EN VIVO · Equipzilla compraventa",
              "actualizado " + ahora.strftime("%d/%m/%Y %H:%M") + " (Madrid)"],
             [], ["CAMPAÑAS BREVO (motor ABM)"],
             ["Campaña", "Enviada", "Enviados", "Entregados", "Rebotes",
              "Aperturas", "Clics", "% apertura", "% clic"]]
    tot = dict(enviados=0, entregados=0, aberturas=0, clics=0)
    for c in campanas():
        pa = round(100 * c["aberturas"] / c["entregados"], 1) if c["entregados"] else ""
        pc = round(100 * c["clics"] / c["entregados"], 1) if c["entregados"] else ""
        filas.append([c["nombre"], c["fecha"], c["enviados"], c["entregados"],
                      c["rebotes"], c["aberturas"], c["clics"], pa, pc])
        for k in tot:
            tot[k] += c[k]
    filas.append(["TOTAL", "", tot["enviados"], tot["entregados"], "",
                  tot["aberturas"], tot["clics"],
                  round(100 * tot["aberturas"] / tot["entregados"], 1) if tot["entregados"] else "",
                  round(100 * tot["clics"] / tot["entregados"], 1) if tot["entregados"] else ""])
    filas += [[], ["FRÍO (Smartlead)"],
              ["Campaña", "Estado", "Enviados", "Respuestas", "Clics", "Rebotes",
               "Leads cargados", "% respuesta"]]
    for f in frio():
        pr = round(100 * f["respuestas"] / f["enviados"], 2) if f["enviados"] else ""
        filas.append([f["nombre"], f["estado"], f["enviados"], f["respuestas"],
                      f["clics"], f["rebotes"], f["leads"], pr])
    filas += [[], ["GOOGLE ADS (últimos 30 días)"],
              ["Campaña", "Estado", "Impresiones", "Clics", "Coste", "CPC", "Conversiones", "CPA"]]
    try:
        import ads_metricas
        for a in ads_metricas.campanas(30):
            filas.append([a["nombre"], a["estado"], a["impresiones"], a["clics"],
                          a["coste"], a["cpc"], a["conversiones"], a["cpa"]])
    except Exception as e:
        filas.append(["Google Ads no responde: %s" % str(e)[:120]])
    filas += [[], ["SEO (Search Console · 28 días)"]]
    try:
        import gsc_metricas
        tot, quick, com, _ = gsc_metricas.resumen(28)
        filas += [["Clics", tot["clics"], "Impresiones", tot["impresiones"],
                   "Consultas", tot["consultas"]],
                  ["Consultas con intención de compra", len(com)],
                  [], ["Quick wins (posición 4-20)", "Posición", "Impresiones", "Clics"]]
        for r in quick[:12]:
            filas.append([r["keys"][0], round(r["position"], 1),
                          r["impressions"], r["clicks"]])
    except Exception as e:
        filas.append(["Search Console no responde: %s" % str(e)[:120]])
    filas += [[], ["CRM (Pipedrive · compraventa)"]] + crm()
    return filas


def token_google(scopes):
    """Token de la cuenta de servicio firmando el JWT con openssl.

    La librería `cryptography` está rota en este contenedor (falla el binding
    nativo), así que se firma con openssl, que siempre está disponible.
    """
    import base64
    import subprocess
    import tempfile
    import time
    sa = json.load(open(os.path.join(CRED, "google_sa.json")))
    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=")
    ahora = int(time.time())
    cabecera = {"alg": "RS256", "typ": "JWT"}
    cuerpo = {"iss": sa["client_email"], "scope": " ".join(scopes),
              "aud": sa["token_uri"], "iat": ahora, "exp": ahora + 3600}
    firmable = b64(json.dumps(cabecera).encode()) + b"." + b64(json.dumps(cuerpo).encode())
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as f:
        f.write(sa["private_key"])
        pem = f.name
    try:
        r = subprocess.run(["openssl", "dgst", "-sha256", "-sign", pem],
                           input=firmable, capture_output=True)
    finally:
        os.unlink(pem)
    if r.returncode != 0:
        raise RuntimeError("openssl: " + r.stderr.decode()[:200])
    jwt = firmable + b"." + b64(r.stdout)
    datos = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt.decode()}).encode()
    req = urllib.request.Request(sa["token_uri"], data=datos)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())["access_token"]


def sheets(ruta, metodo="GET", cuerpo=None, cab=None):
    req = urllib.request.Request(
        "https://sheets.googleapis.com/v4/spreadsheets/" + ruta, method=metodo,
        data=json.dumps(cuerpo).encode() if cuerpo is not None else None, headers=cab)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:300]}


def subir(filas, pestana="Panel · en vivo"):
    """Escribe la pestaña del panel. No toca la lista de llamadas del equipo."""
    if not os.path.exists(os.path.join(CRED, "google_sa.json")):
        print("\n[sin subir: falta ~/.outbound/google_sa.json]")
        return
    tk = token_google(["https://www.googleapis.com/auth/spreadsheets"])
    cab = {"Authorization": "Bearer " + tk, "Content-Type": "application/json"}

    meta = sheets("%s?fields=sheets.properties" % SHEET_ID, cab=cab)
    if "_error" in meta:
        print("\n[Sheets ERROR]", meta)
        return
    titulos = [x["properties"]["title"] for x in meta.get("sheets", [])]
    if pestana not in titulos:
        sheets("%s:batchUpdate" % SHEET_ID, "POST",
               {"requests": [{"addSheet": {"properties": {"title": pestana}}}]}, cab)

    rng = urllib.parse.quote("%s!A1:Z300" % pestana)
    sheets("%s/values/%s:clear" % (SHEET_ID, rng), "POST", {}, cab)
    r = sheets("%s/values/%s?valueInputOption=RAW"
               % (SHEET_ID, urllib.parse.quote("%s!A1" % pestana)), "PUT",
               {"values": filas}, cab)
    print("\nPanel subido a «%s»: %s" % (pestana, "OK" if "_error" not in r else r))


if __name__ == "__main__":
    filas = construir()
    for f in filas:
        print(" | ".join(str(x) for x in f))
    if "--sheet" in sys.argv:
        subir(filas)
        # cola de llamadas con los clickers de las campañas de los últimos días
        recientes = [(c["id"], c["nombre"], c["fecha"]) for c in campanas(4)]
        subir(cola_llamadas(recientes), "Clics nuevos · auto")
