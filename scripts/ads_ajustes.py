#!/usr/bin/env python3
"""Ajustes de estructura en Google Ads aprobados por Maikel (11/09):
anuncios para los grupos sin anuncio, URLs finales rotas, geo por presencia, negativas.
Uso: python3 scripts/ads_ajustes.py [--prueba]"""
import json, os, sys, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ads_metricas import CUENTA, DEV, VERSION, consulta
from panel_horario import token_google

PRUEBA = "--prueba" in sys.argv
BASE = f"https://googleads.googleapis.com/{VERSION}/customers/{CUENTA}"
SEARCH, SHOPPING = 24065940601, 24066002797
URL_OK = "https://equipzilla.com/compra/maquinaria/usada/maquinaria-construccion-segunda-mano"
URL_MAL = "https://equipzilla.com/compra/maquinaria/ocasion/maquinaria-construccion-segunda-mano"
URL_EXC = "https://equipzilla.com/compra/maquinaria/usada/maquinaria-construccion-segunda-mano/excavadoras-segunda-mano"
URL_PLAT = "https://equipzilla.com/compra/maquinaria/ocasion/plataforma-elevadora-segunda-mano"

def mutate(servicio, ops):
    if PRUEBA:
        print(f"[prueba] {servicio}: {len(ops)} operaciones"); return {}
    tk = token_google(["https://www.googleapis.com/auth/adwords"])
    req = urllib.request.Request(f"{BASE}/{servicio}:mutate", data=json.dumps({"operations": ops, "partialFailure": True}).encode(),
        headers={"Authorization": "Bearer " + tk, "developer-token": open(DEV).read().strip(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            j = json.loads(r.read()); pf = j.get("partialFailureError")
            print(f"{servicio}: {len(j.get('results', []))} ok" + (f" · fallo parcial: {str(pf)[:300]}" if pf else "")); return j
    except urllib.error.HTTPError as e:
        print(f"ERROR {servicio}: {e.code} {e.read().decode()[:400]}"); return {}

def rsa(ad_group_id, url, titulos, descripciones, rutas):
    return {"create": {"adGroup": f"customers/{CUENTA}/adGroups/{ad_group_id}", "status": "ENABLED",
            "ad": {"finalUrls": [url], "responsiveSearchAd": {
                "headlines": [{"text": t} for t in titulos], "descriptions": [{"text": d} for d in descripciones],
                "path1": rutas[0], "path2": rutas[1]}}}}

# 1) Anuncios para los dos grupos sin anuncio
retro = rsa(208483399828, URL_EXC,
    ["Retroexcavadoras de Segunda Mano", "Retro Mixta Usada con Garantía", "Retroexcavadora Ocasión Revisada", "Stock Real en España",
     "Precio Cerrado, Sin Sorpresas", "Horas y Estado Verificados", "Te Buscamos la Retro que Necesitas", "Financiación Disponible",
     "Entrega en Toda España", "Fotos Reales de Cada Unidad", "Asesor Técnico en 24 h", "Equipzilla Maquinaria Usada",
     "Mini Retro y Retro Mixta", "Pide Precio por WhatsApp", "Compra con Inspección Previa"],
    ["Retroexcavadoras y mixtas usadas revisadas por técnicos. Fotos reales, horas verificadas y precio cerrado.",
     "¿Buscas una retro mixta o mini retro? Te localizamos la unidad y te la entregamos con garantía.",
     "Stock de maquinaria de obra usada con inspección previa y financiación. Pide precio hoy.",
     "Compra maquinaria usada sin intermediarios raros: asesor técnico, inspección y entrega en toda España."],
    ["retroexcavadoras", "segunda-mano"])
plat = rsa(208483994348, URL_PLAT,
    ["Plataformas Elevadoras Usadas", "Tijera y Brazo Articulado Ocasión", "Plataforma Elevadora Segunda Mano", "Stock Real con Fotos",
     "Precio Cerrado y Garantía", "Horas Verificadas por Técnicos", "Diésel y Eléctricas Disponibles", "Entrega en Toda España",
     "Financiación a tu Medida", "Asesor Técnico en 24 h", "Equipzilla Maquinaria Usada", "Desde 6.000 € Revisadas",
     "Haulotte, JLG, Genie, Manitou", "Pide Precio por WhatsApp", "Inspección Antes de Comprar"],
    ["Plataformas elevadoras de tijera y articuladas usadas, revisadas y con garantía. Fotos y horas reales.",
     "Haulotte, JLG, Genie y Manitou de ocasión con inspección previa, precio cerrado y entrega en toda España.",
     "Compra tu plataforma elevadora usada con asesor técnico y financiación. Stock real, sin sorpresas.",
     "Eléctricas y diésel de 8 a 20 m. Te ayudamos a elegir la unidad correcta para tu obra o nave."],
    ["plataformas", "segunda-mano"])
mutate("adGroupAds", [retro, plat])

# 2) URLs finales que devuelven 308
ops = []
for r in consulta("SELECT ad_group_ad.ad.id, ad_group_ad.ad.final_urls, ad_group.name FROM ad_group_ad WHERE ad_group_ad.status != 'REMOVED' AND campaign.id = %d" % SEARCH):
    urls = r["adGroupAd"]["ad"].get("finalUrls") or []
    if any(u.rstrip("/") == URL_MAL for u in urls):
        ops.append({"update": {"resourceName": f"customers/{CUENTA}/ads/{r['adGroupAd']['ad']['id']}", "finalUrls": [URL_OK]}, "updateMask": "final_urls"})
        print("  URL corregida en grupo", r["adGroup"]["name"])
if ops: mutate("ads", ops)

# 3) Geo: solo presencia en España (no «interés»)
mutate("campaigns", [{"update": {"resourceName": f"customers/{CUENTA}/campaigns/{c}", "geoTargetTypeSetting": {"positiveGeoTargetType": "PRESENCE"}},
                      "updateMask": "geo_target_type_setting.positive_geo_target_type"} for c in (SEARCH, SHOPPING)])

# 4) Negativas de frase en ambas campañas
NEG = ["vendo", "agricola", "accesorios", "embargadas", "desguaces", "casquero", "hormigon", "hormigonera", "hormigoneras", "bloquera",
       "machacadora", "pozos", "pft", "barredora", "excavator", "diggers", "pelle", "buldoexcavator", "cuanto vale", "grande del mundo"]
mutate("campaignCriteria", [{"create": {"campaign": f"customers/{CUENTA}/campaigns/{c}", "negative": True,
                                        "keyword": {"text": n, "matchType": "PHRASE"}}} for c in (SEARCH, SHOPPING) for n in NEG])
print("hecho")
