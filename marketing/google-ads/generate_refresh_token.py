# -*- coding: utf-8 -*-
"""Genera el GOOGLE_ADS_REFRESH_TOKEN a partir de tu client_id / client_secret.

Uso:
  1) pip install google-auth-oauthlib
  2) rellena CLIENT_ID y CLIENT_SECRET en .env  (o exportalos como variables)
  3) python generate_refresh_token.py
  4) copia el refresh token que imprime en tu .env

Abre una ventana del navegador para que autorices con tu usuario de Google Ads.
"""
import os

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    raise SystemExit("Falta dependencia. Instala:  pip install google-auth-oauthlib")

# Carga .env si existe (sin dependencias externas)
def _load_env(path=".env"):
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()

CLIENT_ID = os.environ.get("GOOGLE_ADS_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("GOOGLE_ADS_CLIENT_SECRET", "").strip()
SCOPES = ["https://www.googleapis.com/auth/adwords"]

if not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit("Define GOOGLE_ADS_CLIENT_ID y GOOGLE_ADS_CLIENT_SECRET en .env")

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}

flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
# Intenta abrir navegador local; si no hay entorno grafico usa consola.
try:
    creds = flow.run_local_server(port=0, prompt="consent")
except Exception:
    creds = flow.run_console()

print("\n================ COPIA ESTO EN TU .env ================")
print(f"GOOGLE_ADS_REFRESH_TOKEN={creds.refresh_token}")
print("=======================================================")
