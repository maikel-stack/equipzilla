#!/usr/bin/env python3
"""Fase 1 del plan de Google Ads. Ejecutar SIEMPRE después de scripts/ads_ajustes.py:
esta fase copia anuncios y URLs tal cual, así que hereda lo que la fase 0 haya corregido.
 (docs/ADS-ESTRUCTURA-Y-PLAN-PRESUPUESTO.md):
divide la campaña única de Search en campañas por categoría, cada una con su
presupuesto, copiando grupos, palabras clave, anuncios, negativas y extensiones.

Seguridad:
  · Sin argumentos o con --prueba: solo lee la cuenta e imprime el plan. No escribe.
  · --aplicar: crea las campañas nuevas EN PAUSA (la actual sigue igual). Reversible.
  · --activar: activa las nuevas y pausa la actual. Cambia el presupuesto total de
    20 a 65 €/día y la puja a Maximizar clics: SOLO con OK de Maikel.
  · --generico-exacta: en la campaña de control deja solo «maquinaria construccion
    segunda mano» exacta con CPC máx. 0,40 €. Por defecto se copia tal cual (el
    grupo genérico es el único con conversiones medidas a 14/09).

Uso: python3 scripts/ads_reestructura.py [--prueba | --aplicar | --activar] [--generico-exacta]
"""
import json, os, sys, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ads_metricas import CUENTA, DEV, VERSION, consulta
from panel_horario import token_google

ARGS = sys.argv[1:]
APLICAR, ACTIVAR, GEN_EXACTA = "--aplicar" in ARGS, "--activar" in ARGS, "--generico-exacta" in ARGS
BASE = f"https://googleads.googleapis.com/{VERSION}/customers/{CUENTA}"
ORIGEN = 24065940601                     # ES | Compra | Maquinaria Construccion 2a Mano
ESPANA, ESPANOL = "geoTargetConstants/2724", "languageConstants/1003"
CPC_MAX = 600_000                        # 0,60 € (doc, apartado 3)

# Campañas nuevas: nombre → (presupuesto €/día, grupos de la campaña actual que se mueven)
PLAN = {
    "ES | Search | Movimiento de tierras": (30, [199640758298, 199075600216, 208483399828, 199640758498, 197328083494, 197362093183]),
    "ES | Search | Elevacion y manipulacion": (20, [208483994348, 200940493918, 199717988763]),
    "ES | Search | Marcas": (10, [204324799371]),
    "ES | Search | Genericas (control)": (5, [203798862652]),
}
GENERICO = 203798862652


