#!/usr/bin/env python3
"""Digest de leads calientes · Equipzilla.

Cada ejecución:
 1. Detecta las campañas de compraventa enviadas en los últimos DAYS días (Brevo).
 2. Exporta los que han hecho CLIC en cada una (actividad real por contacto).
 3. Deduce qué máquina le interesó a cada uno (por el enlace de WhatsApp pulsado).
 4. Enriquece nombre/teléfono/empresa desde Pipedrive (búsqueda por email).
 5. Diffea contra el estado (hashes, sin PII) para avisar SOLO de clics nuevos.
 6. Manda el digest a David y Andrés (tabla + CSV adjunto) vía Brevo.
 7. Actualiza el estado.

Credenciales por variables de entorno (secrets):  BREVO_API_KEY  ·  PIPEDRIVE_TOKEN
"""
import os, sys, json, csv, io, time, base64, hashlib, urllib.request, urllib.error, re

BREVO = os.environ["BREVO_API_KEY"]
PIPE  = os.environ.get("PIPEDRIVE_TOKEN", "")
TO    = [{"email": "david@equipzilla.com", "name": "David"},
         {"email": "andres@equipzilla.com", "name": "Andrés"}]
SENDER_ID = 10
DAYS = int(os.environ.get("DIGEST_DAYS", "10"))
STATE = os.path.join(os.path.dirname(__file__), "state_notified.json")

def brevo(path, method="GET", body=None):
    url = "https://api.brevo.com/v3" + path
    data = json.dumps(body).encode() if body is not None else (b"" if method == "POST" else None)
    for _ in range(6):
        req = urllib.request.Request(url, data=data, method=method,
              headers={"api-key": BREVO, "content-type": "application/json", "accept": "application/json"})
        try:
            r = urllib.request.urlopen(req, timeout=40)
            b = r.read().decode()
            return r.status, (json.loads(b) if b else {})
        except urllib.error.HTTPError as e:
            body_txt = e.read().decode()
            if "unrecognised IP" in body_txt:
                time.sleep(2); continue
            return e.code, body_txt
    return 0, "retry_exhausted"

def download(url):
    import subprocess
    return subprocess.run(["curl", "-s", "-m", "60", "-A", "Mozilla/5.0", url],
                          capture_output=True, text=True).stdout

def recent_campaigns():
    """Campañas enviadas en los últimos DAYS días cuyo nombre huele a compraventa."""
    import datetime
    cutoff = time.time() - DAYS * 86400
    out = []
    s, d = brevo("/emailCampaigns?status=sent&limit=100&sort=desc")
    for c in (d.get("campaigns") if isinstance(d, dict) else []) or []:
        sd = c.get("sentDate") or c.get("scheduledAt")
        if not sd:
            continue
        try:
            ts = datetime.datetime.fromisoformat(sd.replace("Z", "+00:00")).timestamp()
        except Exception:
            continue
        if ts < cutoff:
            continue
        name = (c.get("name") or "").lower()
        if any(k in name for k in ["compraventa", "plataforma", "miniexcav", "excavad", "pala", "elevaci", "stock"]):
            out.append({"id": c["id"], "name": c.get("name")})
    return out

def export_clickers(cid):
    s, d = brevo(f"/emailCampaigns/{cid}/exportRecipients", "POST", {"recipientsType": "clickers"})
    pid = d.get("processId") if isinstance(d, dict) else None
    if not pid:
        return []
    url = None
    for _ in range(20):
        s, p = brevo(f"/processes/{pid}")
        if isinstance(p, dict) and p.get("status") == "completed":
            url = p.get("export_url"); break
        time.sleep(3)
    if not url:
        return []
    text = download(url)
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    if len(rows) < 2:
        return []
    hdr = rows[0]
    i_email = next((i for i, h in enumerate(hdr) if "Email_ID" in h), 0)
    # link columns -> machine ref (from "...me interesa la REF")
    link_cols = {}
    for i, h in enumerate(hdr):
        m = re.search(r"interesa la ([A-Z0-9\-]+)", h)
        if m:
            link_cols[i] = m.group(1)
    res = []
    for r in rows[1:]:
        if len(r) < len(hdr):
            r = r + [""] * (len(hdr) - len(r))
        email = (r[i_email] or "").strip().lower()
        if "@" not in email:
            continue
        machines = sorted({ref for i, ref in link_cols.items() if r[i].strip()})
        res.append({"email": email, "machines": machines})
    return res

def pipe_enrich(email):
    if not PIPE:
        return {}
    try:
        u = f"https://api.pipedrive.com/v1/persons/search?term={urllib.parse.quote(email)}&fields=email&exact_match=true&limit=1&api_token={PIPE}"
        d = json.loads(urllib.request.urlopen(u, timeout=25).read())
        items = (d.get("data") or {}).get("items") or []
        if not items:
            return {}
        it = items[0].get("item", {})
        phones = it.get("phones") or []
        org = (it.get("organization") or {}).get("name", "") if isinstance(it.get("organization"), dict) else ""
        return {"name": it.get("name", ""), "phone": (phones[0] if phones else ""), "org": org}
    except Exception:
        return {}

