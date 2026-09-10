#!/usr/bin/env python3
"""Reconstruye ~/.outbound/ desde variables de entorno.

Las sesiones nuevas (agentes) arrancan en un contenedor limpio sin ~/.outbound/.
Si las credenciales están como variables de entorno del entorno «Equipzilla»
(BREVO_KEY, SMARTLEAD_KEY, PIPEDRIVE_KEY, GOOGLE_SA_JSON, DINORANK_KEY,
GOOGLEADS_DEV_TOKEN, VERCEL_TOKEN, CRM_PASSWORD, APIFY_KEY, NOTION_TOKEN),
este script las vuelca a fichero (chmod 600) para que todos los scripts funcionen.
Se ejecuta solo al arrancar la sesión (hook SessionStart en .claude/settings.json).
"""
import os
import sys

NOMBRES = ["brevo_key", "smartlead_key", "pipedrive_key", "google_sa.json", "dinorank_key",
           "googleads_dev_token", "vercel_token", "crm_password", "apify_key", "notion_token"]
d = os.path.expanduser("~/.outbound")
os.makedirs(d, exist_ok=True)
os.chmod(d, 0o700)
hay, faltan = [], []
for n in NOMBRES:
    p = os.path.join(d, n)
    if os.path.exists(p) and open(p).read().strip():
        hay.append(n); continue
    v = os.environ.get(n.upper().replace(".", "_"), "").strip()
    if v:
        open(p, "w").write(v); os.chmod(p, 0o600); hay.append(n)
    else:
        faltan.append(n)
print("credenciales disponibles:", ", ".join(hay) or "ninguna")
if faltan:
    print("FALTAN (ni fichero ni variable de entorno):", ", ".join(faltan))
    print("Pídelas a Maikel: se añaden como variables de entorno del entorno «Equipzilla» en claude.ai/code.")
sys.exit(0)
