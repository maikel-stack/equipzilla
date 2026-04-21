import os
from collections import Counter
from datetime import datetime, timedelta, timezone

import httpx

PIPELINE_ACTIVE = 6
STAGE_OFERTA_ENVIADA = 37
STAGE_OFERTA_ACEPTADA = 38
STAGE_SEGUIMIENTO = 27
QUOTE_NOTE_TAG = "[EQUIPZILLA_QUOTE]"


def _client() -> httpx.Client:
    domain = os.environ["PIPEDRIVE_DOMAIN"]
    token = os.environ["PIPEDRIVE_API_TOKEN"]
    return httpx.Client(
        base_url=f"https://{domain}.pipedrive.com/v1",
        params={"api_token": token},
        timeout=30.0,
    )


def _paginate(client: httpx.Client, path: str, params: dict | None = None) -> list[dict]:
    out: list[dict] = []
    start = 0
    limit = 500
    while True:
        r = client.get(path, params={**(params or {}), "start": start, "limit": limit})
        r.raise_for_status()
        body = r.json()
        items = body.get("data") or []
        out.extend(items)
        pag = (body.get("additional_data") or {}).get("pagination") or {}
        if not pag.get("more_items_in_collection"):
            break
        start = pag.get("next_start", start + limit)
    return out


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace(" ", "T")).replace(tzinfo=timezone.utc)


def fetch_metrics() -> dict:
    now = datetime.now(timezone.utc)
    today = now.date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    with _client() as client:
        deals = _paginate(
            client,
            "/deals",
            {"status": "all_not_deleted", "filter_id": "", "sort": "add_time DESC"},
        )

    active = [d for d in deals if d.get("pipeline_id") == PIPELINE_ACTIVE]

    new_today = []
    new_yesterday = []
    new_7d = []
    won_7d = []
    lost_7d = []
    by_stage_today: Counter[int] = Counter()

    for d in active:
        added = _parse_dt(d.get("add_time"))
        if not added:
            continue
        added_date = added.date()
        if added_date == today:
            new_today.append(d)
            by_stage_today[d.get("stage_id")] += 1
        if added_date == yesterday:
            new_yesterday.append(d)
        if added_date >= week_ago:
            new_7d.append(d)

        won_at = _parse_dt(d.get("won_time"))
        if won_at and won_at.date() >= week_ago:
            won_7d.append(d)
        lost_at = _parse_dt(d.get("lost_time"))
        if lost_at and lost_at.date() >= week_ago:
            lost_7d.append(d)

    open_offers = [
        d for d in active if d.get("stage_id") == STAGE_OFERTA_ENVIADA and d.get("status") == "open"
    ]

    stuck_offers = []
    for d in open_offers:
        updated = _parse_dt(d.get("update_time"))
        if updated and (now - updated) > timedelta(hours=23):
            stuck_offers.append(
                {
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "value": d.get("value"),
                    "hours_since_update": int((now - updated).total_seconds() // 3600),
                }
            )

    won_count = len(won_7d)
    decided_count = won_count + len(lost_7d)
    win_rate_7d = (won_count / decided_count) if decided_count else None

    return {
        "as_of_utc": now.isoformat(),
        "leads": {
            "new_today": len(new_today),
            "new_yesterday": len(new_yesterday),
            "new_7d": len(new_7d),
            "delta_vs_yesterday_pct": _pct_change(len(new_today), len(new_yesterday)),
        },
        "pipeline": {
            "active_total": len(active),
            "open_offers_stage_37": len(open_offers),
            "stuck_offers_over_23h": stuck_offers,
            "by_stage_today": dict(by_stage_today),
        },
        "conversion_7d": {
            "won": won_count,
            "lost": len(lost_7d),
            "win_rate": round(win_rate_7d, 3) if win_rate_7d is not None else None,
            "won_value_eur": round(sum(float(d.get("value") or 0) for d in won_7d), 2),
        },
        "top_new_today": [
            {
                "id": d.get("id"),
                "title": d.get("title"),
                "value": d.get("value"),
                "stage_id": d.get("stage_id"),
            }
            for d in new_today[:10]
        ],
    }


def _pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)
