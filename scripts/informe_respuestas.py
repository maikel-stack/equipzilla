#!/usr/bin/env python3
"""Informe diario de respuestas y leads calientes (8:00).

Recoge las últimas 24-48 h de señales de compra:
  - respuestas y clics de la campaña de frío (Smartlead);
  - clics de las campañas a la base propia (Brevo, por export de destinatarios);
puntúa cada contacto (lead scoring), lo crea como prospecto en Pipedrive
(pipeline Transaccional → «Lead - Recibido», sin duplicar) y deja un CSV
listo para volcarlo a Google Sheets.

Uso:
    python3 scripts/informe_respuestas.py            # recoger + puntuar + CRM + CSV
    python3 scripts/informe_respuestas.py enviar [url_sheet]   # además, email al equipo
    PRUEBA=1 ...                                     # no toca CRM ni envía

Env: claves en ~/.outbound/ (brevo_key, smartlead_key, pipedrive_key).

Scoring (documentado para que nadie discuta el número):
  +50 respondió al frío (la señal más fuerte; el texto se lee en el buzón)
  +40 clicó una máquina concreta en una campaña
  +10 por cada clic adicional
  +20 ya tenía historial en Pipedrive
  +10 tenemos su teléfono
  HOT ≥ 60 (llamar hoy) · WARM 30-59 (seguimiento) · <30 no sale en el informe
"""
import csv
import datetime as dt
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA_CSV = os.path.join(RAIZ, "leads", "respuestas_hoy.csv")
DESTINATARIOS = ["david@equipzilla.com", "maikel@equipzilla.com",
                 "hector@equipzilla.com", "andres@equipzilla.com"]
VENTANA_H = int(os.environ.get("VENTANA_H", "24"))
PRUEBA = os.environ.get("PRUEBA") == "1"
CAMPANA_FRIO = 3789100
PIPELINE, ETAPA = 6, 45

NAVEGADOR = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")


def clave(nombre):
    return open(os.path.expanduser(f"~/.outbound/{nombre}")).read().strip()


def pedir(url, cab, metodo="GET", cuerpo=None, timeout=90):
    req = urllib.request.Request(url, method=metodo, headers=cab,
        data=json.dumps(cuerpo).encode() if cuerpo else None)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
        return json.loads(b) if b.strip().startswith((b"{", b"[")) else b


def brevo(ruta, metodo="GET", cuerpo=None):
    return pedir("https://api.brevo.com/v3" + ruta,
                 {"api-key": clave("brevo_key"), "accept": "application/json",
                  "content-type": "application/json"}, metodo, cuerpo)


def smartlead(ruta):
    sep = "&" if "?" in ruta else "?"
    return pedir("https://server.smartlead.ai/api/v1" + ruta + sep +
                 "api_key=" + clave("smartlead_key"),
                 {"accept": "application/json", "user-agent": NAVEGADOR,
                  "referer": "https://app.smartlead.ai/"})


def pipedrive(ruta, metodo="GET", **params):
    cuerpo = params.pop("_cuerpo", None)
    params["api_token"] = clave("pipedrive_key")
    q = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    return pedir(f"https://api.pipedrive.com/v1{ruta}?{q}",
                 {"accept": "application/json", "content-type": "application/json"},
                 metodo, cuerpo)


import urllib.parse  # noqa: E402  (después de definirse pipedrive por claridad)


def desde():
    return dt.datetime.utcnow() - dt.timedelta(hours=VENTANA_H)


