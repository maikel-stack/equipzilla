import os
from datetime import date, timedelta

REQUIRED_ENV = (
    "GSC_SERVICE_ACCOUNT_JSON",
    "GSC_SITE_URL",
)


def _credentials_status() -> str | None:
    missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
    if missing:
        return f"missing_env: {', '.join(missing)}"
    return None


def fetch_metrics() -> dict:
    err = _credentials_status()
    if err:
        return {"status": "unconfigured", "reason": err}

    import json

    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds_json = os.environ["GSC_SERVICE_ACCOUNT_JSON"]
    info = json.loads(creds_json) if creds_json.strip().startswith("{") else json.load(open(creds_json))
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    site = os.environ["GSC_SITE_URL"]

    today = date.today()
    yesterday = today - timedelta(days=1)
    eight_days_ago = today - timedelta(days=8)
    fifteen_days_ago = today - timedelta(days=15)

    last_7d = _query(service, site, eight_days_ago, yesterday)
    prev_7d = _query(service, site, fifteen_days_ago, eight_days_ago - timedelta(days=1))
    top_queries = _query_top(service, site, eight_days_ago, yesterday)

    return {
        "status": "ok",
        "site": site,
        "last_7d": last_7d,
        "previous_7d": prev_7d,
        "top_queries_7d": top_queries,
    }


def _agg(rows: list[dict]) -> dict:
    clicks = sum(r["clicks"] for r in rows)
    impressions = sum(r["impressions"] for r in rows)
    return {
        "clicks": int(clicks),
        "impressions": int(impressions),
        "ctr": round(clicks / impressions, 4) if impressions else None,
        "avg_position": round(
            sum(r["position"] * r["impressions"] for r in rows) / impressions, 2
        )
        if impressions
        else None,
    }


def _query(service, site: str, start: date, end: date) -> dict:
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": [],
        "rowLimit": 1,
    }
    resp = service.searchanalytics().query(siteUrl=site, body=body).execute()
    rows = resp.get("rows", [])
    if not rows:
        return {"clicks": 0, "impressions": 0, "ctr": None, "avg_position": None}
    r = rows[0]
    return {
        "clicks": int(r["clicks"]),
        "impressions": int(r["impressions"]),
        "ctr": round(r["ctr"], 4),
        "avg_position": round(r["position"], 2),
    }


def _query_top(service, site: str, start: date, end: date) -> list[dict]:
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["query"],
        "rowLimit": 20,
    }
    resp = service.searchanalytics().query(siteUrl=site, body=body).execute()
    return [
        {
            "query": r["keys"][0],
            "clicks": int(r["clicks"]),
            "impressions": int(r["impressions"]),
            "ctr": round(r["ctr"], 4),
            "position": round(r["position"], 2),
        }
        for r in resp.get("rows", [])
    ]
