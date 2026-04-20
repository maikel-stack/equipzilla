import os
from datetime import datetime, timedelta, timezone

import httpx


def _credentials_status() -> str | None:
    if not os.getenv("RESPOND_IO_API_KEY"):
        return "missing_env: RESPOND_IO_API_KEY"
    return None


def fetch_metrics() -> dict:
    err = _credentials_status()
    if err:
        return {"status": "unconfigured", "reason": err}

    token = os.environ["RESPOND_IO_API_KEY"]
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=7)

    headers = {"Authorization": f"Bearer {token}"}
    base = "https://api.respond.io/v2"

    contacts_7d = 0
    msgs_in = 0
    msgs_out = 0
    try:
        with httpx.Client(headers=headers, timeout=30.0) as client:
            r = client.get(
                f"{base}/contact/list",
                params={
                    "limit": 100,
                    "createdAt[gte]": int(since.timestamp() * 1000),
                },
            )
            if r.status_code == 200:
                contacts_7d = len(r.json().get("data", []) or [])

            r = client.get(
                f"{base}/message/list",
                params={
                    "limit": 100,
                    "createdAt[gte]": int(since.timestamp() * 1000),
                },
            )
            if r.status_code == 200:
                for m in r.json().get("data", []) or []:
                    if m.get("direction") == "incoming":
                        msgs_in += 1
                    else:
                        msgs_out += 1
    except httpx.HTTPError as e:
        return {"status": "error", "reason": str(e)}

    return {
        "status": "ok",
        "window_days": 7,
        "new_contacts": contacts_7d,
        "messages_incoming": msgs_in,
        "messages_outgoing": msgs_out,
        "reply_ratio": round(msgs_in / msgs_out, 2) if msgs_out else None,
    }