import urllib.parse

def main():
    state = {}
    if os.path.exists(STATE):
        try: state = json.load(open(STATE))
        except Exception: state = {}
    seen = set(state.get("hashes", []))

    camps = recent_campaigns()
    leads = {}  # email -> {machines set, campaigns set}
    for c in camps:
        for row in export_clickers(c["id"]):
            key = hashlib.sha256(f"{c['id']}:{row['email']}".encode()).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            L = leads.setdefault(row["email"], {"machines": set(), "campaigns": set()})
            L["machines"].update(row["machines"])
            L["campaigns"].add(c["name"])

    if not leads:
        print("Sin clics nuevos. Nada que enviar.")
        json.dump({"hashes": sorted(seen)}, open(STATE, "w"))
        return

    # enrich + build rows
    rows = []
    for email, L in leads.items():
        info = pipe_enrich(email)
        rows.append({
            "empresa": info.get("org") or email.split("@")[1],
            "contacto": info.get("name") or "",
            "email": email,
            "telefono": info.get("phone") or "",
            "maquinas": " · ".join(sorted(L["machines"])) or "(catálogo/genérico)",
            "campana": " · ".join(sorted(L["campaigns"])),
        })
    rows.sort(key=lambda r: (r["maquinas"] == "(catálogo/genérico)", r["empresa"]))

    # CSV attachment
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["Empresa", "Contacto", "Email", "Telefono", "Maquina(s) de interes", "Campana"])
    for r in rows:
        w.writerow([r["empresa"], r["contacto"], r["email"], r["telefono"], r["maquinas"], r["campana"]])
    csv_b64 = base64.b64encode(buf.getvalue().encode()).decode()

    # HTML table
    trs = ""
    for r in rows:
        tel = re.sub(r"[^0-9+]", "", r["telefono"])
        telcell = f'<a href="tel:{tel}" style="color:#0a58ca;text-decoration:none">{r["telefono"]}</a>' if tel else "—"
        wa = f'&nbsp;·&nbsp;<a href="https://wa.me/{tel.lstrip("+")}" style="color:#1F9D5B;text-decoration:none">WA</a>' if tel else ""
        trs += (f'<tr><td style="padding:9px 12px;border-bottom:1px solid #E3E1DB"><b>{r["empresa"]}</b>'
                f'<div style="font-size:12px;color:#5B5F66">{r["contacto"]}</div>'
                f'<div style="font-size:12px;color:#5B5F66">{r["email"]}</div></td>'
                f'<td style="padding:9px 12px;border-bottom:1px solid #E3E1DB">{telcell}{wa}</td>'
                f'<td style="padding:9px 12px;border-bottom:1px solid #E3E1DB">{r["maquinas"]}</td></tr>')
    html = (f'<div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto">'
            f'<div style="background:#1B1D21;padding:18px 22px;border-radius:10px 10px 0 0">'
            f'<span style="font:800 17px Arial;color:#F5A623">🔥 {len(rows)} leads calientes nuevos</span>'
            f'<div style="color:#C9CDD4;font-size:13px">Han hecho clic en las campañas de compraventa · a llamar hoy</div></div>'
            f'<table style="width:100%;border-collapse:collapse;border:1px solid #E3E1DB;font-size:14px">'
            f'<tr style="background:#FAF9F6"><td style="padding:8px 12px;font-size:11px;color:#5B5F66;text-transform:uppercase">Contacto</td>'
            f'<td style="padding:8px 12px;font-size:11px;color:#5B5F66;text-transform:uppercase">Teléfono</td>'
            f'<td style="padding:8px 12px;font-size:11px;color:#5B5F66;text-transform:uppercase">Máquina(s)</td></tr>{trs}</table>'
            f'<p style="font-size:12px;color:#8A8F98;margin-top:14px">El clic abre WhatsApp con el mensaje escrito, pero no garantiza que lo enviaran — es intención de compra. Detalle completo en el CSV adjunto.</p></div>')

    st, r = brevo("/smtp/email", "POST", {
        "sender": {"id": SENDER_ID},
        "to": TO,
        "replyTo": {"email": "clientes@equipzilla.com", "name": "Equipzilla"},
        "subject": f"🔥 {len(rows)} leads calientes nuevos · compraventa Equipzilla",
        "htmlContent": html,
        "attachment": [{"name": "leads_calientes.csv", "content": csv_b64}],
    })
    print("Email digest ->", st, r)
    json.dump({"hashes": sorted(seen)}, open(STATE, "w"))
    print(f"Enviados {len(rows)} leads. Estado actualizado ({len(seen)} hashes).")

if __name__ == "__main__":
    main()
