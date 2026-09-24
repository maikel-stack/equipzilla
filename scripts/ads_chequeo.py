#!/usr/bin/env python3
"""Chequeo diario de Google Ads: solo lo que exige una acción.

Reúne en un comando las comprobaciones que el ciclo diario venía haciendo por
separado, y calla lo que está bien. Pensado para que cualquiera del equipo vea el
estado de la cuenta sin leer el reporte entero.

    python3 scripts/ads_chequeo.py

No escribe nada en la cuenta.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ads_metricas import consulta  # noqa: E402

SEARCH = 24065940601
CPA_OBJETIVO = 150
URL_QUE_REDIRIGE = "/compra/maquinaria/ocasion/"

alertas = []


def avisa(titulo, detalle, quien):
    alertas.append((titulo, detalle, quien))


def revisa_gasto_y_conversiones():
    tot = {"coste": 0.0, "conv": 0.0, "clics": 0}
    for r in consulta("SELECT campaign.name, metrics.cost_micros, metrics.conversions, metrics.clicks "
                      "FROM campaign WHERE segments.date DURING LAST_7_DAYS"):
        m = r["metrics"]
        tot["coste"] += int(m.get("costMicros") or 0) / 1e6
        tot["conv"] += float(m.get("conversions") or 0)
        tot["clics"] += int(m.get("clicks") or 0)
    print(f"7 días: {tot['coste']:.2f} € · {tot['clics']} clics · {tot['conv']:.0f} conversiones")
    if tot["conv"] == 0 and tot["coste"] > 100:
        avisa("Siete días sin una sola conversión",
              f"{tot['coste']:.0f} € gastados y nada medido", "Lorenzo (etiqueta) y Director")
    elif tot["conv"] and tot["coste"] / tot["conv"] > CPA_OBJETIVO:
        avisa("Coste por conversión por encima del objetivo",
              f"{tot['coste'] / tot['conv']:.0f} € frente a {CPA_OBJETIVO} €", "Director")
    return tot


def revisa_cuota():
    from ads_cuota import serie
    fs = serie(7)
    if not fs:
        return
    media = sum(f["cuota"] for f in fs) / len(fs)
    print(f"Cuota de impresiones de Búsqueda: {media:.1f} % de media en 7 días")
    if media < 30:
        avisa("No aparecemos en la mayoría de las búsquedas de nuestras keywords",
              f"cuota media {media:.0f} %: {100 - media:.0f} de cada 100 búsquedas no nos ven", "Director")


def revisa_grupos_sin_anuncio():
    con_anuncio = {r["adGroup"]["name"] for r in consulta(
        "SELECT ad_group.name FROM ad_group_ad WHERE ad_group_ad.status = 'ENABLED'")}
    huerfanos = [r["adGroup"]["name"] for r in consulta(
        "SELECT ad_group.name FROM ad_group WHERE ad_group.status = 'ENABLED' "
        "AND campaign.advertising_channel_type = 'SEARCH'") if r["adGroup"]["name"] not in con_anuncio]
    if huerfanos:
        avisa("Grupos activos que no pueden salir porque no tienen anuncio",
              ", ".join(huerfanos), "Director (scripts/ads_ajustes.py)")


def revisa_urls():
    malos = [r["adGroup"]["name"] for r in consulta(
        "SELECT ad_group.name, ad_group_ad.ad.final_urls FROM ad_group_ad "
        "WHERE ad_group_ad.status = 'ENABLED' AND campaign.advertising_channel_type = 'SEARCH'")
        if URL_QUE_REDIRIGE in (r["adGroupAd"]["ad"].get("finalUrls") or [""])[0]]
    enlaces = [r for r in consulta(
        "SELECT asset.final_urls FROM campaign_asset WHERE campaign_asset.field_type = 'SITELINK' "
        "AND campaign_asset.status = 'ENABLED'")
        if URL_QUE_REDIRIGE in (r["asset"].get("finalUrls") or [""])[0]]
    if malos or enlaces:
        avisa("Destinos que pasan por una redirección",
              f"{len(malos)} anuncios y {len(enlaces)} enlaces de sitio", "Director (scripts/ads_ajustes.py)")


def revisa_feed():
    try:
        from ads_feed import en_la_web, en_shopping, modelo
    except Exception as e:
        print("no se pudo revisar el feed:", e)
        return
    try:
        web, shop = en_la_web(), en_shopping()
    except SystemExit as e:
        avisa("La web ya no publica el stock como antes", str(e), "Lorenzo")
        return
    modelos_web = {modelo(n) for n in web}
    fuera = {t: d for t, d in shop.items()
             if not any(modelo(t) in w or w in modelo(t) for w in modelos_web if w and modelo(t))}
    gasto_total = sum(d["coste"] for d in shop.values())
    gasto_fuera = sum(d["coste"] for d in fuera.values())
    print(f"Shopping: {len(shop)} máquinas anunciadas · {len(web)} publicadas en la web")
    if fuera:
        pct = gasto_fuera / gasto_total * 100 if gasto_total else 0
        avisa("Shopping anuncia máquinas que ya no están en la web",
              f"{len(fuera)} máquinas se llevan {gasto_fuera:.0f} € de {gasto_total:.0f} € ({pct:.0f} %): "
              + ", ".join(list(fuera)[:4]), "David y Lorenzo (Merchant Center)")
    sin_anunciar = [n for n in web if not any(
        modelo(n) in modelo(t) or modelo(t) in modelo(n) for t in shop if modelo(t) and modelo(n))]
    if len(sin_anunciar) > 5:
        avisa("Stock publicado que Shopping no enseña",
              f"{len(sin_anunciar)} máquinas, entre ellas {', '.join(sin_anunciar[:3])}",
              "David y Lorenzo (Merchant Center)")


def revisa_llamadas():
    for r in consulta("SELECT campaign.name, metrics.phone_calls, metrics.phone_impressions "
                      "FROM campaign WHERE segments.date DURING LAST_30_DAYS"):
        m = r["metrics"]
        llamadas = int(m.get("phoneCalls") or 0)
        if llamadas:
            avisa("Llamadas desde el anuncio que el embudo no ve",
                  f"{llamadas} llamadas en 30 días al número de la extensión. No llevan gclid, "
                  "así que no aparecen como leads de Ads en Pipedrive", "Andrés (registro de la llamada)")


if __name__ == "__main__":
    revisa_gasto_y_conversiones()
    revisa_cuota()
    revisa_grupos_sin_anuncio()
    revisa_urls()
    revisa_llamadas()
    revisa_feed()
    print()
    if not alertas:
        print("Sin alertas. Todo en orden.")
    else:
        print(f"{len(alertas)} alertas:\n")
        for i, (t, d, q) in enumerate(alertas, 1):
            print(f"{i}. {t}\n   {d}\n   → {q}\n")
