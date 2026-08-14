#!/usr/bin/env python3
"""Informe comercial diario: resultados de Brevo (templada) + Smartlead (frío).

Cada mañana envía a comercial un email con:
  1. Leads accionables — quién ha clicado en qué máquina (últimas 48 h) con
     empresa y teléfono (enriquecido desde Pipedrive), y quién ha respondido
     en la campaña de frío.
  2. Resumen de números por campaña (enviados / aperturas / clics reales por
     export — el globalStats de la API de Brevo devuelve 0 por un bug).

Env: BREVO_API_KEY, SMARTLEAD_API_KEY, PIPEDRIVE_TOKEN.
Opcionales: REPORT_TO (emails separados por coma; por defecto David, Andrés y
Maikel), REPORT_DAYS (ventana de campañas Brevo, por defecto 10),
FRESH_HOURS (ventana de "clics nuevos", por defecto 48).
"""
import datetime
import html as htmllib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BREVO_KEY = os.environ.get("BREVO_API_KEY", "")
SL_KEY = os.environ.get("SMARTLEAD_API_KEY", "")
PD_TOKEN = os.environ.get("PIPEDRIVE_TOKEN", "")
TO = [e.strip() for e in os.environ.get(
    "REPORT_TO", "david@equipzilla.com,andres@equipzilla.com,maikel@equipzilla.com"
).split(",") if e.strip()]
DAYS = int(os.environ.get("REPORT_DAYS", "10"))
FRESH_HOURS = int(os.environ.get("FRESH_HOURS", "48"))

KEYWORDS = ["compraventa", "plataforma", "miniexcav", "excavad", "pala",
            "elevaci", "stock", "carretilla", "manipulador", "telesc",
            "oportunidad"]


def brevo(method, path, body=None):
    req = urllib.request.Request(
        "https://api.brevo.com/v3/" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"api-key": BREVO_KEY, "content-type": "application/json",
                 "accept": "application/json"}, method=method)
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


def export_csv(campaign_id, rtype):
    r = brevo("POST", f"emailCampaigns/{campaign_id}/exportRecipients",
              {"recipientsType": rtype})
    pid = r.get("processId")
    if not pid:
        return None
    for _ in range(30):
        p = brevo("GET", f"processes/{pid}")
        if p.get("status") == "completed" and p.get("export_url"):
            out = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0",
                                  p["export_url"]],
                                 capture_output=True, text=True).stdout
            return [l for l in out.splitlines() if l.strip()]
        time.sleep(6)
    return None


def machine_from_link(link):
    """Nombre de máquina a partir del texto del enlace de WhatsApp."""
    txt = urllib.parse.unquote(link)
    m = re.search(r"interesad[oa] en (?:la|el)\s+([^&\"]+)", txt)
    if m:
        return m.group(1).strip()
    if "wa.me" in txt:
        return "CTA general (WhatsApp)"
    if "equipzilla.com" in txt:
        return "Catálogo web"
    return "Otro enlace"