def senales_frio():
    """Respuestas y clics del frío en la ventana."""
    filas, offset = [], 0
    while True:
        st = smartlead(f"/campaigns/{CAMPANA_FRIO}/statistics"
                       f"?offset={offset}&limit=1000")
        lote = st.get("data", []) if isinstance(st, dict) else []
        filas.extend(lote)
        if len(lote) < 1000:
            break
        offset += 1000
    corte = desde()
    salida = {}
    for f in filas:
        email = (f.get("lead_email") or "").lower()
        if not email:
            continue
        for campo, tipo in (("reply_time", "respuesta_frio"), ("click_time", "clic_frio")):
            v = f.get(campo)
            if not v:
                continue
            try:
                cuando = dt.datetime.strptime(v[:19], "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                continue
            if cuando >= corte:
                e = salida.setdefault(email, dict(
                    email=email, nombre=f.get("lead_name") or "",
                    empresa=f.get("lead_company_name") or "", senales=[]))
                e["senales"].append(tipo)
    return salida


def senales_brevo():
    """Clics de campañas recientes vía export de destinatarios (el
    globalStats de la API devuelve 0 por un bug conocido)."""
    corte = desde()
    camps = brevo("/emailCampaigns?limit=15&sort=desc").get("campaigns", [])
    recientes = [c for c in camps if c.get("status") == "sent" and
                 (c.get("sentDate") or "") >= (dt.datetime.utcnow() -
                  dt.timedelta(days=10)).strftime("%Y-%m-%d")]
    salida = {}
    for c in recientes[:8]:
        try:
            proc = brevo(f"/emailCampaigns/{c['id']}/exportRecipients", "POST",
                         {"recipientsType": "clickers"})
            pid = proc.get("processId")
            url_exp = None
            for _ in range(30):
                time.sleep(4)
                p = brevo(f"/processes/{pid}")
                if p.get("status") == "completed":
                    url_exp = p.get("export_url")
                    break
            if not url_exp:
                continue
            bruto = pedir(url_exp, {"user-agent": NAVEGADOR})
            texto = bruto.decode("utf-8", "replace") if isinstance(bruto, bytes) else str(bruto)
            lector = csv.DictReader(io.StringIO(texto), delimiter=";")
            for fila in lector:
                email = (fila.get("EMAIL") or fila.get("email") or "").lower()
                if not email:
                    continue
                maquinas, clics = set(), 0
                for k, v in fila.items():
                    if not v or "http" not in str(v):
                        continue
                    m = re.search(r"interesa(?:d[oa] en)? la\s+([^&\"?]+)",
                                  urllib.parse.unquote(str(v)))
                    if m:
                        maquinas.add(m.group(1).strip()[:40])
                    clics += 1
                if not clics:
                    continue
                e = salida.setdefault(email, dict(
                    email=email, nombre=(fila.get("NOMBRE") or "")[:60],
                    empresa="", senales=[], maquinas=set(), campanas=set()))
                e["senales"].extend(["clic_campana"] * min(clics, 3))
                e["maquinas"] |= maquinas
                e["campanas"].add(c.get("name", "")[:40])
        except Exception as err:
            print(f"  aviso: campaña {c.get('id')} sin export ({err})")
    return salida


def enriquecer(lead):
    """Busca la persona en Pipedrive; devuelve (person_id, telefono, historial)."""
    try:
        r = pipedrive("/persons/search", term=lead["email"],
                      fields="email", exact_match="true")
        items = (r.get("data") or {}).get("items") or []
        if not items:
            return None, "", False
        p = items[0]["item"]
        tel = ""
        det = pipedrive(f"/persons/{p['id']}")
        d = det.get("data") or {}
        tels = [x.get("value") for x in (d.get("phone") or []) if x.get("value")]
        if tels:
            tel = tels[0]
        if not lead.get("nombre"):
            lead["nombre"] = d.get("name", "")
        if not lead.get("empresa"):
            lead["empresa"] = (d.get("org_id") or {}).get("name", "") if isinstance(d.get("org_id"), dict) else ""
        return p["id"], tel, True
    except Exception:
        return None, "", False


def puntuar(lead, tiene_tel, historial):
    s = 0
    s += 50 * min(lead["senales"].count("respuesta_frio"), 1)
    if "clic_campana" in lead["senales"] or "clic_frio" in lead["senales"]:
        s += 40
        extra = lead["senales"].count("clic_campana") + lead["senales"].count("clic_frio") - 1
        s += 10 * max(0, min(extra, 3))
    if historial:
        s += 20
    if tiene_tel:
        s += 10
    return min(s, 100)


def a_pipedrive(lead, person_id):
    """Crea persona si falta y deal de prospecto si no hay uno abierto reciente."""
    if PRUEBA:
        return "prueba"
    if not person_id:
        nombre = (lead.get("nombre") or "").strip() or lead["email"]
        r = pipedrive("/persons", "POST", _cuerpo={
            "name": nombre,
            "email": [{"value": lead["email"], "primary": True}]})
        person_id = (r.get("data") or {}).get("id")
    if not person_id:
        return "sin_persona"
    abiertos = pipedrive(f"/persons/{person_id}/deals", status="open").get("data") or []
    corte = (dt.datetime.utcnow() - dt.timedelta(days=30)).strftime("%Y-%m-%d")
    for d in abiertos:
        if d.get("pipeline_id") == PIPELINE and (d.get("add_time") or "") >= corte:
            return "ya_existia"
    detalle = " · ".join(sorted(lead.get("maquinas", set()))) or lead["origen"]
    pipedrive("/deals", "POST", _cuerpo={
        "title": f"Prospecto - {lead['origen']} - {detalle}"[:120],
        "person_id": person_id, "pipeline_id": PIPELINE, "stage_id": ETAPA})
    return "creado"


def recoger():
    print(f"ventana: últimas {VENTANA_H} h · prueba={PRUEBA}")
    frio = senales_frio()
    print(f"frío: {len(frio)} contactos con señal")
    tibio = senales_brevo()
    print(f"campañas BBDD: {len(tibio)} contactos con clic")

    todos = {}
    for origen, grupo in (("Respuesta frío", frio), ("Clic campaña BBDD", tibio)):
        for email, lead in grupo.items():
            e = todos.setdefault(email, dict(
                email=email, nombre="", empresa="", senales=[],
                maquinas=set(), campanas=set(), origen=origen))
            e["senales"] += lead["senales"]
            e["nombre"] = e["nombre"] or lead.get("nombre", "")
            e["empresa"] = e["empresa"] or lead.get("empresa", "")
            e["maquinas"] |= lead.get("maquinas", set())
            e["campanas"] |= lead.get("campanas", set())
            if "respuesta_frio" in lead["senales"]:
                e["origen"] = "Respuesta frío"

    filas = []
    for email, lead in todos.items():
        pid, tel, hist = enriquecer(lead)
        score = puntuar(lead, bool(tel), hist)
        if score < 30:
            continue
        try:
            estado_crm = a_pipedrive(lead, pid)
        except Exception as err:
            # Un lead que no entra en el CRM no debe tumbar el informe entero.
            estado_crm = f"error: {err}"[:60]
        filas.append(dict(
            SCORE=score,
            NIVEL="HOT" if score >= 60 else "WARM",
            NOMBRE=lead.get("nombre", ""), EMPRESA=lead.get("empresa", ""),
            EMAIL=email, TELEFONO=tel,
            ORIGEN=lead["origen"],
            DETALLE=(" · ".join(sorted(lead["maquinas"])) or
                     ", ".join(sorted(lead["campanas"])) or "-")[:80],
            CRM=estado_crm,
            ACCION="Llamar hoy" if score >= 60 else "Seguimiento"))
        time.sleep(0.25)  # límite de 10 peticiones/ventana de Pipedrive

    filas.sort(key=lambda f: -f["SCORE"])
    os.makedirs(os.path.dirname(SALIDA_CSV), exist_ok=True)
    with open(SALIDA_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()) if filas else
                           ["SCORE", "EMAIL"])
        w.writeheader()
        w.writerows(filas)
    print(f"\n{len(filas)} leads en el informe → {SALIDA_CSV}")
    for x in filas[:10]:
        print(f"  {x['SCORE']:>3} {x['NIVEL']:<5} {x['EMAIL'][:34]:<34} {x['ORIGEN']}")
    return filas


