#!/usr/bin/env python3
"""Crea en Brevo, como BORRADOR, una campaña a partir de un HTML de campanas/
y envía el test interno. Nunca programa ni envía a clientes: eso lo hace una
persona desde Brevo (o con --enviar, solo tras el «mándala» de Maikel).

Uso:
  python3 scripts/brevo_campana.py --grupo minis --listas 39,43,34 \
      --test maikel@equipzilla.com
  python3 scripts/brevo_campana.py --grupo minis --listas 39,43,34 --solo-ver   # no toca Brevo

Reglas fijas (docs/PLAYBOOK-ABM-CAMPANAS.md): remitente id 10, replyTo explícito
a clientes@equipzilla.com, lista 34 siempre incluida. El asunto sale del grupo
en scripts/gen_lanzamiento.py; el HTML de campanas/lanzamiento-<grupo>.html.
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_lanzamiento import GRUPOS, SALIDA  # noqa: E402

API = "https://api.brevo.com/v3"
COPIA_EQUIPO = 34


def clave():
    v = os.environ.get("BREVO_API_KEY") or os.environ.get("BREVO_KEY")
    if v:
        return v.strip()
    ruta = os.path.expanduser("~/.outbound/brevo_key")
    if not os.path.exists(ruta):
        sys.exit("Falta brevo_key (~/.outbound/brevo_key o BREVO_API_KEY)")
    return open(ruta).read().strip()


def brevo(ruta, metodo="GET", cuerpo=None):
    req = urllib.request.Request(API + ruta, data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
                                 headers={"api-key": clave(), "accept": "application/json",
                                          "content-type": "application/json"}, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit("Brevo %s %s: %s" % (e.code, ruta, e.read().decode()[:300]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grupo", required=True, help="clave de GRUPOS en gen_lanzamiento.py")
    ap.add_argument("--listas", required=True, help="ids de lista separados por coma (la 34 se añade sola)")
    ap.add_argument("--test", default="", help="emails de prueba separados por coma")
    ap.add_argument("--nombre", default="", help="nombre interno de la campaña")
    ap.add_argument("--solo-ver", action="store_true", help="imprime lo que haría y no toca Brevo")
    ap.add_argument("--enviar", default="", help="SOLO tras el «mándala» de Maikel: id de campaña a enviar ahora")
    a = ap.parse_args()

    if a.enviar:
        if input("¿Maikel ha dicho «mándala» para la campaña %s? (escribe MANDALA) " % a.enviar) != "MANDALA":
            sys.exit("Sin OK: no se envía.")
        print(brevo("/emailCampaigns/%s/sendNow" % a.enviar, "POST", {}))
        return

    g = GRUPOS[a.grupo]
    html = open(os.path.join(SALIDA, "lanzamiento-%s.html" % a.grupo)).read()
    listas = sorted({int(x) for x in a.listas.split(",") if x.strip()} | {COPIA_EQUIPO})
    nombre = a.nombre or "Lanzamiento · %s · %d unidades · %s" % (
        a.grupo, len(g["maquinas"]), datetime.date.today().isoformat())
    cuerpo = {
        "name": nombre,
        "subject": g["asunto"],
        "sender": {"id": 10},
        "replyTo": "clientes@equipzilla.com",
        "htmlContent": html,
        "recipients": {"listIds": listas},
        "inlineImageActivation": False,
    }
    tam = {}
    for L in listas:
        d = brevo("/contacts/lists/%d" % L)
        tam[L] = (d.get("name"), d.get("totalSubscribers"))
    print("Campaña:", nombre)
    print("Asunto:", g["asunto"])
    print("Listas:", ", ".join("%d %s (%s enviables)" % (L, n, t) for L, (n, t) in tam.items()))
    print("Enviables en total (sin descontar solapes):", sum(t or 0 for _, t in tam.values()))
    if a.solo_ver:
        return
    r = brevo("/emailCampaigns", "POST", cuerpo)
    cid = r.get("id")
    print("Borrador creado en Brevo: id", cid)
    if a.test:
        emails = [e.strip() for e in a.test.split(",") if e.strip()]
        brevo("/emailCampaigns/%s/sendTest" % cid, "POST", {"emailTo": emails})
        print("Test enviado a:", ", ".join(emails))
    print("NO enviada. Se envía solo cuando Maikel diga «mándala»:")
    print("  python3 scripts/brevo_campana.py --grupo %s --listas %s --enviar %s" % (a.grupo, a.listas, cid))


if __name__ == "__main__":
    main()
