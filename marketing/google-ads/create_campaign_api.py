# -*- coding: utf-8 -*-
"""Crea la campana completa de Equipzilla en Google Ads via API.

Reutiliza EXACTAMENTE los grupos, keywords, anuncios y negativas ya validados
en build_campaign.py.  La campana se crea EN PAUSA para que la revises antes de
activarla y gastar.

Uso:
  1) pip install google-ads
  2) rellena .env  (copia de .env.example) con tus credenciales
  3) genera el refresh token:  python generate_refresh_token.py
  4) prueba primero en seco:    python create_campaign_api.py --dry-run
  5) crea de verdad:            python create_campaign_api.py

Nada de esto toca el repo: las credenciales viven solo en tu .env local.
"""
import os
import sys
import uuid

from build_campaign import (
    AD_GROUPS, NEGATIVES, FINAL_URL, PATH1, PATH2, CAMPAIGN, DAILY_BUDGET,
)

# --- Constantes de segmentacion ---
GEO_SPAIN = "geoTargetConstants/2724"       # Espana
LANG_SPANISH = "languageConstants/1003"     # Espanol
BUDGET_MICROS = int(float(DAILY_BUDGET) * 1_000_000)   # 50 EUR/dia -> 50.000.000 micros

DRY_RUN = "--dry-run" in sys.argv


def load_env(path=".env"):
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def build_client():
    from google.ads.googleads.client import GoogleAdsClient
    cfg = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    login_cid = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").strip()
    if login_cid:
        cfg["login_customer_id"] = login_cid
    return GoogleAdsClient.load_from_dict(cfg)


def match_type_enum(client, mt):
    e = client.enums.KeywordMatchTypeEnum
    return {"Exact": e.EXACT, "Phrase": e.PHRASE, "Broad": e.BROAD}[mt]