def enviar(filas, url_sheet=""):
    hoy = dt.date.today().strftime("%d/%m/%Y")
    if not filas:
        cuerpo_tabla = "<p>Hoy no hay respuestas ni clics nuevos. El frío sigue enviando.</p>"
    else:
        celdas = "".join(
            f"<tr><td style='padding:6px 10px;text-align:center;font-weight:700;"
            f"color:{'#B23A2A' if f['NIVEL']=='HOT' else '#8A6210'}'>{f['SCORE']}</td>"
            f"<td style='padding:6px 10px'>{f['NOMBRE'] or '-'}<br>"
            f"<span style='color:#667085;font-size:12px'>{f['EMPRESA'] or ''}</span></td>"
            f"<td style='padding:6px 10px'>{f['EMAIL']}<br>"
            f"<b>{f['TELEFONO'] or 'sin teléfono'}</b></td>"
            f"<td style='padding:6px 10px'>{f['ORIGEN']}<br>"
            f"<span style='color:#667085;font-size:12px'>{f['DETALLE']}</span></td>"
            f"<td style='padding:6px 10px'><b>{f['ACCION']}</b></td></tr>"
            for f in filas)
        cuerpo_tabla = (
            "<table style='border-collapse:collapse;font-size:14px;width:100%'>"
            "<tr style='background:#17323A;color:#fff'>"
            "<th style='padding:8px 10px'>Score</th><th style='padding:8px 10px'>Quién</th>"
            "<th style='padding:8px 10px'>Contacto</th><th style='padding:8px 10px'>Origen</th>"
            "<th style='padding:8px 10px'>Acción</th></tr>" + celdas + "</table>")
    enlace = (f"<p><a href='{url_sheet}'>Abrir en Google Sheets</a> para marcar "
              f"las llamadas.</p>" if url_sheet else "")
    hot = sum(1 for f in filas if f["NIVEL"] == "HOT")
    html = (f"<div style='font-family:system-ui,sans-serif;max-width:720px'>"
            f"<h2 style='margin:0 0 4px'>Respuestas y leads calientes · {hoy}</h2>"
            f"<p style='color:#3A424E'>{len(filas)} leads con señal en las últimas "
            f"{VENTANA_H} h · <b>{hot} para llamar hoy</b>. Todos creados como "
            f"prospecto en Pipedrive (Transaccional → Lead - Recibido).</p>"
            f"{cuerpo_tabla}{enlace}"
            f"<p style='color:#8A94A0;font-size:12px'>Scoring: +50 respuesta a "
            f"frío · +40 clic en máquina · +10 por clic extra · +20 historial en "
            f"CRM · +10 con teléfono. HOT ≥60.</p></div>")
    if PRUEBA:
        print("PRUEBA=1 → email no enviado")
        return
    brevo("/smtp/email", "POST", {
        "sender": {"name": "Equipzilla · Leads", "email": "clientes@equipzilla.com"},
        "replyTo": {"email": "clientes@equipzilla.com"},
        "to": [{"email": e} for e in DESTINATARIOS],
        "subject": f"[{hot} HOT] Respuestas y leads · {hoy}",
        "htmlContent": html})
    print(f"email enviado a {', '.join(DESTINATARIOS)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "enviar":
        # Reutiliza el CSV del paso de recogida: recolectar dos veces
        # repetiría los exports lentos de Brevo.
        with open(SALIDA_CSV) as f:
            filas = [dict(r) for r in csv.DictReader(f)]
        for fila in filas:
            fila["SCORE"] = int(fila["SCORE"])
        enviar(filas, sys.argv[2] if len(sys.argv) > 2 else "")
    else:
        recoger()
