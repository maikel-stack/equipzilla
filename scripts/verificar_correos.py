#!/usr/bin/env python3
"""Verifica que los dominios de una lista aceptan correo, antes de enviarles.

Nace del 18/09: la campaña de obra rebotó un 9,4 % y hubo que pausarla. Los
correos salen de rastrear webs y nadie comprueba que el dominio siga vivo. Un
dominio sin registro MX no acepta correo: ese envío es un rebote duro seguro, y
los rebotes duros son lo que quema la reputación de los buzones.

No hace falta contratar un verificador: la consulta de MX es gratis y se hace
por DNS sobre HTTPS, que además pasa por el proxy del contenedor.

Qué NO comprueba: si el buzón concreto existe. Eso exige hablar SMTP con el
servidor y los proveedores serios lo bloquean. Aun así, el MX se lleva por
delante la mayor parte de los rebotes duros.

Uso:
    python3 scripts/verificar_correos.py csv leads/tanda2_obra.csv
    python3 scripts/verificar_correos.py campana 3962539          # lee de Smartlead
    python3 scripts/verificar_correos.py campana 3962539 --pausar # y para los malos
"""
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

NAVEGADOR = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
# Proveedores gratuitos: siempre tienen MX, no hace falta preguntar.
LIBRES = {"gmail.com", "hotmail.com", "hotmail.es", "yahoo.es", "yahoo.com",
          "outlook.com", "outlook.es", "live.com", "icloud.com", "telefonica.net",
          "movistar.es", "terra.es", "ono.com"}
_cache = {}

# Fallos del rastreo que se detectan sin preguntar a nadie, vistos en los
# rebotes del 18 y el 21/09:
#   n@tlmtransportes.com, a@perezgarran.es  -> el rastreador cortó el correo
#   web@ferrovial.como                      -> dominio mal tecleado en la web
import re  # noqa: E402
TLD_BUENO = re.compile(
    r"\.(com|es|net|org|eu|cat|gal|eus|info|biz|io|co|pt|fr|it|de|solar|energy|"
    r"group|tech|online|shop|site|web|pro|sl|barcelona|madrid|quest|"
    r"services|company|construction|com\.es)$", re.I)
# Dominios de país fuera de nuestro mercado: no son un error, pero una empresa
# que compra máquina en España no suele tener su correo en .cl o .cn.
FUERA = re.compile(r"\.(cl|cn|ru|in|br|mx|ar|us|uk|ws|tk|ml)$", re.I)


def defectuoso(email):
    """Motivo por el que el correo no sirve para enviar, o cadena vacía."""
    if "@" not in email:
        return "sin arroba"
    local, dom = email.rsplit("@", 1)
    if len(local) < 3:
        return "buzón de 1-2 letras (rastreo cortado)"
    if FUERA.search(dom):
        return f"dominio fuera de mercado (.{dom.rsplit('.', 1)[-1]})"
    if not TLD_BUENO.search(dom):
        return f"terminación rara del dominio (.{dom.rsplit('.', 1)[-1]})"
    return ""


def clave(nombre):
    p = os.path.expanduser(f"~/.outbound/{nombre}")
    if os.path.exists(p):
        return open(p).read().strip()
    return os.environ.get(nombre.upper(), "")


def tiene_mx(dominio):
    """True si el dominio publica MX. Ante la duda (fallo de red), True: más
    vale enviar de más que descartar a un cliente bueno por un timeout."""
    if dominio in _cache:
        return _cache[dominio]
    if dominio in LIBRES:
        _cache[dominio] = True
        return True
    ok = True
    for intento in range(2):
        try:
            u = f"https://dns.google/resolve?name={urllib.parse.quote(dominio)}&type=MX"
            req = urllib.request.Request(u, headers={"accept": "application/dns-json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                d = json.loads(r.read())
            # Status 3 = el dominio no existe. Sin Answer de tipo 15 = sin MX.
            ok = d.get("Status") == 0 and any(
                a.get("type") == 15 for a in (d.get("Answer") or []))
            break
        except Exception:
            if intento:
                ok = True          # no pudimos comprobarlo: no lo descartamos
    _cache[dominio] = ok
    return ok


def verificar(emails, hilos=16):
    doms = sorted({e.split("@")[-1].lower() for e in emails if "@" in e})
    print(f"{len(emails)} correos · {len(doms)} dominios distintos")
    with ThreadPoolExecutor(max_workers=hilos) as p:
        list(p.map(tiene_mx, doms))
    malos, motivos = [], {}
    for e in emails:
        m = defectuoso(e)
        if not m and "@" in e and not _cache.get(e.split("@")[-1].lower(), True):
            m = "el dominio no acepta correo (sin MX)"
        if m:
            malos.append(e)
            motivos[e] = m
    print(f"descartables: {len(malos)} · {100*len(malos)/max(len(emails),1):.1f} %")
    for m in sorted({v for v in motivos.values()}):
        print(f"   {sum(1 for x in motivos.values() if x == m):>3} · {m}")
    verificar.motivos = motivos
    return malos


def sl(ruta, metodo="GET", cuerpo=None):
    sep = "&" if "?" in ruta else "?"
    url = "https://server.smartlead.ai/api/v1" + ruta + sep + "api_key=" + clave("smartlead_key")
    req = urllib.request.Request(url, method=metodo, headers={
        "accept": "application/json", "content-type": "application/json",
        "user-agent": NAVEGADOR, "referer": "https://app.smartlead.ai/"},
        data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            b = r.read()
            return json.loads(b) if b.strip() else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code}


def de_campana(cid, pausar=False):
    leads, off = [], 0
    while True:
        r = sl(f"/campaigns/{cid}/leads?offset={off}&limit=100")
        d = r.get("data") or []
        leads += [x.get("lead") or x for x in d]
        if len(d) < 100:
            break
        off += 100
    malos = set(verificar([(l.get("email") or "").lower() for l in leads]))
    for l in leads:
        if (l.get("email") or "").lower() in malos:
            print(f"   {'PARADO ' if pausar else 'sin MX '} "
                  f"{(l.get('company_name') or '')[:34]:<34} {l.get('email')}")
            if pausar:
                sl(f"/campaigns/{cid}/leads/{l['id']}/pause", "POST", {})
    return malos


if __name__ == "__main__":
    orden = sys.argv[1] if len(sys.argv) > 1 else "csv"
    if orden == "campana":
        de_campana(int(sys.argv[2]), "--pausar" in sys.argv)
    else:
        ruta = sys.argv[2]
        filas = list(csv.DictReader(open(ruta)))
        malos = verificar([f["email"].lower() for f in filas])
        for f in filas:
            if f["email"].lower() in malos:
                print(f"   {f['empresa'][:34]:<34} {f['email']}")
