#!/usr/bin/env python3
"""Vuelca cada día las métricas de envío (Brevo + Smartlead) al Google Sheet.

Añade una fila por campaña y día en la pestaña "Métricas Envíos" del Sheet de
seguimiento, para tener la serie histórica: enviados, aperturas, clics,
respuestas y rebotes.

- Brevo: las cifras salen del export de destinatarios (el globalStats de la API
  devuelve 0 por un bug conocido), solo campañas de compraventa ya enviadas.
- Smartlead: analytics de cada campaña (el frío) + salud del warmup.

Env necesarias: BREVO_API_KEY, SMARTLEAD_API_KEY, GOOGLE_SA_JSON.
Opcionales: METRICS_SHEET_ID (por defecto el sheet de seguimiento),
METRICS_TAB (por defecto "Métricas Envíos").
"""
import datetime
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

BREVO_KEY = os.environ.get("BREVO_API_KEY", "")
SL_KEY = os.environ.get("SMARTLEAD_API_KEY", "")
SA_JSON = os.environ.get("GOOGLE_SA_JSON", "")
SHEET_ID = os.environ.get("METRICS_SHEET_ID", "1KgVYP1jjQB8NbUSvfS9PLcaFEJDY4ldFH2vphW1sakI")
TAB = os.environ.get("METRICS_TAB", "Métricas Envíos")

# Mismas palabras clave que el digest para identificar campañas de compraventa.
KEYWORDS = ["compraventa", "plataforma", "miniexcav", "excavad", "pala",
            "elevaci", "stock", "carretilla", "manipulador", "telesc"]

HEADER = ["fecha", "canal", "campaña", "enviados", "aperturas", "apertura %",
          "clics", "respuestas", "rebotes", "notas"]


def brevo(method, path, body=None):
    req = urllib.request.Request(
        "https://api.brevo.com/v3/" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"api-key": BREVO_KEY, "content-type": "application/json",
                 "accept": "application/json"},
        method=method)
    for attempt in range(4):
        try:
            r = urllib.request.urlopen(req, timeout=60)
            return json.load(r) if r.length != 0 else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(5 * (attempt + 1))
                continue
            return json.loads(e.read() or b"{}")
        except Exception:
            time.sleep(5)
    return {}


def export_count(campaign_id, rtype):
    """Cuenta destinatarios de un tipo vía export (CSV con cabecera, sep ';')."""
    r = brevo("POST", f"emailCampaigns/{campaign_id}/exportRecipients",
              {"recipientsType": rtype})
    pid = r.get("processId")
    if not pid:
        return None
    url = None
    for _ in range(30):
        p = brevo("GET", f"processes/{pid}")
        if p.get("status") == "completed" and p.get("export_url"):
            url = p["export_url"]
            break
        time.sleep(6)
    if not url:
        return None
    # El CDN de storage rechaza urllib sin User-Agent; curl funciona.
    raw = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", url],
                         capture_output=True, text=True).stdout
    lines = [l for l in raw.splitlines() if l.strip()]
    return max(0, len(lines) - 1)


def brevo_rows(today):
    data = brevo("GET", "emailCampaigns?status=sent&limit=50&sort=desc")
    camps = [c for c in data.get("campaigns", [])
             if any(k in (c.get("name") or "").lower() for k in KEYWORDS)]
    rows, tot = [], [0, 0, 0]
    for c in camps:
        cid = c["id"]
        sent = export_count(cid, "all")
        opens = export_count(cid, "openers")
        clicks = export_count(cid, "clickers")
        if sent is None:
            rows.append([today, "Brevo", c.get("name", str(cid)), "", "", "",
                         "", "", "", "export falló"])
            continue
        rate = f"{100 * (opens or 0) / sent:.1f}%" if sent else ""
        rows.append([today, "Brevo", c.get("name", str(cid)), sent, opens or 0,
                     rate, clicks if clicks is not None else "", "n/a", "", ""])
        tot[0] += sent
        tot[1] += opens or 0
        tot[2] += clicks or 0
    if tot[0]:
        rows.append([today, "Brevo", "TOTAL", tot[0], tot[1],
                     f"{100 * tot[1] / tot[0]:.1f}%", tot[2], "n/a", "", ""])
    return rows


def smartlead_get(path):
    sep = "&" if "?" in path else "?"
    url = f"https://server.smartlead.ai/api/v1{path}{sep}api_key={SL_KEY}"
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(url, timeout=45))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return {}


def smartlead_rows(today):
    rows = []
    camps = smartlead_get("/campaigns")
    camps = camps if isinstance(camps, list) else camps.get("data", [])
    for c in camps or []:
        cid = c.get("id")
        a = smartlead_get(f"/campaigns/{cid}/analytics")
        sent = a.get("sent_count")
        stats = a.get("campaign_lead_stats") or {}
        note = f"status={c.get('status')} · leads={stats.get('total')}"
        rate = ""
        if sent:
            rate = f"{100 * (a.get('unique_open_count') or 0) / int(sent):.1f}%"
        rows.append([today, "Smartlead", c.get("name", str(cid)), sent or 0,
                     a.get("unique_open_count") or 0, rate,
                     a.get("click_count") or 0, a.get("reply_count") or 0,
                     a.get("bounce_count") or 0, note])
    # Salud del warmup como fila informativa.
    accs = smartlead_get("/email-accounts/?limit=50")
    accs = accs if isinstance(accs, list) else accs.get("data", [])
    if accs:
        active = sum(1 for x in accs
                     if (x.get("warmup_details") or {}).get("status") == "ACTIVE")
        wsent = sum((x.get("warmup_details") or {}).get("total_sent_count") or 0
                    for x in accs)
        spam = sum((x.get("warmup_details") or {}).get("total_spam_count") or 0
                   for x in accs)
        rows.append([today, "Smartlead", "WARMUP buzones", wsent, "", "", "", "",
                     spam, f"{active}/{len(accs)} activos"])
    return rows


def write_sheet(rows):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_info(
        json.loads(SA_JSON),
        scopes=["https://www.googleapis.com/auth/spreadsheets"])
    svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    titles = [s["properties"]["title"] for s in meta["sheets"]]
    if TAB not in titles:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": [{"addSheet": {"properties": {"title": TAB}}}]},
        ).execute()
        rows = [HEADER] + rows
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID, range=f"'{TAB}'!A1",
        valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
        body={"values": rows}).execute()
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"


def main():
    missing = [n for n, v in [("BREVO_API_KEY", BREVO_KEY),
                              ("SMARTLEAD_API_KEY", SL_KEY),
                              ("GOOGLE_SA_JSON", SA_JSON)] if not v]
    if missing:
        print("Faltan variables:", ", ".join(missing))
        sys.exit(1)
    today = datetime.date.today().isoformat()
    rows = brevo_rows(today) + smartlead_rows(today)
    if not rows:
        print("Sin datos que volcar.")
        return
    link = write_sheet(rows)
    print(f"{len(rows)} filas añadidas a '{TAB}' → {link}")


if __name__ == "__main__":
    main()
