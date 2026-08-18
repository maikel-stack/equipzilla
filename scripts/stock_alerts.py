#!/usr/bin/env python3
"""Alertas de stock: avisa a los suscriptores de bajadas de precio y novedades.

Compara data/machines.json (catálogo canónico) con el último estado guardado
(scripts/state_stock.json). Si hay bajadas de precio o máquinas nuevas, envía
un email a cada suscriptor de la lista de Brevo "Alertas Stock" (#33) cuya
categoría de interés (y presupuesto, si lo indicó) encaje. Sin cambios → no
se envía nada.

El primer run solo guarda el estado (no alerta sobre stock ya conocido).

Env: BREVO_API_KEY. Opcional: ALERT_LIST_ID (33), TEAM_SUMMARY (1 = enviar
resumen al equipo cuando haya alertas).
Cuando el equipo active WhatsApp Business en Brevo, poner BREVO_WA_TEMPLATE_ID
para que además del email salga el aviso por WhatsApp al teléfono del
suscriptor (hasta entonces, solo email).
"""
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

KEY = os.environ.get("BREVO_API_KEY", "")
LIST_ID = int(os.environ.get("ALERT_LIST_ID", "33"))
WA_TEMPLATE = os.environ.get("BREVO_WA_TEMPLATE_ID", "")
MACHINES = "data/machines.json"
STATE = "scripts/state_stock.json"
IMG = "https://cdn.jsdelivr.net/gh/maikel-stack/equipzilla@7f1a7307d80db1639f05024cc720552c363df284/email_assets/machines/"
LANDING = "https://equipzilla-quiz.vercel.app"

# categoría interna -> texto que eligió el suscriptor en el quiz
CAT_LABEL = {
    "mini": "Miniexcavadora (hasta 8 t)",
    "exca": "Excavadora grande (14-23 t)",
    "plat": "Plataforma elevadora",
    "carr": "Carretilla elevadora",
    "tele": "Manipulador telescópico",
    "pala": "Pala cargadora",
}
ALL_CATS = {"No lo tengo claro", "todas", ""}