def mutate(servicio, ops, etiqueta=""):
    if not ops:
        return []
    if not (APLICAR or ACTIVAR):
        print(f"  [prueba] {servicio}: {len(ops)} operaciones {etiqueta}")
        return [f"prueba/{servicio}/{i}" for i in range(len(ops))]
    tk = token_google(["https://www.googleapis.com/auth/adwords"])
    req = urllib.request.Request(f"{BASE}/{servicio}:mutate", data=json.dumps({"operations": ops}).encode(),
        headers={"Authorization": "Bearer " + tk, "developer-token": open(DEV).read().strip(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            res = json.loads(r.read()).get("results", [])
            print(f"  {servicio}: {len(res)} ok {etiqueta}")
            return [x["resourceName"] for x in res]
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ERROR {servicio} {etiqueta}: {e.code} {e.read().decode()[:600]}")


def leer_origen():
    """Todo lo que hay que copiar de la campaña actual."""
    o = {}
    o["campana"] = consulta(f"SELECT campaign.network_settings.target_google_search, campaign.network_settings.target_search_network, campaign.network_settings.target_partner_search_network, campaign.network_settings.target_content_network FROM campaign WHERE campaign.id = {ORIGEN}")[0]["campaign"]
    o["grupos"] = {int(r["adGroup"]["id"]): r["adGroup"] for r in consulta(
        f"SELECT ad_group.id, ad_group.name, ad_group.status, ad_group.cpc_bid_micros FROM ad_group WHERE campaign.id = {ORIGEN} AND ad_group.status != 'REMOVED'")}
    o["keywords"] = {}
    for r in consulta(f"SELECT ad_group.id, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group_criterion.status, ad_group_criterion.final_urls FROM ad_group_criterion WHERE campaign.id = {ORIGEN} AND ad_group_criterion.type = 'KEYWORD' AND ad_group_criterion.negative = FALSE AND ad_group_criterion.status != 'REMOVED'"):
        o["keywords"].setdefault(int(r["adGroup"]["id"]), []).append(r["adGroupCriterion"])
    o["anuncios"] = {}
    for r in consulta(f"SELECT ad_group.id, ad_group_ad.status, ad_group_ad.ad.final_urls, ad_group_ad.ad.responsive_search_ad.headlines, ad_group_ad.ad.responsive_search_ad.descriptions, ad_group_ad.ad.responsive_search_ad.path1, ad_group_ad.ad.responsive_search_ad.path2 FROM ad_group_ad WHERE campaign.id = {ORIGEN} AND ad_group_ad.status != 'REMOVED' AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'"):
        o["anuncios"].setdefault(int(r["adGroup"]["id"]), []).append(r["adGroupAd"])
    o["negativas"] = [r["campaignCriterion"]["keyword"] for r in consulta(
        f"SELECT campaign_criterion.keyword.text, campaign_criterion.keyword.match_type FROM campaign_criterion WHERE campaign.id = {ORIGEN} AND campaign_criterion.negative = TRUE AND campaign_criterion.type = 'KEYWORD'")]
    o["assets"] = [(r["campaignAsset"]["asset"], r["campaignAsset"]["fieldType"]) for r in consulta(
        f"SELECT campaign.id, campaign_asset.asset, campaign_asset.field_type FROM campaign_asset WHERE campaign.id = {ORIGEN} AND campaign_asset.status = 'ENABLED'")]
    return o


def rsa_copia(a):
    rsa = a["ad"]["responsiveSearchAd"]
    ad = {"finalUrls": a["ad"].get("finalUrls", []), "responsiveSearchAd": {
        "headlines": [{"text": h["text"], **({"pinnedField": h["pinnedField"]} if h.get("pinnedField") else {})} for h in rsa["headlines"]],
        "descriptions": [{"text": d["text"], **({"pinnedField": d["pinnedField"]} if d.get("pinnedField") else {})} for d in rsa["descriptions"]]}}
    for p in ("path1", "path2"):
        if rsa.get(p):
            ad["responsiveSearchAd"][p] = rsa[p]
    return ad


def crear(o):
    ns = o["campana"].get("networkSettings", {})
    resumen = []
    for nombre, (eur, grupos) in PLAN.items():
        faltan = [g for g in grupos if g not in o["grupos"]]
        if faltan:
            raise SystemExit(f"grupos que no existen en la campaña actual: {faltan}")
        print(f"\n== {nombre} · {eur} €/día · {len(grupos)} grupos ==")
        for g in grupos:
            n_kw, n_ad = len(o["keywords"].get(g, [])), len(o["anuncios"].get(g, []))
            aviso = "  ← SIN ANUNCIO: ejecutar antes scripts/ads_ajustes.py" if n_ad == 0 and o["grupos"][g]["status"] == "ENABLED" else ""
            print(f"   · {o['grupos'][g]['name']} [{o['grupos'][g]['status']}] {n_kw} kw · {n_ad} anuncio(s){aviso}")
        cpc_max = 400_000 if (GEN_EXACTA and GENERICO in grupos) else CPC_MAX
        # 1) presupuesto propio
        (presu,) = mutate("campaignBudgets", [{"create": {"name": f"Presupuesto · {nombre}", "amountMicros": eur * 1_000_000,
                                                            "deliveryMethod": "STANDARD", "explicitlyShared": False}}], nombre)
        # 2) campaña en pausa, Maximizar clics con CPC máximo, geo solo presencia
        (camp,) = mutate("campaigns", [{"create": {
            "name": nombre, "status": "PAUSED", "advertisingChannelType": "SEARCH", "campaignBudget": presu,
            "maximizeClicks": {"cpcBidCeilingMicros": cpc_max},
            "networkSettings": {"targetGoogleSearch": ns.get("targetGoogleSearch", True), "targetSearchNetwork": ns.get("targetSearchNetwork", False),
                                "targetPartnerSearchNetwork": False, "targetContentNetwork": False},
            "geoTargetTypeSetting": {"positiveGeoTargetType": "PRESENCE", "negativeGeoTargetType": "PRESENCE"},
            "containsEuPoliticalAdvertising": "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING"}}], nombre)
        # 3) España, español y las negativas de la campaña actual
        crit = [{"create": {"campaign": camp, "location": {"geoTargetConstant": ESPANA}}},
                {"create": {"campaign": camp, "language": {"languageConstant": ESPANOL}}}]
        crit += [{"create": {"campaign": camp, "negative": True, "keyword": {"text": k["text"], "matchType": k["matchType"]}}} for k in o["negativas"]]
        mutate("campaignCriteria", crit, f"(geo, idioma y {len(o['negativas'])} negativas)")
        # 4) extensiones: mismos assets enlazados a la campaña nueva
        mutate("campaignAssets", [{"create": {"campaign": camp, "asset": a, "fieldType": f}} for a, f in o["assets"]], "(extensiones)")
        # 5) grupos, palabras clave y anuncios
        for g in grupos:
            src = o["grupos"][g]
            (ag,) = mutate("adGroups", [{"create": {"campaign": camp, "name": src["name"], "status": src["status"], "type": "SEARCH_STANDARD",
                                                     **({"cpcBidMicros": src["cpcBidMicros"]} if src.get("cpcBidMicros") else {})}}], src["name"])
            kws = o["keywords"].get(g, [])
            if GEN_EXACTA and g == GENERICO:
                kws = [{"keyword": {"text": "maquinaria construccion segunda mano", "matchType": "EXACT"}, "status": "ENABLED"}]
            mutate("adGroupCriteria", [{"create": {"adGroup": ag, "status": k.get("status", "ENABLED"),
                                                   "keyword": {"text": k["keyword"]["text"], "matchType": k["keyword"]["matchType"]},
                                                   **({"finalUrls": k["finalUrls"]} if k.get("finalUrls") else {})}} for k in kws], f"(kw {src['name']})")
            mutate("adGroupAds", [{"create": {"adGroup": ag, "status": a.get("status", "ENABLED"), "ad": rsa_copia(a)}} for a in o["anuncios"].get(g, [])], f"(anuncios {src['name']})")
        resumen.append((nombre, eur, camp))
    return resumen


def activar(resumen):
    nuevas = {r["campaign"]["name"]: r["campaign"]["resourceName"] for r in consulta(
        "SELECT campaign.name, campaign.resource_name FROM campaign WHERE campaign.name LIKE 'ES | Search | %' AND campaign.status = 'PAUSED'")}
    ops = [{"update": {"resourceName": rn, "status": "ENABLED"}, "updateMask": "status"} for rn in nuevas.values()]
    ops.append({"update": {"resourceName": f"customers/{CUENTA}/campaigns/{ORIGEN}", "status": "PAUSED"}, "updateMask": "status"})
    print(f"\nActivando {len(nuevas)} campañas nuevas y pausando la actual ({ORIGEN})")
    mutate("campaigns", ops, "(activar)")


if __name__ == "__main__":
    if ACTIVAR:
        activar(None)
        sys.exit(0)
    o = leer_origen()
    print(f"Campaña actual {ORIGEN}: {len(o['grupos'])} grupos · {sum(map(len, o['keywords'].values()))} keywords · "
          f"{sum(map(len, o['anuncios'].values()))} anuncios · {len(o['negativas'])} negativas · {len(o['assets'])} extensiones")
    print("Modo:", "APLICAR (crea en pausa)" if APLICAR else "PRUEBA (no escribe)", "· genérico:", "solo exacta 0,40 €" if GEN_EXACTA else "se copia tal cual")
    res = crear(o)
    total = sum(e for _, e, _ in res)
    print(f"\nResumen: {len(res)} campañas nuevas · {total} €/día en total (hoy 20 €/día en Search). "
          + ("Creadas EN PAUSA. Activar con --activar solo con OK de Maikel." if APLICAR else "Nada escrito. Aplicar con --aplicar."))
