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
URL_PLAT = "https://equipzilla.com/compra/maquinaria/usada/plataforma-elevadora-segunda-mano"
# Páginas de categoría verificadas el 16/09 (200 + <title> y <h1> propios). Rodillos y
# compactadores NO tienen página: devuelven la genérica (404 blando), así que se quedan
# en URL_OK. Mandar cada anuncio a su categoría sube la relevancia, que es lo que hoy
# hace perder el 55 % de las impresiones por ranking.
POR_GRUPO = {
    "Dumpers 2a mano": "https://equipzilla.com/compra/maquinaria/usada/maquinaria-construccion-segunda-mano/dumpers-segunda-mano",
    "Minicargadoras 2a mano": "https://equipzilla.com/compra/maquinaria/usada/maquinaria-construccion-segunda-mano/minicargadoras-segunda-mano",
}

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
    ["Retroexcavadoras 2ª Mano", "Retro Mixta Usada con Garantía", "Retroexcavadora Ocasión", "Stock Real en España",
     "Precio Cerrado, Sin Sorpresas", "Horas y Estado Verificados", "Te Buscamos tu Retro", "Financiación Disponible",
     "Entrega en Toda España", "Fotos Reales de Cada Unidad", "Asesor Técnico en 24 h", "Equipzilla Maquinaria Usada",
     "Mini Retro y Retro Mixta", "Pide Precio por WhatsApp", "Compra con Inspección Previa"],
    ["Retroexcavadoras y mixtas usadas revisadas por técnicos. Fotos reales y precio cerrado.",
     "¿Retro mixta o mini retro? Te localizamos la unidad y te la entregamos con garantía.",
     "Stock de maquinaria de obra usada con inspección previa y financiación. Pide precio hoy.",
     "Compra con asesor técnico, inspección previa y entrega en toda España. Pide precio hoy."],
    ["retros", "segunda-mano"])
plat = rsa(208483994348, URL_PLAT,
    ["Plataformas Elevadoras Usadas", "Tijera y Articulada Ocasión", "Plataforma Elevadora 2ª Mano", "Stock Real con Fotos",
     "Precio Cerrado y Garantía", "Horas Verificadas por Técnicos", "Diésel y Eléctricas en Stock", "Entrega en Toda España",
     "Financiación a tu Medida", "Asesor Técnico en 24 h", "Equipzilla Maquinaria Usada", "Desde 6.000 € Revisadas",
     "Haulotte, JLG, Genie, Manitou", "Pide Precio por WhatsApp", "Inspección Antes de Comprar"],
    ["Plataformas de tijera y articuladas usadas, revisadas y con garantía. Fotos reales.",
     "Haulotte, JLG, Genie y Manitou de ocasión con inspección previa y entrega en toda España.",
     "Compra tu plataforma usada con asesor técnico y financiación. Stock real, sin sorpresas.",
     "Eléctricas y diésel de 8 a 20 m. Te ayudamos a elegir la unidad correcta para tu obra."],
    ["plataformas", "segunda-mano"])
mutate("adGroupAds", [retro, plat])

# 2) URLs finales: quitar la que devuelve 308 y, si el grupo tiene página propia, usarla
ops = []
for r in consulta("SELECT ad_group_ad.ad.id, ad_group_ad.ad.final_urls, ad_group.name FROM ad_group_ad WHERE ad_group_ad.status != 'REMOVED' AND campaign.id = %d" % SEARCH):
    urls = r["adGroupAd"]["ad"].get("finalUrls") or []
    grupo = r["adGroup"]["name"]
    destino = POR_GRUPO.get(grupo, URL_OK)
    if any(u.rstrip("/") == URL_MAL for u in urls) or (grupo in POR_GRUPO and urls and urls[0].rstrip("/") != destino):
        ops.append({"update": {"resourceName": f"customers/{CUENTA}/ads/{r['adGroupAd']['ad']['id']}", "finalUrls": [destino]}, "updateMask": "final_urls"})
        print(f"  URL de {grupo} -> {destino.rsplit('/', 1)[-1]}")
if ops: mutate("ads", ops)