def parse_ts(val):
    for fmt in ("%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.datetime.strptime(val.strip(), fmt)
        except Exception:
            pass
    return None


def brevo_campaigns():
    """Campañas de compraventa enviadas en la ventana."""
    data = brevo("GET", "emailCampaigns?status=sent&limit=25&sort=desc")
    cutoff = datetime.datetime.now() - datetime.timedelta(days=DAYS)
    out = []
    for c in data.get("campaigns", []):
        name = (c.get("name") or "").lower()
        if not any(k in name for k in KEYWORDS):
            continue
        sd = c.get("sentDate") or ""
        try:
            when = datetime.datetime.fromisoformat(sd.replace("Z", "+00:00"))
            when = when.replace(tzinfo=None)
        except Exception:
            when = None
        if when and when < cutoff:
            continue
        out.append({"id": c["id"], "name": c.get("name"), "sent": sd[:10]})
    return out


def brevo_stats_and_clicks(camp):
    cid = camp["id"]
    allc = export_csv(cid, "all")
    opn = export_csv(cid, "openers")
    clk = export_csv(cid, "clickers")
    sent = max(0, len(allc) - 1) if allc else None
    opens = max(0, len(opn) - 1) if opn else None
    clicks = []
    if clk and len(clk) > 1:
        hdr = [h.strip('"') for h in clk[0].split(";")]
        link_cols = {i: machine_from_link(h) for i, h in enumerate(hdr)
                     if h.startswith("http")}
        idx_email = next((i for i, h in enumerate(hdr)
                          if "email" in h.lower()), 2)
        for line in clk[1:]:
            parts = [p.strip('"') for p in line.split(";")]
            email = parts[idx_email].strip().lower()
            if "@" not in email:
                continue
            machines, latest = [], None
            for i, mach in link_cols.items():
                if i < len(parts) and parts[i].strip():
                    machines.append(mach)
                    ts = parse_ts(parts[i])
                    if ts and (latest is None or ts > latest):
                        latest = ts
            clicks.append({"email": email, "machines": machines,
                           "when": latest})
    return {"sent": sent, "opens": opens, "clicks": clicks}


def pipedrive(email):
    if not PD_TOKEN:
        return "", "", ""
    def get(path, **p):
        p["api_token"] = PD_TOKEN
        url = ("https://api.pipedrive.com/v1/" + path + "?" +
               urllib.parse.urlencode(p))
        try:
            return json.load(urllib.request.urlopen(url, timeout=25))
        except Exception:
            return {}
    r = get("persons/search", term=email, fields="email", exact_match="true")
    items = (r.get("data") or {}).get("items") or []
    if not items:
        return "", "", ""
    it = items[0]["item"]
    nombre = it.get("name", "")
    org = (it.get("organization") or {}).get("name", "") \
        if it.get("organization") else ""
    tel = ""
    pr = get(f"persons/{it.get('id')}")
    phones = (pr.get("data") or {}).get("phone") or []
    if phones:
        tel = phones[0].get("value", "")
    return nombre, org, tel


def smartlead():
    def get(path):
        sep = "&" if "?" in path else "?"
        url = f"https://server.smartlead.ai/api/v1{path}{sep}api_key={SL_KEY}"
        for attempt in range(4):
            try:
                return json.load(urllib.request.urlopen(url, timeout=45))
            except Exception:
                time.sleep(5 * (attempt + 1))
        return {}
    camps = get("/campaigns")
    camps = camps if isinstance(camps, list) else camps.get("data", [])
    out = []
    for c in camps or []:
        cid = c.get("id")
        a = get(f"/campaigns/{cid}/analytics")
        stats = get(f"/campaigns/{cid}/statistics?offset=0&limit=100")
        rows = stats.get("data") or []
        replies = [r for r in rows if r.get("reply_time")]
        out.append({"name": c.get("name"), "status": c.get("status"),
                    "sent": a.get("sent_count") or 0,
                    "reply_count": a.get("reply_count") or 0,
                    "bounces": a.get("bounce_count") or 0,
                    "total": (a.get("campaign_lead_stats") or {}).get("total"),
                    "replies": replies})
    return out


def esc(s):
    return htmllib.escape(str(s or ""))


def build_html(campaign_data, cold):
    now = datetime.datetime.now()
    fresh_cut = now - datetime.timedelta(hours=FRESH_HOURS)

    # --- leads accionables (clics recientes, dedup por email) ---
    hot = {}
    for camp, st in campaign_data:
        for c in st["clicks"]:
            if "@equipzilla.com" in c["email"]:
                continue
            if c["when"] and c["when"] < fresh_cut:
                continue
            e = hot.setdefault(c["email"], {"machines": set(), "camps": set(),
                                            "when": c["when"]})
            e["machines"].update(m for m in c["machines"]
                                 if "Catálogo" not in m and "CTA" not in m
                                 and "Otro" not in m)
            e["camps"].add(camp["name"])
            if c["when"] and (e["when"] is None or c["when"] > e["when"]):
                e["when"] = c["when"]

    hot_rows = ""
    for email, info in sorted(hot.items(),
                              key=lambda kv: kv[1]["when"] or datetime.datetime.min,
                              reverse=True):
        nombre, org, tel = pipedrive(email)
        who = org or nombre or email
        maqs = " · ".join(sorted(info["machines"])) or "(catálogo)"
        multi = " 🔥" if len(info["machines"]) > 1 else ""
        when = info["when"].strftime("%d-%m %H:%M") if info["when"] else "—"
        hot_rows += (f"<tr><td style='padding:7px 10px;border-bottom:1px solid "
                     f"#EEF1F4;font-weight:600;color:#14181C'>{esc(who)}{multi}"
                     f"</td><td style='padding:7px 10px;border-bottom:1px solid "
                     f"#EEF1F4'>{esc(tel) or '—'}</td>"
                     f"<td style='padding:7px 10px;border-bottom:1px solid "
                     f"#EEF1F4;font-size:12px'>{esc(email)}</td>"
                     f"<td style='padding:7px 10px;border-bottom:1px solid "
                     f"#EEF1F4;font-size:12px'>{esc(maqs)}</td>"
                     f"<td style='padding:7px 10px;border-bottom:1px solid "
                     f"#EEF1F4;font-size:12px'>{when}</td></tr>")
    if not hot_rows:
        hot_rows = ("<tr><td colspan='5' style='padding:10px;color:#667085'>"
                    "Sin clics nuevos en las últimas 48 h.</td></tr>")

    # --- respuestas del frío ---
    cold_rows = ""
    for c in cold:
        for r in c["replies"]:
            cold_rows += (f"<tr><td style='padding:7px 10px;border-bottom:1px "
                          f"solid #EEF1F4;font-weight:600'>"
                          f"{esc(r.get('lead_name') or r.get('lead_email'))}"
                          f"</td><td style='padding:7px 10px;border-bottom:1px "
                          f"solid #EEF1F4;font-size:12px'>"
                          f"{esc(r.get('lead_email'))}</td>"
                          f"<td style='padding:7px 10px;border-bottom:1px solid "
                          f"#EEF1F4;font-size:12px'>"
                          f"{esc((r.get('reply_time') or '')[:16])}</td></tr>")
    if not cold_rows:
        cold_rows = ("<tr><td colspan='3' style='padding:10px;color:#667085'>"
                     "Sin respuestas nuevas.</td></tr>")

    # --- resumen campañas Brevo ---
    camp_rows = ""
    for camp, st in campaign_data:
        rate = (f"{100 * st['opens'] / st['sent']:.1f}%"
                if st["sent"] and st["opens"] is not None else "—")
        camp_rows += (f"<tr><td style='padding:6px 10px;border-bottom:1px solid "
                      f"#EEF1F4'>{esc(camp['name'])[:48]}</td>"
                      f"<td style='padding:6px 10px;border-bottom:1px solid "
                      f"#EEF1F4;font-size:12px'>{esc(camp['sent'])}</td>"
                      f"<td style='padding:6px 10px;border-bottom:1px solid "
                      f"#EEF1F4;text-align:right'>{st['sent'] or '—'}</td>"
                      f"<td style='padding:6px 10px;border-bottom:1px solid "
                      f"#EEF1F4;text-align:right'>{st['opens'] if st['opens'] is not None else '—'}</td>"
                      f"<td style='padding:6px 10px;border-bottom:1px solid "
                      f"#EEF1F4;text-align:right'>{rate}</td>"
                      f"<td style='padding:6px 10px;border-bottom:1px solid "
                      f"#EEF1F4;text-align:right;font-weight:700;color:#387E7F'>"
                      f"{len(st['clicks'])}</td></tr>")

    cold_summary = ""
    for c in cold:
        cold_summary += (f"<li><strong>{esc(c['name'])}</strong> "
                         f"({esc(c['status'])}): {c['sent']} emails enviados · "
                         f"<strong>{c['reply_count']} respuestas</strong> · "
                         f"{c['bounces']} rebotes · {c['total']} leads</li>")

    th = ("text-align:left;padding:7px 10px;background:#F4F7F9;font-size:11px;"
          "color:#667085")
    return f"""<div style="font-family:system-ui,sans-serif;font-size:14px;
line-height:1.55;color:#14181C;max-width:680px">
<p style="font-size:16px"><strong>Informe comercial diario</strong> ·
{now.strftime('%d-%m-%Y')} </p>

<h3 style="margin:18px 0 8px;color:#14181C">🔥 Para llamar hoy — clics últimas
{FRESH_HOURS} h (newsletter)</h3>
<table style="width:100%;border-collapse:collapse;font-size:13px;
background:#fff;border:1px solid #D9DEE4">
<tr><th style='{th}'>EMPRESA / CONTACTO</th><th style='{th}'>TELÉFONO</th>
<th style='{th}'>EMAIL</th><th style='{th}'>MÁQUINA(S)</th>
<th style='{th}'>CUÁNDO</th></tr>{hot_rows}</table>
<p style="font-size:12px;color:#667085">🔥 = clicó en varias máquinas.</p>

<h3 style="margin:22px 0 8px">✉️ Respuestas del outbound en frío</h3>
<table style="width:100%;border-collapse:collapse;font-size:13px;
background:#fff;border:1px solid #D9DEE4">
<tr><th style='{th}'>LEAD</th><th style='{th}'>EMAIL</th>
<th style='{th}'>CUÁNDO</th></tr>{cold_rows}</table>
<ul style="font-size:13px;color:#3A424E">{cold_summary}</ul>

<h3 style="margin:22px 0 8px">📊 Números por campaña (Brevo)</h3>
<table style="width:100%;border-collapse:collapse;font-size:12.5px;
background:#fff;border:1px solid #D9DEE4">
<tr><th style='{th}'>CAMPAÑA</th><th style='{th}'>FECHA</th>
<th style='{th};text-align:right'>ENVIADOS</th>
<th style='{th};text-align:right'>APERTURAS</th>
<th style='{th};text-align:right'>%</th>
<th style='{th};text-align:right'>CLICS</th></tr>{camp_rows}</table>

<p style="font-size:11.5px;color:#8A93A0;margin-top:16px">Informe automático
diario · métricas por export de Brevo y API de Smartlead · los clics con
teléfono también quedan en el Sheet de seguimiento.</p></div>"""


def main():
    missing = [n for n, v in [("BREVO_API_KEY", BREVO_KEY),
                              ("SMARTLEAD_API_KEY", SL_KEY)] if not v]
    if missing:
        print("Faltan variables:", ", ".join(missing))
        sys.exit(1)
    camps = brevo_campaigns()
    campaign_data = [(c, brevo_stats_and_clicks(c)) for c in camps]
    cold = smartlead() if SL_KEY else []
    html = build_html(campaign_data, cold)
    for to in TO:
        payload = {"sender": {"id": 10}, "to": [{"email": to}],
                   "subject": f"Informe comercial · {datetime.date.today():%d-%m}"
                              " · leads y resultados",
                   "htmlContent": html, "tags": ["informe-comercial"]}
        r = brevo("POST", "smtp/email", payload)
        print("enviado a", to, "->", r.get("messageId") or r)


if __name__ == "__main__":
    main()
