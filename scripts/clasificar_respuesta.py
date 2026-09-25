#!/usr/bin/env python3
"""Marca en Smartlead la categoría de un lead que ha contestado.

El ciclo diario pide clasificar cada respuesta (Interesado / No ahora / No es su
área / Baja / Rebote / Automática). `informe_respuestas.py` lee y puntúa las
respuestas, pero nunca las escribía de vuelta en Smartlead: la categoría se
quedaba vacía y al día siguiente no había forma de saber qué se había mirado ya.

Categorías de Smartlead (las que usamos):
    1 Interested · 2 Meeting Request · 3 Not Interested · 4 Do Not Contact
    5 Information Request · 6 Out Of Office · 7 Wrong Person
    8 Unsubscribed · 9 Sender Originated Bounce

Uso:
    python3 scripts/clasificar_respuesta.py 3789100 info@empresa.com 6
    python3 scripts/clasificar_respuesta.py 3789100 info@empresa.com 6 --reanudar
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

NAVEGADOR = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
NOMBRES = {1: "Interesado", 2: "Pide reunión", 3: "No interesado",
           4: "No contactar", 5: "Pide información", 6: "Fuera de la oficina",
           7: "No es su área", 8: "Baja", 9: "Rebote"}


def clave(nombre):
    ruta = os.path.expanduser(f"~/.outbound/{nombre}")
    if os.path.exists(ruta):
        return open(ruta).read().strip()
    valor = os.environ.get(nombre.upper(), "")
    if not valor:
        sys.exit(f"falta la credencial {nombre}")
    return valor


def sl(ruta, metodo="GET", cuerpo=None):
    sep = "&" if "?" in ruta else "?"
    url = ("https://server.smartlead.ai/api/v1" + ruta + sep
           + "api_key=" + clave("smartlead_key"))
    req = urllib.request.Request(url, method=metodo, headers={
        "accept": "application/json", "content-type": "application/json",
        "user-agent": NAVEGADOR, "referer": "https://app.smartlead.ai/"},
        data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            b = r.read()
            return json.loads(b) if b.strip() else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read()[:300].decode("utf8", "ignore")}


def buscar(campana, correo):
    """Devuelve el id del lead dentro de la campaña, o None."""
    r = sl("/leads/?email=" + urllib.parse.quote(correo))
    lead_id = (r or {}).get("id")
    if lead_id:
        return lead_id
    off = 0
    while True:
        r = sl(f"/campaigns/{campana}/leads?offset={off}&limit=100")
        datos = r.get("data") or []
        for fila in datos:
            l = fila.get("lead") or fila
            if (l.get("email") or "").lower() == correo.lower():
                return l.get("id")
        if len(datos) < 100:
            return None
        off += 100


def clasificar(campana, correo, categoria, reanudar=False):
    lead_id = buscar(campana, correo)
    if not lead_id:
        sys.exit(f"{correo} no está en la campaña {campana}")
    r = sl(f"/campaigns/{campana}/leads/{lead_id}/category", "POST",
           {"category_id": int(categoria), "pause_lead": False})
    print(f"{correo} · lead {lead_id} · {NOMBRES.get(int(categoria), categoria)} · {r}")
    if reanudar:
        # Smartlead para el lead solo al contestar. Para una respuesta automática
        # (fuera de la oficina) hay que volver a arrancarlo o la secuencia muere ahí.
        print("   reanudar:", sl(f"/campaigns/{campana}/leads/{lead_id}/resume", "POST", {}))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    clasificar(sys.argv[1], sys.argv[2], sys.argv[3], "--reanudar" in sys.argv)