# 3) Geo: solo presencia en España (no «interés»)
mutate("campaigns", [{"update": {"resourceName": f"customers/{CUENTA}/campaigns/{c}", "geoTargetTypeSetting": {"positiveGeoTargetType": "PRESENCE"}},
                      "updateMask": "geo_target_type_setting.positive_geo_target_type"} for c in (SEARCH, SHOPPING)])

# 4) Negativas de frase en ambas campañas (20 del 11/09 + 11 del 12/09 + 5 del 13/09 + 5 del 14/09 + 4 del 15/09)
NEG = ["vendo", "agricola", "accesorios", "embargadas", "desguaces", "casquero", "hormigon", "hormigonera", "hormigoneras", "bloquera",
       "machacadora", "pozos", "pft", "barredora", "excavator", "diggers", "pelle", "buldoexcavator", "cuanto vale", "grande del mundo",
       "tractopelle", "vanzare", "olx", "maroc", "prix", "bolivia", "escavadeira", "cuanto cuesta", "tipos de", "tractores", "desbrozadora",
       "tractor", "trabajando", "trituradora", "forestal", "escavador",
       "fratasadora", "fratasadoras", "bagger", "como es", "precio hora",
       "occasion", "miniexcavatoare", "bauhaus", "camion",
       "chinas", "super maquina", "por menos de"]
# Google trata los acentos como caracteres distintos en las negativas: «agricola» no
# bloquea «agrícola». Medido el 17/09 sobre los términos de 7 días: 420 impresiones y
# 3 clics se escapaban por esto, 364 de ellas de maquinaria agrícola. Importa poco por
# el gasto y mucho por el CTR, que es lo que sostiene el ranking.
ACENTOS = {"agricola": "agrícola", "hormigon": "hormigón", "financiacion": "financiación",
           "camion": "camión", "cuanto vale": "cuánto vale", "cuanto cuesta": "cuánto cuesta",
           "como es": "cómo es", "ficha tecnica": "ficha técnica",
           "caracteristicas tecnicas": "características técnicas"}
NEG = NEG + [v for k, v in ACENTOS.items() if v not in NEG]
mutate("campaignCriteria", [{"create": {"campaign": f"customers/{CUENTA}/campaigns/{c}", "negative": True,
                                        "keyword": {"text": n, "matchType": "PHRASE"}}} for c in (SEARCH, SHOPPING) for n in NEG])
# 5) Enlaces de sitio: cada uno a la página que promete
# Los 4 enlaces activos («Miniexcavadoras», «Excavadoras 2a mano», «Dumpers de obra» y
# «Asesoramiento de compra») apuntaban los cuatro a la MISMA página genérica, y además
# por la ruta /ocasion/ que devuelve 308. Medido el 20/09 sobre 30 días: por esos enlaces
# pasan 465 clics y 386,21 € (el 71 % del gasto de Search) y salen 3 de las 8 conversiones
# de la cuenta. Es el cambio de mayor alcance de toda la fase 0.
SITELINKS = {
    "398500184077": "https://equipzilla.com/compra/maquinaria/usada/maquinaria-construccion-segunda-mano/miniexcavadoras-segunda-mano",
    "398500245136": "https://equipzilla.com/compra/maquinaria/usada/maquinaria-construccion-segunda-mano/excavadoras-segunda-mano",
    "398574061461": "https://equipzilla.com/compra/maquinaria/usada/maquinaria-construccion-segunda-mano/dumpers-segunda-mano",
    "398500245241": URL_OK,   # «Asesoramiento de compra»: no hay página propia, va a la general sin redirección
}
ops = []
for r in consulta("SELECT asset.id, asset.final_urls, asset.sitelink_asset.link_text FROM campaign_asset WHERE campaign_asset.field_type = 'SITELINK' AND campaign_asset.status = 'ENABLED'"):
    aid = str(r["asset"]["id"])
    destino = SITELINKS.get(aid)
    actual = (r["asset"].get("finalUrls") or [""])[0]
    if destino and actual.rstrip("/") != destino:
        ops.append({"update": {"resourceName": f"customers/{CUENTA}/assets/{aid}", "finalUrls": [destino]}, "updateMask": "final_urls"})
        print(f"  Enlace «{r['asset']['sitelinkAsset']['linkText']}» -> {destino.rsplit('/', 1)[-1]}")
if ops: mutate("assets", ops)

print("hecho")
