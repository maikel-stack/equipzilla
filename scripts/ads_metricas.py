#!/usr/bin/env python3
"""KPIs de Google Ads compraventa con la cuenta de servicio del Sheet.

La cuenta de servicio está dada de alta directamente en la cuenta de Ads
3057448284, así que NO se manda login-customer-id (el MCC no la conoce).

Uso:
    python3 scripts/ads_metricas.py [dias]     # por defecto 30
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import token_google        # noqa: E402  (misma cuenta de servicio)

CUENTA = "3057448284"
VERSION = "v22"
DEV = os.path.expanduser("~/.outbound/googleads_dev_token")


def consulta(gaql):
    tk = token_google(["https://www.googleapis.com/auth/adwords"])
    req = urllib.request.Request(
        "https://googleads.googleapis.com/%s/customers/%s/googleAds:searchStream"
        % (VERSION, CUENTA), data=json.dumps({"query": gaql}).encode(),
        headers={"Authorization": "Bearer " + tk,
                 "developer-token": open(DEV).read().strip(),
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return [x for lote in json.loads(r.read()) for x in lote.get("results", [])]
    except urllib.error.HTTPError as e:
        print("ERROR Ads:", e.code, e.read().decode()[:300])
        return []


def campanas(dias=30):
    rango = "LAST_30_DAYS" if dias == 30 else ("LAST_7_DAYS" if dias == 7 else "TODAY")
    filas = []
    for r in consulta(
            "SELECT campaign.name, campaign.status, campaign.advertising_channel_type, "
            "metrics.impressions, metrics.clicks, metrics.cost_micros, "
            "metrics.conversions, metrics.average_cpc "
            "FROM campaign WHERE segments.date DURING %s" % rango):
        c, m = r["campaign"], r["metrics"]
        coste = int(m.get("costMicros") or 0) / 1e6
        clics = int(m.get("clicks") or 0)
        conv = float(m.get("conversions") or 0)
        filas.append(dict(
            nombre=c["name"], estado=c["status"], tipo=c.get("advertisingChannelType", ""),
            impresiones=int(m.get("impressions") or 0), clics=clics, coste=round(coste, 2),
            conversiones=round(conv, 1),
            cpc=round(coste / clics, 2) if clics else 0,
            cpa=round(coste / conv, 2) if conv else 0))
    return filas


if __name__ == "__main__":
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    fs = campanas(dias)
    if not fs:
        print("sin datos")
        sys.exit(0)
    print(f"{'Campaña':<46}{'Estado':<9}{'Impr':>7}{'Clics':>7}{'Coste':>9}{'CPC':>7}{'Conv':>7}{'CPA':>8}")
    t = dict(impresiones=0, clics=0, coste=0.0, conversiones=0.0)
    for f in fs:
        print(f"{f['nombre'][:44]:<46}{f['estado']:<9}{f['impresiones']:>7}{f['clics']:>7}"
              f"{f['coste']:>8.2f}€{f['cpc']:>7.2f}{f['conversiones']:>7.1f}{f['cpa']:>7.2f}€")
        for k in t:
            t[k] += f[k]
    print(f"{'TOTAL':<46}{'':<9}{t['impresiones']:>7}{t['clics']:>7}{t['coste']:>8.2f}€"
          f"{t['coste']/t['clics'] if t['clics'] else 0:>7.2f}{t['conversiones']:>7.1f}"
          f"{t['coste']/t['conversiones'] if t['conversiones'] else 0:>7.2f}€")
