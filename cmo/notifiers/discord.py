import os

import httpx

DISCORD_LIMIT = 2000


def send(content: str) -> None:
    url = os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        return
    for chunk in _split(content, DISCORD_LIMIT):
        r = httpx.post(url, json={"content": chunk}, timeout=30.0)
        r.raise_for_status()


def _split(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    buf = ""
    for line in text.splitlines(keepends=True):
        if len(buf) + len(line) > limit:
            chunks.append(buf)
            buf = ""
        buf += line
    if buf:
        chunks.append(buf)
    return chunks
