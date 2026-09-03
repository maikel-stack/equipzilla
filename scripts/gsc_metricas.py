#!/usr/bin/env python3
"""Search Console de equipzilla.com con la cuenta de servicio.

Da lo que pide la instrucción maestra §11: tráfico, consultas con intención
comercial y los quick wins (posiciones 4-20 con impresiones).

Uso:
    python3 scripts/gsc_metricas.py [dias]      # por defecto 28
"""
import datetime as dt
import json
import os
import re
import urllib.parse
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import token_google        # noqa: E402

SITIO = "sc-domain:equipzilla.com"
# Intención de compraventa: lo que separa tráfico de demanda real.
COMERCIAL = re.compile(r"segunda mano|usad|ocasion|ocasión|comprar|venta|"
                       r"precio|barat|vendo", re.I)


def consulta(dias=28, dimensiones=("query",), filas=500):
    tk = token_google(["https://www.googleapis.com/auth/webmasters.readonly"])
    fin = dt.date.today() - dt.timedelta(days=2)      # GSC va 2 días por detrás
    cuerpo = {"startDate": str(fin - dt.timedelta(days=dias)), "endDate": str(fin),
              "dimensions": list(dimensiones), "rowLimit": filas}
    req = urllib.request.Request(
        "https://www.googleapis.com/webmasters/v3/sites/%s/searchAnalytics/query"
        % urllib.parse.quote(SITIO, safe=""),
        data=json.dumps(cuerpo).encode(),
        headers={"Authorization": "Bearer " + tk, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read()).get("rows", [])
    except urllib.error.HTTPError as e:
        print("ERROR GSC:", e.code, e.read().decode()[:200])
        return []


def resumen(dias=28):
    fs = consulta(dias, ("query",))
    tot = dict(clics=sum(r["clicks"] for r in fs),
               impresiones=sum(r["impressions"] for r in fs),
               consultas=len(fs))
    # Quick wins: ya rankeamos (4-20) y hay demanda. Subir aquí es lo barato.
    quick = [r for r in fs if 4 <= r["position"] <= 20 and r["impressions"] >= 10]
    quick.sort(key=lambda r: -r["impressions"])
    comercial = [r for r in fs if COMERCIAL.search(r["keys"][0])]
    return tot, quick, comercial, fs


if __name__ == "__main__":
    import urllib.parse
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 28
    tot, quick, com, fs = resumen(dias)
    print(f"=== equipzilla.com · últimos {dias} días ===")
    print(f"{tot['clics']} clics · {tot['impresiones']} impresiones · {tot['consultas']} consultas\n")
    print("QUICK WINS (posición 4-20, ≥10 impresiones):")
    for r in quick[:20]:
        print(f"  pos {r['position']:>5.1f} · {r['impressions']:>5} impr · {r['clicks']:>3} clics · {r['keys'][0]}")
    if not quick:
        print("  (ninguna todavía)")
    print(f"\nCONSULTAS CON INTENCIÓN DE COMPRA: {len(com)}")
    for r in sorted(com, key=lambda x: -x["impressions"])[:15]:
        print(f"  pos {r['position']:>5.1f} · {r['impressions']:>5} impr · {r['clicks']:>3} clics · {r['keys'][0]}")
