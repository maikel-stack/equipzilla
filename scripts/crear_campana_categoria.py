#!/usr/bin/env python3
"""Crea en Smartlead una campaña de frío por categoría de máquina.

Nace de la observación de Andrés (15/09): todo lo que preguntan es excavación
porque todo lo que mandamos es excavación. El 61 % de las unidades del stock no
son minis ni excavadoras y no tenían ni un email saliendo.

Cada campaña lleva su lista (un sector que USA esa máquina) y su secuencia de
3 pasos con máquinas reales de `data/machines.json`, precio cerrado, horas y
garantía. Solo demanda: nunca «compramos tu máquina» (Maikel, 14/09).

Uso:
    python3 scripts/crear_campana_categoria.py prueba            # valida y no toca nada
    python3 scripts/crear_campana_categoria.py crear obra        # crea en pausa
    python3 scripts/crear_campana_categoria.py crear logistica
    python3 scripts/crear_campana_categoria.py arrancar <id>     # la pone a enviar

La campaña se crea SIEMPRE en pausa. Arrancarla es un paso aparte y explícito.
"""
import csv
import json
import os
import sys
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAVE = open(os.path.expanduser("~/.outbound/smartlead_key")).read().strip()
BASE = "https://server.smartlead.ai/api/v1"
CABECERAS = {
    "accept": "application/json", "content-type": "application/json",
    "user-agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"),
    "referer": "https://app.smartlead.ai/",
}
FIRMA = ("<p>Un saludo,<br>David Devis<br>Director de Desarrollo de Negocio "
         "&middot; Equipzilla<br>606 836 581 (llamada o WhatsApp) "
         "&middot; equipzilla.com</p>")

