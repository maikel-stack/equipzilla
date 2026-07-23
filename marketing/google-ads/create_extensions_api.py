# -*- coding: utf-8 -*-
"""Crea todas las extensiones (assets) y las vincula a la campana de busqueda."""
import os, sys
from create_campaign_api import load_env, build_client, FINAL_URL

load_env()
cid = os.environ["GOOGLE_ADS_CUSTOMER_ID"].replace("-", "").strip()
client = build_client()
ga = client.get_service("GoogleAdsService")
asset_svc = client.get_service("AssetService")
camp_asset_svc = client.get_service("CampaignAssetService")
AFT = client.enums.AssetFieldTypeEnum

# Campana de busqueda destino
sid = None
for r in ga.search(customer_id=cid, query="""SELECT campaign.id FROM campaign
        WHERE campaign.advertising_channel_type='SEARCH' AND campaign.status!='REMOVED'"""):
    sid = r.campaign.id
camp_rn = f"customers/{cid}/campaigns/{sid}"
print("Campana de busqueda:", camp_rn)

created = []  # (asset_rn, field_type)


def add_asset(build, field_type, label):
    op = client.get_type("AssetOperation")
    build(op.create)
    try:
        rn = asset_svc.mutate_assets(customer_id=cid, operations=[op]).results[0].resource_name
        created.append((rn, field_type))
        print(f"  [OK] asset {label}")
    except Exception as e:
        m = [l.strip() for l in str(e).splitlines() if 'message:' in l]
        print(f"  [X] asset {label}: {m[0][:80] if m else ''}")


# --- Sitelinks ---
SITELINKS = [
    ("Excavadoras 2a mano", "Oruga y ruedas revisadas", "Marcas Doosan y Develon"),
    ("Miniexcavadoras", "Compactas desde 13.900 EUR", "Kubota y mas marcas"),
    ("Dumpers de obra", "Articulados y rigidos", "Listos para trabajar"),
    ("Asesoramiento de compra", "Te ayudamos a elegir", "Sin compromiso"),
]
for text, d1, d2 in SITELINKS:
    def b(a, text=text, d1=d1, d2=d2):
        a.sitelink_asset.link_text = text
        a.sitelink_asset.description1 = d1
        a.sitelink_asset.description2 = d2
        a.final_urls.append(FINAL_URL)
    add_asset(b, AFT.SITELINK, f"sitelink '{text}'")

# --- Textos destacados (callouts) ---
CALLOUTS = ["Equipos revisados", "Envio a toda Espana", "Asesoramiento experto",
            "Marcas Doosan y Kubota", "Stock disponible", "Atencion personalizada"]
for c in CALLOUTS:
    add_asset(lambda a, c=c: setattr(a.callout_asset, "callout_text", c),
              AFT.CALLOUT, f"callout '{c}'")

# --- Fragmentos estructurados ---
SNIPPETS = [
    ("Marcas", ["Doosan", "Kubota", "Develon"]),
    ("Tipos", ["Excavadoras", "Miniexcavadoras", "Dumpers", "Rodillos", "Minicargadoras"]),
]
for header, values in SNIPPETS:
    def b(a, header=header, values=values):
        a.structured_snippet_asset.header = header
        a.structured_snippet_asset.values.extend(values)
    add_asset(b, AFT.STRUCTURED_SNIPPET, f"snippet '{header}'")

# --- Llamada ---
def call(a):
    a.call_asset.country_code = "ES"
    a.call_asset.phone_number = "911238750"
add_asset(call, AFT.CALL, "call 911238750")

# --- Precios ---
def price(a):
    p = a.price_asset
    p.type_ = client.enums.PriceExtensionTypeEnum.PRODUCT_CATEGORIES
    p.price_qualifier = client.enums.PriceExtensionPriceQualifierEnum.FROM
    p.language_code = "es"
    offers = [
        ("Miniexcavadoras", "Compactas revisadas", 13900),
        ("Excavadoras", "Oruga y ruedas", 87500),
        ("Palas cargadoras", "Alta capacidad", 197900),
    ]
    for header, desc, amount in offers:
        po = client.get_type("PriceOffering")
        po.header = header
        po.description = desc
        po.price.amount_micros = amount * 1_000_000
        po.price.currency_code = "EUR"
        po.unit = client.enums.PriceExtensionPriceUnitEnum.UNSPECIFIED
        po.final_url = FINAL_URL
        p.price_offerings.append(po)
add_asset(price, AFT.PRICE, "price (3 categorias)")

# --- Vincular todos los assets a la campana ---
print(f"\nVinculando {len(created)} assets a la campana...")
ops = []
for rn, ft in created:
    op = client.get_type("CampaignAssetOperation")
    op.create.campaign = camp_rn
    op.create.asset = rn
    op.create.field_type = ft
    ops.append(op)
ok = 0
for op in ops:
    try:
        camp_asset_svc.mutate_campaign_assets(customer_id=cid, operations=[op])
        ok += 1
    except Exception as e:
        m = [l.strip() for l in str(e).splitlines() if 'message:' in l]
        print(f"  [X] link {op.create.field_type.name}: {m[0][:70] if m else ''}")
print(f"[OK] {ok}/{len(ops)} extensiones vinculadas a la campana de busqueda.")
