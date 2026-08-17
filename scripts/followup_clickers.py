#!/usr/bin/env python3
"""Seguimiento personalizado a los clickers de las campañas de compraventa.

Lee leads/clickers_unificados.json (export de Brevo con atribución por máquina)
y envía a cada clicker un email corto firmado por David ofreciendo informe,
fotos y vídeo de la(s) máquina(s) que miró + alerta de precio con un clic.

Uso:
  BREVO_API_KEY=... python3 scripts/followup_clickers.py            # DRY RUN (no envía)
  BREVO_API_KEY=... SEND=1 python3 scripts/followup_clickers.py     # envía de verdad
  BREVO_API_KEY=... EXAMPLE_TO=maikel@equipzilla.com python3 ...    # 1 ejemplo a esa dirección
"""
import json
import os
import sys
import time
import urllib.request

KEY = os.environ.get("BREVO_API_KEY", "")
SEND = os.environ.get("SEND") == "1"
EXAMPLE_TO = os.environ.get("EXAMPLE_TO", "")
EXCLUDE = {"maikel@equipzilla.com", "zilia@equipzilla.com"}
DATA = os.path.join(os.path.dirname(__file__), "..", "leads", "clickers_unificados.json")
ONECLICK = "https://equipzilla-quiz.vercel.app/api/subscribe?email={email}&categoria=todas"

def send(email, html, subject):
    req = urllib.request.Request("https://api.brevo.com/v3/smtp/email",
        data=json.dumps({
            "sender": {"id": 10, "name": "David de Equipzilla"},
            "replyTo": {"email": "david@equipzilla.com", "name": "David Devis"},
            "to": [{"email": email}],
            "subject": subject,
            "htmlContent": html,
            "tags": ["followup-clicker"],
        }).encode(),
        headers={"api-key": KEY, "content-type": "application/json"})
    r = urllib.request.urlopen(req, timeout=60)
    return r.status < 300

def build(email, maquinas):
    if len(maquinas) == 1:
        que = f"la <b>{maquinas[0]}</b>"
        subject = f"¿Te envío el informe de la {maquinas[0]}?"
    elif maquinas:
        que = "las máquinas que estuviste mirando (" + ", ".join(f"<b>{m}</b>" for m in maquinas) + ")"
        subject = "¿Te envío informe de las máquinas que estuviste mirando?"
    else:
        que = "las máquinas de ocasión que te enviamos"
        subject = "¿Buscas máquina? Te ayudo a elegir"
    alerta = ONECLICK.format(email=urllib.parse.quote(email))
    html = f"""<div style="font-family:system-ui,sans-serif;font-size:14.5px;line-height:1.65;color:#14181C;max-width:540px">
<p>Hola,</p>
<p>Soy David, de Equipzilla. Vi que estuviste mirando {que} de nuestro último envío de ocasión.</p>
<p>Si te encaja, te envío <b>fotos adicionales, vídeo en funcionamiento y el informe de la unidad</b> — sin compromiso. Y si el momento no es ahora, dos opciones útiles:</p>
<ul style="margin:8px 0;padding-left:20px">
<li><a href="{alerta}" style="color:#387E7F;font-weight:600">Activa la alerta de precio (1 clic)</a> y te aviso solo si baja o entra una similar.</li>
<li><a href="https://equipzilla-quiz.vercel.app" style="color:#387E7F;font-weight:600">Prueba nuestro asesor de compra</a>: cuéntale el trabajo y te dice qué máquina encaja (1 minuto).</li>
</ul>
<p>¿Hablamos? Respóndeme a este email o escríbeme al <b>606 836 581</b> (WhatsApp).</p>
<p>Un saludo,<br><b>David Devis</b><br>
<span style="color:#667085;font-size:12.5px">Equipzilla · Director de Desarrollo de Negocio · 911 238 750</span></p></div>"""
    return subject, html

def main():
    if not KEY:
        sys.exit("Falta BREVO_API_KEY")
    data = json.load(open(DATA))
    targets = {e: v for e, v in data.items() if e not in EXCLUDE}
    if EXAMPLE_TO:
        ricos = sorted(targets.items(), key=lambda kv: -len(kv[1]["maquinas"]))
        em, v = ricos[0]
        subject, html = build(em, v["maquinas"])
        send(EXAMPLE_TO, html, "[EJEMPLO seguimiento clicker] " + subject)
        print(f"ejemplo enviado a {EXAMPLE_TO} (basado en {em})")
        return
    n = 0
    for em, v in sorted(targets.items()):
        subject, html = build(em, v["maquinas"])
        if SEND:
            ok = send(em, html, subject)
            n += 1 if ok else 0
            time.sleep(0.5)
            print(("✓" if ok else "✗"), em)
        else:
            print("DRY:", em, "->", subject)
    print(("enviados" if SEND else "pendientes (dry run)"), len(targets) if not SEND else n)

import urllib.parse  # noqa: E402

if __name__ == "__main__":
    main()