CAMPANAS = {
    "obra": dict(
        nombre="Compraventa Frio - Obra (minis y excavadoras) - 2026-09",
        csv="leads/tanda2_obra.csv",
        pasos=[
            dict(dias=0, asunto="una Kubota de 3 t revisada para {{company_name}}?", cuerpo=(
                "<p>{{saludo}}:</p>"
                "<p>Vi que en {{ciudad}} trabajáis en obra y movimiento de tierras, así que voy al grano.</p>"
                "<p>Tengo ahora mismo dos miniexcavadoras revisadas que suelen encajar con empresas como {{company_name}}:</p>"
                "<p>&bull; Kubota KX 030-4 GL &middot; 3 t &middot; 2023 &middot; 700 h &middot; 35.900 € + IVA<br>"
                "&bull; Doosan DX 35 Z-7 &middot; 3,5 t &middot; 2023 &middot; 40 h &middot; 45.500 € + IVA</p>"
                "<p>Las dos con inspección y prueba presencial, horas certificadas y opción de garantía. "
                "Frente a nueva, entre un 30 y un 40 % menos.</p>"
                "<p>Si buscáis otro tamaño, tenemos de 0,8 a 23 t. Decidme cuál os encaja y os digo qué hay.</p>"
                "<p>¿Os encaja alguna?</p>")),
            dict(dias=4, asunto="", cuerpo=(
                "<p>Hola, os dejo algunas más por si el tamaño no era ese:</p>"
                "<p>&bull; Kubota KX 016-4 &middot; 0,8 t &middot; 2024 &middot; 250 h &middot; 18.900 € + IVA<br>"
                "&bull; Kubota KX 080-4 &middot; 8 t &middot; 2022 &middot; 2.150 h &middot; 56.900 € + IVA<br>"
                "&bull; Doosan DX 140 LCR-5 &middot; 14 t &middot; 2020 &middot; 2.900 h &middot; 87.500 € + IVA</p>"
                "<p>Y para el resto de la obra: dumper Wacker Neuson 1601 (2021 &middot; 900 h &middot; 18.500 € + IVA), "
                "minicargadora Bobcat S70 (2023 &middot; 350 h &middot; 23.500 € + IVA), telescópico Merlo P 27.6 Plus "
                "(2023 &middot; 1.000 h &middot; 58.500 € + IVA) y plataforma articulada JLG 450AJ de 16 m "
                "(2013 &middot; 19.500 € + IVA).</p>"
                "<p>Fotos e informe de cada una en equipzilla.com/compra. Opción de garantía y financiación.</p>"
                "<p>¿Os preparo una selección con lo que os encaje?</p>")),
            dict(dias=4, asunto="", cuerpo=(
                "<p>Hola, no quiero saturaros, así que cierro el hilo por ahora.</p>"
                "<p>Si os viene bien, os aviso solo cuando entre una máquina que encaje con lo vuestro "
                "(tipo y presupuesto), sin más correos de por medio. ¿Os apunto? Con un «sí» me vale.</p>"
                "<p>Y si hoy hay algo concreto, la Kubota KX 030-4 de 3 t (35.900 € + IVA) es la que más sale. "
                "Me tenéis en el 606 836 581.</p>")),
        ]),
    "logistica": dict(
        nombre="Compraventa Frio - Logistica (carretillas) - 2026-09",
        csv="leads/tanda2_logistica.csv",
        pasos=[
            dict(dias=0, asunto="una carretilla eléctrica de 2,5 t para {{company_name}}?", cuerpo=(
                "<p>{{saludo}}:</p>"
                "<p>Vi que en {{ciudad}} movéis mercancía y almacén, y por eso os escribo directamente.</p>"
                "<p>Tengo dos carretillas eléctricas revisadas, listas para entrar a trabajar en {{company_name}}:</p>"
                "<p>&bull; Clark EPX25 &middot; 2,5 t &middot; eléctrica &middot; 2011 &middot; 801 h &middot; 7.000 € + IVA<br>"
                "&bull; Yale ERP16VT &middot; 1,6 t &middot; eléctrica &middot; 2018 &middot; 6.938 h &middot; 7.800 € + IVA</p>"
                "<p>Con inspección y prueba presencial, horas certificadas y opción de garantía. "
                "Frente a nueva, entre un 30 y un 40 % menos.</p>"
                "<p>Si necesitáis retráctil, GLP o diésel, también tengo. ¿Os encaja alguna?</p>")),
            dict(dias=4, asunto="", cuerpo=(
                "<p>Hola, os amplío por si buscabais otro tipo:</p>"
                "<p>&bull; Hyster R1.4 &middot; retráctil &middot; 1,4 t &middot; 8,5 m &middot; 2019 &middot; 3.283 h &middot; 6.200 € + IVA<br>"
                "&bull; Hyster H2.5FT &middot; 2,5 t &middot; GLP &middot; 2019 &middot; 11.503 h &middot; 15.000 € + IVA<br>"
                "&bull; Hyster H3.0FT &middot; 3 t &middot; mástil 5,6 m &middot; 2021 &middot; 13.132 h &middot; 16.000 € + IVA<br>"
                "&bull; Jungheinrich DFG 320s &middot; 2 t &middot; diésel &middot; 2017 &middot; 12.360 h &middot; 12.400 € + IVA</p>"
                "<p>Y si en el almacén trabajáis en altura, tengo una tijera eléctrica Haulotte Compact 10 de 10 m "
                "(2011 &middot; 1.116 h &middot; 5.500 € + IVA).</p>"
                "<p>Fotos e informe en equipzilla.com/compra. Entrega en toda España y financiación.</p>"
                "<p>¿Os preparo una selección?</p>")),
            dict(dias=4, asunto="", cuerpo=(
                "<p>Hola, no quiero saturaros, así que cierro el hilo por ahora.</p>"
                "<p>Si os viene bien, os aviso solo cuando entre una carretilla que encaje con lo vuestro "
                "(tonelaje, eléctrica o térmica, presupuesto), sin más correos. ¿Os apunto? Con un «sí» me vale.</p>"
                "<p>Si hoy hay algo concreto, la Clark EPX25 de 2,5 t eléctrica (7.000 € + IVA) es la mejor "
                "relación precio-horas. Me tenéis en el 606 836 581.</p>")),
        ]),
}


def sl(ruta, metodo="GET", cuerpo=None, espera=120):
    url = BASE + ruta + ("&" if "?" in ruta else "?") + "api_key=" + CLAVE
    req = urllib.request.Request(
        url, method=metodo, headers=CABECERAS,
        data=json.dumps(cuerpo).encode() if cuerpo else None)
    try:
        with urllib.request.urlopen(req, timeout=espera) as r:
            b = r.read()
            return json.loads(b) if b else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:300]}


def leer_leads(ruta):
    leads = []
    for r in csv.DictReader(open(os.path.join(RAIZ, ruta))):
        email = (r.get("email") or "").strip().lower()
        if not email or "@" not in email:
            continue
        ciudad = (r.get("ciudad") or "").strip()
        leads.append({
            "email": email,
            "company_name": (r.get("empresa") or "").strip()[:60],
            "phone_number": (r.get("telefono") or "").strip(),
            "website": (r.get("web") or "").strip(),
            "location": ciudad,
            "custom_fields": {"saludo": "Hola",
                              "ciudad": ciudad or "vuestra zona"},
        })
    return leads


