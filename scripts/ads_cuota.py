#!/usr/bin/env python3
"""Cuota de impresiones de Search: por qué no crecemos, día a día.

Por qué existe este script. En los agregados de 7 días parecía que la campaña
«pierde cada vez más impresiones por presupuesto». Mirando el dato diario se ve
que no es una tendencia: las tres cifras que da Google suman siempre 100 %.

    cuota obtenida + perdida por presupuesto + perdida por ranking = 100 %

Son el reparto del mismo pastel, no tres problemas distintos. Cuando la puja
automática puja alto, agota los 20 €/día y Google lo llama «perdida por
presupuesto»; cuando puja bajo, no agota nada y lo llama «perdida por ranking».
El número que de verdad importa es el primero: qué porcentaje de las búsquedas
de nuestras palabras clave nos ve un comprador. Lee siempre esa columna.

Uso: python3 scripts/ads_cuota.py [dias]     # por defecto 14
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ads_metricas import consulta  # noqa: E402

SEARCH = 24065940601


def serie(dias=14):
    rango = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}.get(dias, "LAST_14_DAYS")
    filas = []
    for r in consulta(
            "SELECT segments.date, metrics.impressions, metrics.clicks, metrics.cost_micros, "
            "metrics.average_cpc, metrics.conversions, metrics.search_impression_share, "
            "metrics.search_budget_lost_impression_share, metrics.search_rank_lost_impression_share "
            "FROM campaign WHERE campaign.id = %d AND segments.date DURING %s "
            "ORDER BY segments.date" % (SEARCH, rango)):
        m = r["metrics"]
        filas.append(dict(
            fecha=r["segments"]["date"], impresiones=int(m.get("impressions") or 0),
            clics=int(m.get("clicks") or 0), coste=int(m.get("costMicros") or 0) / 1e6,
            cpc=int(m.get("averageCpc") or 0) / 1e6, conv=float(m.get("conversions") or 0),
            cuota=float(m.get("searchImpressionShare") or 0) * 100,
            presu=float(m.get("searchBudgetLostImpressionShare") or 0) * 100,
            rank=float(m.get("searchRankLostImpressionShare") or 0) * 100))
    return filas


if __name__ == "__main__":
    fs = serie(int(sys.argv[1]) if len(sys.argv) > 1 else 14)
    if not fs:
        print("sin datos")
        sys.exit(0)
    print(f"{'fecha':<12}{'impr':>6}{'clics':>6}{'coste':>9}{'CPC':>7}{'conv':>6}"
          f"{'CUOTA':>8}{'presu':>8}{'rank':>7}{'suma':>7}")
    for f in fs:
        print(f"{f['fecha']:<12}{f['impresiones']:>6}{f['clics']:>6}{f['coste']:>8.2f}€"
              f"{f['cpc']:>7.2f}{f['conv']:>6.0f}{f['cuota']:>7.1f}%{f['presu']:>7.1f}%"
              f"{f['rank']:>6.1f}%{f['cuota'] + f['presu'] + f['rank']:>6.1f}%")
    cuotas = [f["cuota"] for f in fs]
    media = sum(cuotas) / len(cuotas)
    print(f"\nCuota media {media:.1f}% · mejor día {max(cuotas):.1f}% · peor {min(cuotas):.1f}%")
    print("La suma es siempre 100: «presu» y «rank» reparten lo mismo que no ganamos.")
    if media < 30:
        print(f"AVISO: con una cuota media del {media:.0f}% no vemos {100 - media:.0f} de cada "
              "100 búsquedas de nuestras keywords. Sube con presupuesto Y relevancia, no con una sola.")
