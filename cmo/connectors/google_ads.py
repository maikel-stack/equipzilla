import os
from datetime import date, timedelta

REQUIRED_ENV = (
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "GOOGLE_ADS_CLIENT_ID",
    "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN",
    "GOOGLE_ADS_CUSTOMER_ID",
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

    from google.ads.googleads.client import GoogleAdsClient

    client = GoogleAdsClient.load_from_dict(
        {
            "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
            "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
            "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
            "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
            or os.environ["GOOGLE_ADS_CUSTOMER_ID"],
            "use_proto_plus": True,
        }
    )
    customer_id = os.environ["GOOGLE_ADS_CUSTOMER_ID"].replace("-", "")
    ga_service = client.get_service("GoogleAdsService")

    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    summary = _query_summary(ga_service, customer_id, yesterday, today)
    prev = _query_summary(ga_service, customer_id, yesterday - timedelta(days=1), yesterday)
    week = _query_summary(ga_service, customer_id, week_ago, today)
    top_terms = _query_top_search_terms(ga_service, customer_id, week_ago, today)

    return {
        "status": "ok",
        "yesterday": summary,
        "day_before": prev,
        "last_7d": week,
        "top_search_terms_7d": top_terms,
    }


def _query_summary(service, customer_id: str, start: date, end: date) -> dict:
    query = f"""
        SELECT
            metrics.cost_micros,
            metrics.clicks,
            metrics.impressions,
            metrics.conversions,
            metrics.conversions_value
        FROM customer
        WHERE segments.date BETWEEN '{start.isoformat()}' AND '{end.isoformat()}'
    """
    cost = clicks = impressions = conv = conv_value = 0.0
    for row in service.search(customer_id=customer_id, query=query):
        m = row.metrics
        cost += m.cost_micros / 1_000_000
        clicks += m.clicks
        impressions += m.impressions
        conv += m.conversions
        conv_value += m.conversions_value
    return {
        "spend_eur": round(cost, 2),
        "clicks": int(clicks),
        "impressions": int(impressions),
        "ctr": round(clicks / impressions, 4) if impressions else None,
        "cpc_eur": round(cost / clicks, 2) if clicks else None,
        "conversions": round(conv, 2),
        "cpa_eur": round(cost / conv, 2) if conv else None,
        "roas": round(conv_value / cost, 2) if cost else None,
    }


def _query_top_search_terms(service, customer_id: str, start: date, end: date) -> list[dict]:
    query = f"""
        SELECT
            search_term_view.search_term,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM search_term_view
        WHERE segments.date BETWEEN '{start.isoformat()}' AND '{end.isoformat()}'
        ORDER BY metrics.cost_micros DESC
        LIMIT 15
    """
    out = []
    for row in service.search(customer_id=customer_id, query=query):
        out.append(
            {
                "term": row.search_term_view.search_term,
                "clicks": row.metrics.clicks,
                "spend_eur": round(row.metrics.cost_micros / 1_000_000, 2),
                "conversions": round(row.metrics.conversions, 2),
            }
        )
    return out
