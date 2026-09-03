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
--sheet, ~/.outbound/google_oauth.json (client_id/secret/refresh_token con
scope spreadsheets).
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
    filas += [[], ["CRM (Pipedrive)"], ["Leads nuevos en 24 h", leads_24h()]]
    return filas


def subir(filas):
    """Escribe la pestaña 'Panel · en vivo'. Requiere OAuth con scope sheets."""
    cfg = os.path.join(CRED, "google_oauth.json")
    if not os.path.exists(cfg):
        print("\n[sin subir: falta ~/.outbound/google_oauth.json con el refresh token]")
        return
    c = json.load(open(cfg))
    datos = urllib.parse.urlencode({
        "client_id": c["client_id"], "client_secret": c["client_secret"],
        "refresh_token": c["refresh_token"], "grant_type": "refresh_token"}).encode()
    tok = json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=datos), timeout=60).read())["access_token"]
    cab = {"Authorization": "Bearer " + tok, "Content-Type": "application/json"}

    # crea la pestaña si no existe
    meta = pedir("https://sheets.googleapis.com/v4/spreadsheets/%s?fields=sheets.properties"
                 % SHEET_ID, cab)
    titulos = [s["properties"]["title"] for s in meta.get("sheets", [])]
    if "Panel · en vivo" not in titulos:
        req = urllib.request.Request(
            "https://sheets.googleapis.com/v4/spreadsheets/%s:batchUpdate" % SHEET_ID,
            data=json.dumps({"requests": [{"addSheet": {"properties": {
                "title": "Panel · en vivo"}}}]}).encode(), headers=cab, method="POST")
        urllib.request.urlopen(req, timeout=60)

    rng = urllib.parse.quote("Panel · en vivo!A1:Z200")
    req = urllib.request.Request(
        "https://sheets.googleapis.com/v4/spreadsheets/%s/values/%s:clear" % (SHEET_ID, rng),
        data=b"{}", headers=cab, method="POST")
    urllib.request.urlopen(req, timeout=60)
    req = urllib.request.Request(
        "https://sheets.googleapis.com/v4/spreadsheets/%s/values/%s?valueInputOption=RAW"
        % (SHEET_ID, urllib.parse.quote("Panel · en vivo!A1")),
        data=json.dumps({"values": filas}).encode(), headers=cab, method="PUT")
    urllib.request.urlopen(req, timeout=60)
    print("\nPanel subido al Sheet.")


if __name__ == "__main__":
    filas = construir()
    for f in filas:
        print(" | ".join(str(x) for x in f))
    if "--sheet" in sys.argv:
        subir(filas)