def secuencia(clave):
    """Los 3 pasos con la firma de David pegada al final de cada uno."""
    return [{"seq_number": i + 1,
             "seq_delay_details": {"delayInDays": p["dias"]},
             "seq_variants": [{"subject": p["asunto"],
                               "email_body": p["cuerpo"] + FIRMA,
                               "variant_label": "A"}]}
            for i, p in enumerate(CAMPANAS[clave]["pasos"])]


def resecuencia(clave, cid):
    """Reescribe la secuencia de una campaña ya creada (p. ej. para corregir
    un texto). Sustituye los pasos existentes."""
    print(sl(f"/campaigns/{cid}/sequences", "POST", {"sequences": secuencia(clave)}))


def prueba():
    for clave, c in CAMPANAS.items():
        leads = leer_leads(c["csv"])
        print(f"\n=== {clave}: {c['nombre']}")
        print(f"    {len(leads)} leads · {len(c['pasos'])} pasos")
        for p in c["pasos"]:
            print(f"    día +{p['dias']:<2} asunto={p['asunto'] or '(mismo hilo)'!r} "
                  f"· {len(p['cuerpo'])} car. · links: {'sí' if 'http' in p['cuerpo'] or 'equipzilla.com/' in p['cuerpo'] else 'no'}")
        print(f"    ejemplo de lead: {leads[0]['company_name']} · {leads[0]['email']} "
              f"· {leads[0]['custom_fields']['ciudad']}")
    cuentas = sl("/email-accounts/?offset=0&limit=100")
    print(f"\nbuzones disponibles en la cuenta: "
          f"{len(cuentas) if isinstance(cuentas, list) else cuentas}")


def crear(clave, leads_dia=25):
    c = CAMPANAS[clave]
    r = sl("/campaigns/create", "POST", {"name": c["nombre"], "client_id": None})
    cid = r.get("id")
    if not cid:
        print("no se pudo crear:", r)
        return
    print(f"campaña creada: {cid} · {c['nombre']}")

    print("  secuencia:", sl(f"/campaigns/{cid}/sequences", "POST",
                             {"sequences": secuencia(clave)}))

    # Los mismos 10 buzones calentados de la campaña de Madrid. No se añade
    # capacidad: se reparte la que ya hay, que es lo seguro para el dominio.
    cuentas = sl("/campaigns/3789100/email-accounts")
    ids = [x["id"] for x in cuentas] if isinstance(cuentas, list) else []
    print("  buzones:", sl(f"/campaigns/{cid}/email-accounts", "POST",
                           {"email_account_ids": ids}), f"({len(ids)})")

    print("  horario:", sl(f"/campaigns/{cid}/schedule", "POST", {
        "timezone": "Europe/Madrid", "days_of_the_week": [1, 2, 3, 4, 5],
        "start_hour": "08:30", "end_hour": "17:30",
        "min_time_btw_emails": 15, "max_new_leads_per_day": leads_dia}))

    print("  ajustes:", sl(f"/campaigns/{cid}/settings", "POST", {
        "track_settings": ["DONT_EMAIL_OPEN"],
        "stop_lead_settings": "REPLY_TO_AN_EMAIL",
        "unsubscribe_text": "", "send_as_plain_text": False,
        "follow_up_percentage": 40, "enable_ai_esp_matching": True}))

    leads = leer_leads(c["csv"])
    subidos = 0
    for i in range(0, len(leads), 100):
        r = sl(f"/campaigns/{cid}/leads", "POST", {
            "lead_list": leads[i:i + 100],
            "settings": {"ignore_global_block_list": False,
                         "ignore_unsubscribe_list": False,
                         "ignore_duplicate_leads_in_other_campaign": False}})
        subidos += r.get("upload_count", 0)
        print(f"  lote {i // 100 + 1}: +{r.get('upload_count', 0)} "
              f"({r.get('already_added_to_campaign', 0)} duplicados)"
              + (f" ERROR {r.get('_error')} {r.get('_body','')}" if "_error" in r else ""))
    print(f"  {subidos} leads cargados · campaña EN PAUSA")
    print(f"  para arrancarla: python3 scripts/crear_campana_categoria.py arrancar {cid}")
    return cid


def arrancar(cid):
    print("arrancar:", sl(f"/campaigns/{cid}/status", "POST", {"status": "START"}))
    print("estado:", sl(f"/campaigns/{cid}").get("status"))


if __name__ == "__main__":
    orden = sys.argv[1] if len(sys.argv) > 1 else "prueba"
    if orden == "crear":
        crear(sys.argv[2])
    elif orden == "resecuencia":
        resecuencia(sys.argv[2], sys.argv[3])
    elif orden == "arrancar":
        arrancar(sys.argv[2])
    else:
        prueba()
