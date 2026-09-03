# -*- coding: utf-8 -*-
"""Crea una campana de Shopping estandar en Google Ads via API (EN PAUSA).

Vincula la cuenta con Google Merchant Center y crea un grupo de productos raiz
que puja por todo el catalogo. Reutiliza las credenciales de .env y las mismas
helpers que create_campaign_api.py.

Requisitos previos:
  - Merchant Center vinculado a la cuenta de Google Ads (link aprobado).
  - Feed subido a Merchant Center (usa feed_generator.py).

Uso:
  python create_shopping_api.py --dry-run
  python create_shopping_api.py
"""
import os
import sys
import uuid

from create_campaign_api import load_env, build_client

MERCHANT_ID = os.environ.get("GOOGLE_ADS_MERCHANT_ID", "5828608786")
FEED_LABEL = os.environ.get("GOOGLE_ADS_FEED_LABEL", "ES")   # etiqueta/pais del feed
DAILY_BUDGET_EUR = 30
GEO_SPAIN = "geoTargetConstants/2724"
LANG_SPANISH = "languageConstants/1003"
CAMPAIGN_NAME = "ES | Shopping | Maquinaria Construccion 2a Mano"

DRY_RUN = "--dry-run" in sys.argv


def main():
    load_env()
    customer_id = os.environ["GOOGLE_ADS_CUSTOMER_ID"].replace("-", "").strip()
    merchant_id = str(MERCHANT_ID).replace("-", "").strip()

    if DRY_RUN:
        print("== DRY RUN Shopping (no se crea nada) ==")
        print(f"Cuenta: {customer_id}  |  Merchant Center: {merchant_id}")
        print(f"Campana: {CAMPAIGN_NAME}  |  {DAILY_BUDGET_EUR} EUR/dia (EN PAUSA)")
        print(f"Feed label/pais: {FEED_LABEL}  |  Geo: Espana  |  Idioma: Espanol")
        print("Recuerda: el link Merchant<->Ads debe estar aprobado y el feed subido.")
        return

    client = build_client()

    # 1) Presupuesto
    budget_svc = client.get_service("CampaignBudgetService")
    b_op = client.get_type("CampaignBudgetOperation")
    b = b_op.create
    b.name = f"Presupuesto Shopping {uuid.uuid4().hex[:6]}"
    b.amount_micros = DAILY_BUDGET_EUR * 1_000_000
    b.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    b.explicitly_shared = False
    budget_rn = budget_svc.mutate_campaign_budgets(
        customer_id=customer_id, operations=[b_op]).results[0].resource_name
    print(f"[OK] Presupuesto: {budget_rn}")

    # 2) Campana Shopping (EN PAUSA)
    camp_svc = client.get_service("CampaignService")
    c_op = client.get_type("CampaignOperation")
    c = c_op.create
    c.name = CAMPAIGN_NAME
    c.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SHOPPING
    c.status = client.enums.CampaignStatusEnum.PAUSED
    c.campaign_budget = budget_rn
    # CPC manual provisional (sin conversiones aun); cambiar a Max. conversiones despues.
    c.manual_cpc.enhanced_cpc_enabled = False
    try:
        c.contains_eu_political_advertising = (
            client.enums.EuPoliticalAdvertisingStatusEnum
            .DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING)
    except Exception:
        pass
    c.shopping_setting.merchant_id = int(merchant_id)
    c.shopping_setting.campaign_priority = 0
    c.shopping_setting.enable_local = False
    try:
        c.shopping_setting.feed_label = FEED_LABEL
    except Exception:
        c.shopping_setting.sales_country = FEED_LABEL
    c.network_settings.target_google_search = True
    c.network_settings.target_search_network = False
    campaign_rn = camp_svc.mutate_campaigns(
        customer_id=customer_id, operations=[c_op]).results[0].resource_name
    print(f"[OK] Campana Shopping creada (EN PAUSA): {campaign_rn}")

    # 3) Ubicacion + idioma
    # Nota: Shopping estandar NO admite criterio de idioma -> solo ubicacion.
    crit_svc = client.get_service("CampaignCriterionService")
    op = client.get_type("CampaignCriterionOperation")
    op.create.campaign = campaign_rn
    op.create.location.geo_target_constant = GEO_SPAIN
    crit_svc.mutate_campaign_criteria(customer_id=customer_id, operations=[op])
    print("[OK] Segmentacion: Espana")

    # 4) Grupo de anuncios de producto
    ag_svc = client.get_service("AdGroupService")
    ag_op = client.get_type("AdGroupOperation")
    ag = ag_op.create
    ag.name = "Todos los productos"
    ag.campaign = campaign_rn
    ag.type_ = client.enums.AdGroupTypeEnum.SHOPPING_PRODUCT_ADS
    ag.status = client.enums.AdGroupStatusEnum.ENABLED
    ag_rn = ag_svc.mutate_ad_groups(
        customer_id=customer_id, operations=[ag_op]).results[0].resource_name
    print(f"[OK] Grupo de productos: {ag_rn}")

    # 5) Anuncio de producto (Shopping product ad)
    aga_svc = client.get_service("AdGroupAdService")
    ad_op = client.get_type("AdGroupAdOperation")
    ad_op.create.ad_group = ag_rn
    ad_op.create.status = client.enums.AdGroupAdStatusEnum.ENABLED
    ad_op.create.ad.shopping_product_ad = client.get_type("ShoppingProductAdInfo")
    aga_svc.mutate_ad_group_ads(customer_id=customer_id, operations=[ad_op])
    print("[OK] Anuncio de producto creado")

    # 6) Grupo de fichas raiz (puja por todo el catalogo)
    agc_svc = client.get_service("AdGroupCriterionService")
    lg_op = client.get_type("AdGroupCriterionOperation")
    lg = lg_op.create
    lg.ad_group = ag_rn
    lg.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
    lg.listing_group.type_ = client.enums.ListingGroupTypeEnum.UNIT
    lg.cpc_bid_micros = 300_000  # 0,30 EUR puja por defecto (CPC manual)
    agc_svc.mutate_ad_group_criteria(customer_id=customer_id, operations=[lg_op])
    print("[OK] Grupo de fichas raiz (todos los productos)")

    print("\n===================================================")
    print("CAMPANA DE SHOPPING CREADA — esta EN PAUSA.")
    print("Antes de activar: verifica el link Merchant<->Ads y que el")
    print("feed este subido y aprobado en Merchant Center.")
    print("===================================================")


if __name__ == "__main__":
    main()
