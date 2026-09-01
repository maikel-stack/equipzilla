#!/usr/bin/env python3
"""Carga leads en la campaña de frío de Smartlead y ajusta el ritmo.

Uso:
    python3 scripts/cargar_frio.py estado           # qué hay ahora
    python3 scripts/cargar_frio.py cargar [csv]     # sube leads nuevos
    python3 scripts/cargar_frio.py ritmo 40 25      # leads/día y tope por buzón
    python3 scripts/cargar_frio.py arrancar         # reanuda la campaña

Sobre el ritmo: el playbook fija el techo en 30–40 correos/día por buzón.
Con 10 buzones eso son 300–400 diarios, pero NO se salta de golpe: pasar de
16 a 350 en un día es la forma más rápida de quemar los dominios. Se sube
por escalones semanales.
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

CLAVE = open(os.path.expanduser("~/.outbound/smartlead_key")).read().strip()
CAMPANA = 3789100
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_POR_DEFECTO = os.path.join(RAIZ, "leads", "frio_espana.csv")

# Cloudflare devuelve 403 (error 1010) a toda petición sin firma de navegador.
CABECERAS = {
    "accept": "application/json",
    "content-type": "application/json",
    "user-agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/128.0.0.0 Safari/537.36"),
    "referer": "https://app.smartlead.ai/",
}


def sl(ruta, metodo="GET", cuerpo=None):
    sep = "&" if "?" in ruta else "?"
    url = "https://server.smartlead.ai/api/v1" + ruta + sep + "api_key=" + CLAVE
    req = urllib.request.Request(
        url, method=metodo, headers=CABECERAS,
        data=json.dumps(cuerpo).encode() if cuerpo else None)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            b = r.read()
            return json.loads(b) if b else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:300]}


def estado():
    c = sl(f"/campaigns/{CAMPANA}")
    a = sl(f"/campaigns/{CAMPANA}/analytics")
    st = (a.get("campaign_lead_stats") or {})
    print(f"campaña : {c.get('name')}")
    print(f"estado  : {c.get('status')}")
    print(f"leads   : {st.get('total', 0)} cargados · {st.get('inprogress', 0)} en curso "
          f"· {st.get('completed', 0)} terminados · {st.get('blocked', 0)} bloqueados")
    print(f"enviados: {a.get('sent_count', 0)} · respuestas {a.get('reply_count', 0)} "
          f"· clics {a.get('click_count', 0)} · rebotes {a.get('bounce_count', 0)}")
    print(f"ritmo   : {c.get('max_leads_per_day')} leads nuevos/día")
    cuentas = sl(f"/campaigns/{CAMPANA}/email-accounts")
    if isinstance(cuentas, list):
        tope = sum(x.get("message_per_day") or 0 for x in cuentas)
        print(f"buzones : {len(cuentas)} · capacidad {tope} correos/día")


def cargar(ruta_csv):
    with open(ruta_csv) as f:
        filas = list(csv.DictReader(f))
    print(f"{len(filas)} leads en {ruta_csv}")

    leads = []
    for r in filas:
        email = (r.get("email") or "").strip().lower()
        if not email or "@" not in email:
            continue
        empresa = (r.get("empresa") or "").strip()
        ciudad = (r.get("ciudad") or r.get("provincia") or "").strip()
        leads.append({
            "email": email,
            "company_name": empresa,
            "phone_number": (r.get("telefono") or "").strip(),
            "website": (r.get("web") or "").strip(),
            "location": ciudad,
            # El paso 1 abre con {{saludo}} y nombra {{ciudad}}: sin nombre de
            # pila, un saludo genérico de empresa es lo único honesto.
            "custom_fields": {"saludo": "Hola", "ciudad": ciudad or "vuestra zona"},
        })

    print(f"{len(leads)} con email válido · subiendo de 100 en 100")
    subidos = duplicados = 0
    for i in range(0, len(leads), 100):
        lote = leads[i:i + 100]
        r = sl(f"/campaigns/{CAMPANA}/leads", "POST", {
            "lead_list": lote,
            "settings": {
                "ignore_global_block_list": False,
                "ignore_unsubscribe_list": False,
                "ignore_duplicate_leads_in_other_campaign": False,
            },
        })
        if "_error" in r:
            print(f"  lote {i // 100 + 1}: ERROR {r['_error']} {r['_body'][:160]}")
            continue
        subidos += r.get("upload_count", 0)
        duplicados += r.get("already_added_to_campaign", 0)
        print(f"  lote {i // 100 + 1}: +{r.get('upload_count', 0)} "
              f"({r.get('already_added_to_campaign', 0)} ya estaban)")
        time.sleep(1)
    print(f"\nTOTAL subidos {subidos} · duplicados {duplicados}")


def ritmo(leads_dia, por_buzon):
    # El tope de leads nuevos por día vive en el endpoint de /schedule
    # (max_new_leads_per_day); /settings rechaza la clave con un 400.
    r = sl(f"/campaigns/{CAMPANA}/schedule", "POST", {
        "timezone": "Europe/Madrid",
        "days_of_the_week": [1, 2, 3, 4, 5],
        "start_hour": "08:30", "end_hour": "17:30",
        "min_time_btw_emails": 25,
        "max_new_leads_per_day": int(leads_dia),
    })
    print(f"leads nuevos/día -> {leads_dia}: {'OK' if '_error' not in r else r}")
    cuentas = sl(f"/campaigns/{CAMPANA}/email-accounts")
    if not isinstance(cuentas, list):
        print("no pude leer los buzones:", cuentas)
        return
    for c in cuentas:
        x = sl(f"/email-accounts/{c['id']}", "POST",
               {"max_email_per_day": int(por_buzon)})
        print(f"  {c.get('from_email')} -> {por_buzon}/día "
              f"{'OK' if '_error' not in x else x}")
    print(f"\ncapacidad total: {len(cuentas) * int(por_buzon)} correos/día")


def arrancar():
    r = sl(f"/campaigns/{CAMPANA}/status", "POST", {"status": "START"})
    print("arrancar:", "OK" if "_error" not in r else r)
    print("estado ahora:", sl(f"/campaigns/{CAMPANA}").get("status"))


if __name__ == "__main__":
    orden = sys.argv[1] if len(sys.argv) > 1 else "estado"
    if orden == "cargar":
        cargar(sys.argv[2] if len(sys.argv) > 2 else CSV_POR_DEFECTO)
    elif orden == "ritmo":
        ritmo(sys.argv[2], sys.argv[3])
    elif orden == "arrancar":
        arrancar()
    else:
        estado()
