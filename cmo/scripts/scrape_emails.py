import argparse
import concurrent.futures as cf
import csv
import re
from urllib.parse import urljoin, urlparse

import httpx

EMAIL_RE = re.compile(
    r"(?:[a-zA-Z0-9_.+-])+@(?:[a-zA-Z0-9-])+(?:\.[a-zA-Z0-9-]+)+"
)
OBFUSCATED_RES = [
    (re.compile(r"([a-zA-Z0-9._+-]+)\s*(?:\[at\]|\(at\)|\s+at\s+)\s*([a-zA-Z0-9.-]+)\s*(?:\[dot\]|\(dot\)|\s+dot\s+)\s*([a-zA-Z]{2,})", re.I), r"\1@\2.\3"),
]
CONTACT_PATHS = ["", "contacto", "contact", "contactar", "contacta", "aviso-legal", "legal", "empresa", "nosotros", "about"]
SKIP_EMAIL_DOMAINS = {"sentry.io", "wixpress.com", "example.com", "domain.com", "youremail.com", "test.com"}
SKIP_EMAIL_PATTERNS = ["@2x", "sentry", "wixpress"]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)


def candidate_bases(web: str) -> list[str]:
    web = web.strip().rstrip("/")
    if web.startswith(("http://", "https://")):
        return [web]
    return [f"https://{web}", f"http://{web}"]


def clean_email(e: str) -> str | None:
    e = e.lower().strip(".,;:)(\"'“”‘’<>")
    if any(p in e for p in SKIP_EMAIL_PATTERNS):
        return None
    if any(e.endswith("@" + d) for d in SKIP_EMAIL_DOMAINS):
        return None
    if "@" not in e or e.count("@") > 1:
        return None
    local, domain = e.split("@")
    if len(local) > 64 or len(domain) > 253:
        return None
    if domain.endswith((".png", ".jpg", ".gif", ".svg", ".webp", ".css", ".js")):
        return None
    return e


def extract_emails(html: str) -> set[str]:
    found: set[str] = set()
    for m in EMAIL_RE.findall(html):
        c = clean_email(m)
        if c:
            found.add(c)
    for regex, template in OBFUSCATED_RES:
        for m in regex.finditer(html):
            rebuilt = regex.sub(template, m.group(0))
            c = clean_email(rebuilt)
            if c:
                found.add(c)
    for m in re.findall(r'mailto:([^"\s\'>]+)', html, re.I):
        c = clean_email(m.split("?")[0])
        if c:
            found.add(c)
    return found


def scrape_site(row: dict, timeout: float = 10.0, max_pages: int = 5) -> dict:
    bases = candidate_bases(row["web"])
    try:
        host = urlparse(bases[0]).netloc
    except Exception as e:
        return {**row, "emails": "", "status": f"bad_url: {e}"}

    emails: set[str] = set()
    status = "ok"
    domain_part = host.split(":")[0].lower()
    if domain_part.startswith("www."):
        domain_part = domain_part[4:]

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }
    last_err = None
    working_base = None

    with httpx.Client(follow_redirects=True, timeout=timeout, headers=headers, verify=False) as client:
        for base in bases:
            try:
                r = client.get(base)
                if r.status_code < 400:
                    working_base = str(r.url)
                    emails |= extract_emails(r.text)
                    break
                last_err = f"status_{r.status_code}"
            except httpx.HTTPError as e:
                last_err = f"http_error_{type(e).__name__}"

        if not working_base:
            return {**row, "emails": "", "status": last_err or "unreachable"}

        for path in CONTACT_PATHS[1:max_pages]:
            url = urljoin(working_base.rstrip("/") + "/", path)
            try:
                r = client.get(url)
                if r.status_code >= 400:
                    continue
                emails |= extract_emails(r.text)
            except httpx.HTTPError:
                continue

    priority: list[str] = []
    generic: list[str] = []
    personal: list[str] = []
    offsite: list[str] = []
    GENERIC_PREFIXES = ("info@", "contacto@", "contact@", "hola@", "ventas@", "comercial@", "alquiler@", "administracion@", "oficina@", "atencion@", "clientes@")
    for e in sorted(set(emails)):
        e_domain = e.split("@")[1]
        on_domain = domain_part and (e_domain == domain_part or e_domain.endswith("." + domain_part))
        if not on_domain:
            offsite.append(e)
            continue
        if any(e.startswith(p) for p in GENERIC_PREFIXES):
            generic.append(e)
        else:
            personal.append(e)
    ordered = (generic + personal + offsite)[:10]

    if not ordered and status == "ok":
        status = "no_emails_found"

    return {**row, "emails": ";".join(ordered), "status": status}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="/tmp/alquiladores.csv")
    parser.add_argument("--output", default="/tmp/alquiladores_emails.csv")
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--limit", type=int, default=0, help="0 = all")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if args.limit:
        rows = rows[: args.limit]

    print(f"Scraping {len(rows)} sites with {args.workers} workers...")

    results: list[dict] = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(scrape_site, row): row for row in rows}
        for i, fut in enumerate(cf.as_completed(futures), 1):
            res = fut.result()
            results.append(res)
            if i % 25 == 0 or i == len(rows):
                hit = sum(1 for r in results if r["emails"])
                print(f"  {i}/{len(rows)}  hits={hit}")

    results.sort(key=lambda r: r["alquilador"])
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["alquilador", "web", "emails", "status"])
        w.writeheader()
        w.writerows(results)

    hit = sum(1 for r in results if r["emails"])
    print(f"\nDone. {hit}/{len(results)} with email ({hit*100/len(results):.0f}%).")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
