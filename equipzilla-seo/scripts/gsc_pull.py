#!/usr/bin/env python3
"""
Extrae datos de Google Search Console por API para Equipzilla.

Autentica con una cuenta de servicio (clave JSON) y descarga el informe de
Rendimiento (Search Analytics) por consulta y por página, escribiendo:
  output/gsc_queries.csv  — query, clics, impresiones, ctr, posicion
  output/gsc_pages.csv    — pagina, clics, impresiones, ctr, posicion

No depende de `cryptography` (firma el JWT con la librería pura `rsa`).

Uso:
  GSC_KEY=/ruta/sa.json python scripts/gsc_pull.py --site sc-domain:equipzilla.com --months 12
"""
import argparse, base64, csv, json, os, time, urllib.request, urllib.parse
from datetime import date, timedelta
from pathlib import Path
import rsa
from pyasn1.codec.der import decoder

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"


def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=")


def load_priv(pem):
    body = "".join(l for l in pem.splitlines() if "PRIVATE KEY" not in l)
    seq, _ = decoder.decode(base64.b64decode(body))
    return rsa.PrivateKey.load_pkcs1(bytes(seq[2]), format="DER")


def get_token(sa):
    now = int(time.time())
    claims = {"iss": sa["client_email"], "scope": SCOPE,
              "aud": sa["token_uri"], "iat": now, "exp": now + 3600}
    hdr = b64u(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    pld = b64u(json.dumps(claims).encode())
    signing = hdr + b"." + pld
    sig = rsa.sign(signing, load_priv(sa["private_key"]), "SHA-256")
    jwt = signing + b"." + b64u(sig)
    data = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt.decode()}).encode()
    r = urllib.request.urlopen(urllib.request.Request(sa["token_uri"], data=data))
    return json.load(r)["access_token"]


def query(token, site, start, end, dimension, row_limit=25000):
    url = (f"https://www.googleapis.com/webmasters/v3/sites/"
           f"{urllib.parse.quote(site, safe='')}/searchAnalytics/query")
    body = json.dumps({"startDate": start, "endDate": end,
                       "dimensions": [dimension], "rowLimit": row_limit}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Authorization": "Bearer " + token,
                                          "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req)).get("rows", [])


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            key = r["keys"][0]
            w.writerow([key, r["clicks"], r["impressions"],
                        round(r["ctr"] * 100, 2), round(r["position"], 1)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="sc-domain:equipzilla.com")
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--key", default=os.environ.get("GSC_KEY", "/home/user/.gsc/equipzilla-sa.json"))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "output"))
    args = ap.parse_args()

    sa = json.load(open(args.key))
    token = get_token(sa)
    end = date.today() - timedelta(days=3)        # margen por el retardo de datos de GSC
    start = end - timedelta(days=30 * args.months)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    q = query(token, args.site, start.isoformat(), end.isoformat(), "query")
    p = query(token, args.site, start.isoformat(), end.isoformat(), "page")
    write_csv(out / "gsc_queries.csv", ["query", "clics", "impresiones", "ctr_%", "posicion"], q)
    write_csv(out / "gsc_pages.csv", ["pagina", "clics", "impresiones", "ctr_%", "posicion"], p)

    tot_c = sum(r["clicks"] for r in q)
    tot_i = sum(r["impressions"] for r in q)
    print(f"Rango: {start} → {end}  ({args.site})")
    print(f"Consultas: {len(q)} | Páginas: {len(p)}")
    print(f"Totales: {tot_c} clics, {tot_i} impresiones")
    print(f"Escrito: {out/'gsc_queries.csv'} y {out/'gsc_pages.csv'}")


if __name__ == "__main__":
    main()
