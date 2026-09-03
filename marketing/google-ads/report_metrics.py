# -*- coding: utf-8 -*-
"""Lector de metricas de Google Ads para reportes/dashboards (autonomo).

Cualquier sesion (p.ej. la de Brevo) puede ejecutarlo para medir Google Ads:
imprime un resumen en Markdown + un bloque JSON con los KPIs de las campanas.

Credenciales: SOLO por variables de entorno (ver docs/PLAYBOOK-GOOGLE-ADS.md).
No hay ficheros de credenciales en el repo.

Uso:
  pip install google-ads
  python report_metrics.py                 # ultimos 7 dias
  python report_metrics.py --days 30       # ultimos 30 dias
  python report_metrics.py --json          # solo JSON
"""
import os, sys, json

JSON_ONLY = "--json" in sys.argv
DAYS = 7
if "--days" in sys.argv:
    try: DAYS = int(sys.argv[sys.argv.index("--days") + 1])
    except Exception: pass
RANGE = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}.get(DAYS, "LAST_7_DAYS")


def build_client():
    from google.ads.googleads.client import GoogleAdsClient
    cfg = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    login = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "").strip()
    if login:
        cfg["login_customer_id"] = login
    return GoogleAdsClient.load_from_dict(cfg)


def main():
    missing = [k for k in ("GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CLIENT_ID",
               "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_REFRESH_TOKEN",
               "GOOGLE_ADS_CUSTOMER_ID") if not os.environ.get(k)]
    if missing:
        sys.exit("Faltan variables de entorno: " + ", ".join(missing) +
                 "\nVer docs/PLAYBOOK-GOOGLE-ADS.md")
    cid = os.environ["GOOGLE_ADS_CUSTOMER_ID"].replace("-", "").strip()
    ga = build_client().get_service("GoogleAdsService")

    data = {"account_id": cid, "range": RANGE, "campaigns": [], "totals": {}}
    q = f"""SELECT campaign.name, campaign.advertising_channel_type, campaign.status,
        campaign.primary_status, metrics.impressions, metrics.clicks, metrics.cost_micros,
        metrics.conversions, metrics.conversions_value, metrics.average_cpc, metrics.ctr
        FROM campaign WHERE campaign.status!='REMOVED' AND segments.date DURING {RANGE}"""
    ti = tc = 0; tcost = tconv = tval = 0.0
    for r in ga.search(customer_id=cid, query=q):
        c, m = r.campaign, r.metrics
        cost = m.cost_micros / 1e6
        data["campaigns"].append({
            "name": c.name, "type": c.advertising_channel_type.name,
            "status": c.status.name, "primary_status": c.primary_status.name,
            "impressions": m.impressions, "clicks": m.clicks,
            "cost_eur": round(cost, 2), "conversions": round(m.conversions, 2),
            "conv_value_eur": round(m.conversions_value, 2),
            "avg_cpc_eur": round(m.average_cpc / 1e6, 2), "ctr_pct": round(m.ctr * 100, 2),
            "cpa_eur": round(cost / m.conversions, 2) if m.conversions else None})
        ti += m.impressions; tc += m.clicks; tcost += cost
        tconv += m.conversions; tval += m.conversions_value
    data["totals"] = {"impressions": ti, "clicks": tc, "cost_eur": round(tcost, 2),
        "conversions": round(tconv, 2), "conv_value_eur": round(tval, 2),
        "cpa_eur": round(tcost / tconv, 2) if tconv else None,
        "ctr_pct": round(tc / ti * 100, 2) if ti else 0}

    if JSON_ONLY:
        print(json.dumps(data, ensure_ascii=False, indent=2)); return
    t = data["totals"]
    print(f"# Google Ads · Equipzilla Compraventa ({RANGE})\n\n**Cuenta:** {cid}\n")
    print("| Campaña | Tipo | Estado | Impr. | Clics | Coste € | Conv. | CPA € | CTR % |")
    print("|---|---|---|--:|--:|--:|--:|--:|--:|")
    for c in data["campaigns"]:
        print(f"| {c['name']} | {c['type']} | {c['primary_status']} | {c['impressions']} | "
              f"{c['clicks']} | {c['cost_eur']} | {c['conversions']} | "
              f"{c['cpa_eur'] if c['cpa_eur'] is not None else '—'} | {c['ctr_pct']} |")
    print(f"| **TOTAL** | | | **{t['impressions']}** | **{t['clicks']}** | **{t['cost_eur']}** "
          f"| **{t['conversions']}** | **{t['cpa_eur'] if t['cpa_eur'] is not None else '—'}** "
          f"| **{t['ctr_pct']}** |")
    print("\n```json\n" + json.dumps(data, ensure_ascii=False) + "\n```")


if __name__ == "__main__":
    main()