def main():
    load_env()
    customer_id = os.environ["GOOGLE_ADS_CUSTOMER_ID"].replace("-", "").strip()

    if DRY_RUN:
        n_kw = sum(len(d["keywords"]) for d in AD_GROUPS.values())
        print("== DRY RUN (no se crea nada) ==")
        print(f"Cuenta: {customer_id}")
        print(f"Campana: {CAMPAIGN}  |  Presupuesto: {DAILY_BUDGET} EUR/dia (EN PAUSA)")
        print(f"Grupos: {len(AD_GROUPS)}  |  Keywords: {n_kw}  |  Negativas: {len(NEGATIVES)}")
        print(f"Geo: Espana ({GEO_SPAIN})  |  Idioma: Espanol ({LANG_SPANISH})")
        print("Credenciales detectadas:",
              "OK" if os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN") else "FALTAN")
        return

    client = build_client()
    ga = client.get_service("GoogleAdsService")

    # 1) Presupuesto
    budget_svc = client.get_service("CampaignBudgetService")
    b_op = client.get_type("CampaignBudgetOperation")
    b = b_op.create
    b.name = f"Presupuesto {CAMPAIGN} {uuid.uuid4().hex[:6]}"
    b.amount_micros = BUDGET_MICROS
    b.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    b.explicitly_shared = False
    budget_rn = budget_svc.mutate_campaign_budgets(
        customer_id=customer_id, operations=[b_op]).results[0].resource_name
    print(f"[OK] Presupuesto creado: {budget_rn}")

    # 2) Campana (EN PAUSA, Maximizar conversiones, solo Busqueda)
    camp_svc = client.get_service("CampaignService")
    c_op = client.get_type("CampaignOperation")
    c = c_op.create
    c.name = CAMPAIGN
    c.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    c.status = client.enums.CampaignStatusEnum.PAUSED
    c.campaign_budget = budget_rn
    # Estrategia provisional: CPC manual (no requiere conversiones).
    # Cambiar a "Maximizar conversiones" cuando GA4 este vinculado e importadas.
    c.manual_cpc.enhanced_cpc_enabled = False
    # Auto-declaracion UE (evita el bloqueo en cuentas nuevas)
    try:
        c.contains_eu_political_advertising = (
            client.enums.EuPoliticalAdvertisingStatusEnum
            .DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING)
    except Exception:
        pass
    c.network_settings.target_google_search = True
    c.network_settings.target_search_network = False
    c.network_settings.target_content_network = False
    c.network_settings.target_partner_search_network = False
    campaign_rn = camp_svc.mutate_campaigns(
        customer_id=customer_id, operations=[c_op]).results[0].resource_name
    print(f"[OK] Campana creada (EN PAUSA): {campaign_rn}")

    # 3) Criterios de campana: idioma, ubicacion, negativas
    camp_crit_svc = client.get_service("CampaignCriterionService")
    crit_ops = []

    loc_op = client.get_type("CampaignCriterionOperation")
    loc_op.create.campaign = campaign_rn
    loc_op.create.location.geo_target_constant = GEO_SPAIN
    crit_ops.append(loc_op)

    lang_op = client.get_type("CampaignCriterionOperation")
    lang_op.create.campaign = campaign_rn
    lang_op.create.language.language_constant = LANG_SPANISH
    crit_ops.append(lang_op)

    for neg in NEGATIVES:
        n_op = client.get_type("CampaignCriterionOperation")
        n_op.create.campaign = campaign_rn
        n_op.create.negative = True
        n_op.create.keyword.text = neg
        n_op.create.keyword.match_type = client.enums.KeywordMatchTypeEnum.PHRASE
        crit_ops.append(n_op)

    camp_crit_svc.mutate_campaign_criteria(customer_id=customer_id, operations=crit_ops)
    print(f"[OK] Criterios: idioma + Espana + {len(NEGATIVES)} negativas")

    # 4) Grupos de anuncios, keywords y RSA
    ag_svc = client.get_service("AdGroupService")
    agc_svc = client.get_service("AdGroupCriterionService")
    aga_svc = client.get_service("AdGroupAdService")

    for ag_name, data in AD_GROUPS.items():
        ag_op = client.get_type("AdGroupOperation")
        ag = ag_op.create
        ag.name = ag_name
        ag.campaign = campaign_rn
        ag.status = client.enums.AdGroupStatusEnum.ENABLED
        ag.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
        ag.cpc_bid_micros = 600_000  # 0,60 EUR puja por defecto (CPC manual)
        ag_rn = ag_svc.mutate_ad_groups(
            customer_id=customer_id, operations=[ag_op]).results[0].resource_name

        # keywords
        kw_ops = []
        for kw, mt in data["keywords"]:
            k_op = client.get_type("AdGroupCriterionOperation")
            k = k_op.create
            k.ad_group = ag_rn
            k.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            k.keyword.text = kw
            k.keyword.match_type = match_type_enum(client, mt)
            kw_ops.append(k_op)
        agc_svc.mutate_ad_group_criteria(customer_id=customer_id, operations=kw_ops)

        # RSA
        ad_op = client.get_type("AdGroupAdOperation")
        ad = ad_op.create
        ad.ad_group = ag_rn
        ad.status = client.enums.AdGroupAdStatusEnum.ENABLED
        ad.ad.final_urls.append(FINAL_URL)
        rsa = ad.ad.responsive_search_ad
        for h in data["headlines"]:
            asset = client.get_type("AdTextAsset")
            asset.text = h
            rsa.headlines.append(asset)
        for d in data["descriptions"]:
            asset = client.get_type("AdTextAsset")
            asset.text = d
            rsa.descriptions.append(asset)
        rsa.path1 = PATH1
        rsa.path2 = PATH2
        aga_svc.mutate_ad_group_ads(customer_id=customer_id, operations=[ad_op])

        print(f"[OK] Grupo '{ag_name}': {len(data['keywords'])} keywords + 1 RSA")

    print("\n===================================================")
    print("CAMPANA CREADA CORRECTAMENTE — esta EN PAUSA.")
    print("Revisa en Google Ads y dale a ACTIVAR cuando este todo OK.")
    print("Recuerda anadir extensiones (enlaces, llamada, precio) y")
    print("verificar el seguimiento de conversiones antes de activar.")
    print("===================================================")


if __name__ == "__main__":
    main()
