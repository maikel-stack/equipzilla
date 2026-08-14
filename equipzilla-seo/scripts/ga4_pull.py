#!/usr/bin/env python3
"""
Extrae datos de Google Analytics 4 (Data API) para Equipzilla.

Misma autenticación que gsc_pull.py: cuenta de servicio (clave JSON) a la que
hay que dar acceso de lectura ("Viewer") en la propiedad GA4. Descarga el informe
de páginas de aterrizaje por canal orgánico:
  output/ga4_landing.csv — landing_page, sesiones, sesiones_enganchadas,
                           conversiones, ingresos

Uso:
  GSC_KEY=/ruta/sa.json python scripts/ga4_pull.py --property 123456789 --months 12

El property ID es el número de la propiedad GA4 (Admin → Configuración de la
propiedad → ID de propiedad), sin el prefijo "properties/".
"""
import argparse, base64, csv, json, os, time, urllib.request, urllib.parse
from datetime import date, timedelta
from pathlib import Path
import rsa
from pyasn1.codec.der import decoder

SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=")


def load_priv(pem):
    body = "".join(l for l in pem.splitlines() if "PRIVATE KEY" not in l)
    seq, _ = decoder.decode(base64.b64decode(body))
    return rsa.PrivateKey.load_pkcs1(bytes(seq[2]), format="DER")


def get_token(sa):
    now = int(time.time())
    claims = {"iss": sa["client_email"], "scope": SCOPE,
              "aud": sa.get("token_uri", TOKEN_URI), "iat": now, "exp": now + 3600}
    hdr = b64u(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    pld = b64u(json.dumps(claims).encode())
    signing = hdr + b"." + pld
    sig = rsa.sign(signing, load_priv(sa["private_key"]), "SHA-256")
    jwt = signing + b"." + b64u(sig)
    data = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt.decode()}).encode()
    r = urllib.request.urlopen(urllib.request.Request(sa.get("token_uri", TOKEN_URI), data=data))
    return json.load(r)["access_token"]


def run_report(token, prop, start, end):
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport"
    body = json.dumps({
        "dateRanges": [{"startDate": start, "endDate": end}],
        "dimensions": [{"name": "landingPagePlusQueryString"}],
        "metrics": [{"name": "sessions"}, {"name": "engagedSessions"},
                    {"name": "conversions"}, {"name": "totalRevenue"}],
        "dimensionFilter": {"filter": {
            "fieldName": "sessionDefaultChannelGroup",
            "stringFilter": {"value": "Organic Search"}}},
        "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        "limit": 10000,
    }).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Authorization": "Bearer " + token,
                                          "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req)).get("rows", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--property", required=True, help="ID numérico de la propiedad GA4")
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--key", default=os.environ.get("GSC_KEY", "/home/user/.gsc/equipzilla-sa.json"))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "output"))
    args = ap.parse_args()

    sa = json.load(open(args.key))
    token = get_token(sa)
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=30 * args.months)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    rows = run_report(token, args.property, start.isoformat(), end.isoformat())
    dst = out / "ga4_landing.csv"
    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["landing_page", "sesiones", "sesiones_enganchadas",
                    "conversiones", "ingresos"])
        for r in rows:
            d = r["dimensionValues"][0]["value"]
            m = [v["value"] for v in r["metricValues"]]
            w.writerow([d, m[0], m[1], m[2], m[3]])
    print(f"Rango: {start} → {end}  (GA4 property {args.property}, canal orgánico)")
    print(f"Landing pages: {len(rows)}  ->  {dst}")


if __name__ == "__main__":
    main()
