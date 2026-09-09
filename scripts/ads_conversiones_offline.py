#!/usr/bin/env python3
"""Conversiones offline de Google Ads desde Pipedrive.

Google solo ve los formularios web. Lo que de verdad importa (oferta enviada,
operación ganada) vive en Pipedrive. Los tratos que entraron por Ads llevan el
gclid en el campo «Gclid», así que se puede cerrar el círculo: cuando un trato
de compraventa con gclid llega a «Oferta enviada» o se gana, se sube como
conversión de clic a Ads con su fecha real y (si la hay) su valor.

Conversiones destino (creadas 09/09 por API):
  · «Pipedrive · oferta enviada (offline)»   valor por defecto 150 €
  · «Pipedrive · operación ganada (offline)» valor = importe del trato

Estado en data/ads_offline_visto.json para no subir dos veces la misma.
Google acepta conversiones hasta 90 días después del clic.

Uso:
    python3 scripts/ads_conversiones_offline.py           # sube lo nuevo
    PRUEBA=1 python3 scripts/ads_conversiones_offline.py  # solo imprime
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ads_metricas import CUENTA, DEV, VERSION, consulta  # noqa: E402
from panel_horario import pipedrive, token_google  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESTADO = os.path.join(RAIZ, "data", "ads_offline_visto.json")
PRUEBA = os.environ.get("PRUEBA") == "1"
NOMBRE_OFERTA = "Pipedrive · oferta enviada (offline)"
NOMBRE_GANADA = "Pipedrive · operación ganada (offline)"
ETAPAS_OFERTA = {37, 38, 28, 46, 87, 91, 92, 89, 90}   # oferta enviada o más adelante
PIPELINES = (6, 16)


def acciones():
    out = {}
    for r in consulta("SELECT conversion_action.id, conversion_action.name FROM conversion_action WHERE conversion_action.type = 'UPLOAD_CLICKS'"):
        out[r["conversionAction"]["name"]] = "customers/%s/conversionActions/%s" % (CUENTA, r["conversionAction"]["id"])
    return out


def campo_gclid():
    for f in pipedrive("/dealFields", limit=500).get("data") or []:
        if f["name"] == "Gclid":
            return f["key"]
    raise SystemExit("no existe el campo Gclid en Pipedrive")


def tratos_con_gclid():
    key = campo_gclid()
    corte = (dt.date.today() - dt.timedelta(days=90)).isoformat()
    out = []
    for status in ("open", "won", "lost"):
        start = 0
        while True:
            d = pipedrive("/deals", start=start, limit=500, status=status)
            for x in d.get("data") or []:
                g = (x.get(key) or "").strip()
                if x.get("pipeline_id") not in PIPELINES or not g or g.lower() == "sin contenido":
                    continue
                if not re.search(r"compra|prospecto|solicitud de consulta por compra", x.get("title") or "", re.I):
                    continue
                if str(x.get("add_time"))[:10] < corte:
                    continue
                out.append((x, g))
            if not (d.get("additional_data", {}).get("pagination", {}).get("more_items_in_collection")):
                break
            start += 500
    return out


def fecha_ads(ts):
    """Pipedrive da UTC 'YYYY-MM-DD HH:MM:SS'; Ads quiere 'YYYY-MM-DD HH:MM:SS+00:00'."""
    return str(ts)[:19] + "+00:00"


def pendientes(tratos, acc, visto):
    conv = []
    for x, gclid in tratos:
        clave_of = "oferta:%s" % x["id"]
        clave_g = "ganada:%s" % x["id"]
        if x.get("stage_id") in ETAPAS_OFERTA or x.get("status") == "won":
            if clave_of not in visto:
                conv.append((clave_of, {"gclid": gclid, "conversionAction": acc[NOMBRE_OFERTA],
                                        "conversionDateTime": fecha_ads(x.get("stage_change_time") or x.get("update_time")),
                                        "conversionValue": 150.0, "currencyCode": "EUR"}, x))
        if x.get("status") == "won" and clave_g not in visto:
            conv.append((clave_g, {"gclid": gclid, "conversionAction": acc[NOMBRE_GANADA],
                                   "conversionDateTime": fecha_ads(x.get("won_time") or x.get("update_time")),
                                   "conversionValue": float(x.get("value") or 0), "currencyCode": "EUR"}, x))
    return conv


def subir(conversiones):
    """Google obliga a las integraciones nuevas a usar la Data Manager API
    (ConversionUploadService queda solo para cuentas antiguas)."""
    tk = token_google(["https://www.googleapis.com/auth/datamanager"])
    por_accion = {}
    for clave, c, x in conversiones:
        por_accion.setdefault(c["conversionAction"].split("/")[-1], []).append((clave, c))
    resultados, errores = [], []
    for accion_id, lista in por_accion.items():
        cuerpo = {
            "destinations": [{"operatingAccount": {"accountId": str(CUENTA), "product": "GOOGLE_ADS"},
                              "productDestinationId": accion_id}],
            "events": [{"adIdentifiers": {"gclid": c["gclid"]},
                        "eventTimestamp": c["conversionDateTime"].replace(" ", "T"),
                        "conversionValue": c["conversionValue"], "currency": c["currencyCode"],
                        "transactionId": clave} for clave, c in lista],
            "encoding": "HEX", "consent": {"adUserData": "CONSENT_GRANTED", "adPersonalization": "CONSENT_GRANTED"},
        }
        req = urllib.request.Request("https://datamanager.googleapis.com/v1/events:ingest",
                                     data=json.dumps(cuerpo).encode(),
                                     headers={"Authorization": "Bearer " + tk, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                resultados += [json.loads(r.read())] * len(lista)
        except urllib.error.HTTPError as e:
            errores.append("%s: %s" % (e.code, e.read().decode()[:300]))
    return {"results": resultados, "partialFailureError": "; ".join(errores) if errores else None}


def main():
    acc = acciones()
    if NOMBRE_OFERTA not in acc or NOMBRE_GANADA not in acc:
        raise SystemExit("faltan las conversiones offline en Ads: %s" % list(acc))
    visto = set(json.load(open(ESTADO)).get("claves", [])) if os.path.exists(ESTADO) else set()
    tratos = tratos_con_gclid()
    conv = pendientes(tratos, acc, visto)
    print("tratos de compraventa con gclid (90 d): %d · conversiones pendientes de subir: %d" % (len(tratos), len(conv)))
    for clave, c, x in conv:
        print("  %-14s trato %s · %s · %s · %s €" % (clave.split(":")[0], x["id"], (x.get("title") or "")[:40], c["conversionDateTime"][:10], c["conversionValue"]))
    if not conv or PRUEBA:
        return
    r = subir(conv)
    ok = [x for x in r.get("results", []) if x] if "results" in r else []
    err = r.get("partialFailureError") or r.get("error")
    print("subidas: %d · error: %s" % (len(ok), str(err)[:300] if err else "ninguno"))
    if "results" in r and not err:
        visto |= {clave for clave, _, _ in conv}
    elif "results" in r:
        # con fallo parcial, marcar solo las que Google devolvió sin error
        for (clave, _, _), res in zip(conv, r["results"]):
            if res:
                visto.add(clave)
    os.makedirs(os.path.dirname(ESTADO), exist_ok=True)
    json.dump({"claves": sorted(visto), "actualizado": dt.datetime.now().isoformat()}, open(ESTADO, "w"), indent=1)


if __name__ == "__main__":
    main()