def brevo(method, path, body=None):
    req = urllib.request.Request(
        "https://api.brevo.com/v3/" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"api-key": KEY, "content-type": "application/json",
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


def fmt(p):
    return f"{p:,.0f}".replace(",", ".") + " €"


def machine_card(m, old_price=None):
    drop = ""
    # si la ficha trae precio anterior propio, vale como referencia del "antes"
    if not old_price and m.get("pa") and m["pa"] > m["p"]:
        old_price = m["pa"]
    if old_price:
        pct = 100 * (old_price - m["p"]) / old_price
        drop = (f'<div style="color:#B34A38;font-size:12.5px;font-weight:700">'
                f'Antes {fmt(old_price)} → ahora, un {pct:.0f}% menos</div>')
    hours = f' · {m["h"]:,} h'.replace(",", ".") if m.get("h") else ""
    return f'''<div style="border:1px solid #D9DEE4;border-radius:10px;overflow:hidden;margin:12px 0;background:#fff">
<img src="{IMG}{m["img"]}.jpg" alt="{m["n"]}" style="width:100%;height:200px;object-fit:cover;display:block">
<div style="padding:13px 15px">
<div style="font-weight:800;font-size:16px;color:#14181C">{m["n"]}</div>
<div style="font-size:12.5px;color:#387E7F;font-weight:600">{m["y"]} · {m["s"]}{hours}</div>
{drop}
<div style="font-weight:800;font-size:18px;margin-top:6px;color:#14181C">{('<span style="color:#8A93A0;font-weight:400;font-size:14px;text-decoration:line-through;margin-right:6px">' + fmt(old_price) + '</span>') if old_price else ''}{fmt(m["p"])} <span style="font-weight:400;font-size:11px;color:#8A93A0">+ IVA</span></div>
<a href="https://wa.me/34606836581?text=Hola,%20me%20interesa%20la%20{urllib.parse.quote(m["n"])}" style="display:block;margin-top:10px;background:#25D366;color:#fff;text-align:center;font-weight:700;font-size:13.5px;padding:10px;border-radius:7px;text-decoration:none">Me interesa · WhatsApp</a>
</div></div>'''


def send_alert(email, nombre, drops, news):
    parts = []
    if drops:
        parts.append("<h3 style='margin:14px 0 4px;font-size:15px'>📉 Han bajado de precio</h3>"
                     + "".join(machine_card(m, old) for m, old in drops))
    if news:
        parts.append("<h3 style='margin:14px 0 4px;font-size:15px'>✨ Recién llegadas</h3>"
                     + "".join(machine_card(m) for m in news))
    html = f'''<div style="font-family:system-ui,sans-serif;font-size:14px;line-height:1.55;color:#14181C;max-width:540px">
<p>Hola{" " + nombre if nombre else ""},</p>
<p>Novedades en las máquinas que sigues:</p>
{"".join(parts)}
<p style="font-size:12px;color:#8A93A0">Recibes este aviso porque activaste las alertas de stock de Equipzilla.
Responde a este email si quieres dejar de recibirlas.</p></div>'''
    n_items = len(drops) + len(news)
    subject = ("📉 Ha bajado de precio una máquina que sigues" if drops else
               "✨ Máquina nueva que te puede encajar")
    if n_items > 1:
        subject = f"🔔 {n_items} novedades en máquinas que sigues"
    r = brevo("POST", "smtp/email", {
        "sender": {"id": 10}, "to": [{"email": email}],
        "subject": subject, "htmlContent": html, "tags": ["alerta-stock"]})
    return bool(r.get("messageId"))


def send_whatsapp(phone, drops, news):
    """Aviso por WhatsApp vía respond.io (canal WhatsApp Business).

    Si el suscriptor nunca ha escrito a nuestro número, WhatsApp puede exigir
    plantilla aprobada — se intenta el envío y, si no procede, queda el email.
    """
    token = os.environ.get("RESPONDIO_TOKEN", "")
    channel = os.environ.get("RESPONDIO_CHANNEL", "")
    phone = "".join(ch for ch in str(phone) if ch.isdigit() or ch == "+")
    if phone and not phone.startswith("+"):
        phone = "+34" + phone
    if not (token and channel and len(phone) >= 9):
        return False
    lines = ["🔔 Novedades de Equipzilla en máquinas que sigues:"]
    for m, old in drops:
        lines.append(f"📉 {m['n']}: antes {fmt(old)}, ahora {fmt(m['p'])} + IVA")
    for m in news:
        lines.append(f"✨ Nueva: {m['n']} ({m['y']}) — {fmt(m['p'])} + IVA")
    lines.append("¿Quieres fotos e informe? Responde a este mensaje.")
    ident = urllib.parse.quote(f"phone:{phone}")
    try:
        def rio(path, body):
            req = urllib.request.Request(
                f"https://api.respond.io/v2/{path}",
                data=json.dumps(body).encode(),
                headers={"Authorization": f"Bearer {token}",
                         "content-type": "application/json"}, method="POST")
            return urllib.request.urlopen(req, timeout=30)
        rio(f"contact/create_or_update/{ident}", {"phone": phone})
        rio(f"contact/{ident}/message",
            {"channelId": int(channel),
             "message": {"type": "text", "text": "\n".join(lines)}})
        return True
    except Exception:
        return False


def main():
    if not KEY:
        print("Falta BREVO_API_KEY")
        sys.exit(1)
    machines = {m["img"]: m for m in json.load(open(MACHINES))}
    if not os.path.exists(STATE):
        json.dump({k: m["p"] for k, m in machines.items()}, open(STATE, "w"))
        print("Primer run: estado guardado, sin alertas.")
        return
    prev = json.load(open(STATE))
    drops = [(m, prev[k]) for k, m in machines.items()
             if k in prev and m["p"] < prev[k]]
    news = [m for k, m in machines.items() if k not in prev]
    if not drops and not news:
        print("Sin cambios de stock — no se envía nada.")
        return
    print(f"bajadas={len(drops)} nuevas={len(news)}")

    subs = brevo("GET", f"contacts/lists/{LIST_ID}/contacts?limit=500")
    sent = 0
    for c in subs.get("contacts", []):
        at = c.get("attributes") or {}
        cat = (at.get("ALERTA_CATEGORIA") or "").strip()
        pmax = float(at.get("ALERTA_PRECIO_MAX") or 0)
        def match(m):
            if cat not in ALL_CATS and CAT_LABEL.get(m["c"], "") != cat:
                return False
            if pmax > 0 and m["p"] > pmax * 1.15:  # margen del 15%
                return False
            return True
        my_drops = [(m, old) for m, old in drops if match(m)]
        my_news = [m for m in news if match(m)]
        if not my_drops and not my_news:
            continue
        ok = send_alert(c["email"], (at.get("NOMBRE") or "").split()[0]
                        if at.get("NOMBRE") else "", my_drops, my_news)
        send_whatsapp(at.get("ALERTA_TELEFONO") or "", my_drops, my_news)
        sent += 1 if ok else 0
        time.sleep(0.4)
    print(f"alertas enviadas a {sent} suscriptores")

    if os.environ.get("TEAM_SUMMARY", "1") == "1":
        resumen = "".join(f"<li>📉 {m['n']}: {fmt(old)} → {fmt(m['p'])}</li>"
                          for m, old in drops)
        resumen += "".join(f"<li>✨ Nueva: {m['n']} ({fmt(m['p'])})</li>"
                           for m in news)
        brevo("POST", "smtp/email", {
            "sender": {"id": 10},
            "to": [{"email": e} for e in
                   ("david@equipzilla.com", "andres@equipzilla.com",
                    "maikel@equipzilla.com")],
            "subject": f"🔔 Alertas de stock enviadas a {sent} suscriptores",
            "htmlContent": f"<ul>{resumen}</ul>",
            "tags": ["alerta-stock-resumen"]})

    json.dump({k: m["p"] for k, m in machines.items()}, open(STATE, "w"))
    print("estado actualizado")


import urllib.parse  # noqa: E402  (usado en machine_card)

if __name__ == "__main__":
    main()
