import argparse
import base64
import csv
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

MODEL = "gemini-2.5-flash-image"
API = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

PROMPTS_BY_CATEGORY = {
    "elevadores-tijera": "yellow electric or diesel scissor lift aerial work platform, lowered position, industrial design",
    "brazo-articulado": "articulated boom lift (knuckle boom) aerial work platform, outriggers, industrial yellow paint",
    "elevadores-telescopicos": "telescopic boom lift aerial work platform, long extended boom, heavy outriggers",
    "camiones-plataforma-cesta": "truck-mounted aerial platform (cherry picker), mounted on a white commercial truck chassis, boom extended at moderate angle",
    "elevadores-unipersonales": "single-person vertical mast lift, compact vertical lift for one operator, tight footprint",
    "grupos-electrogenos": "industrial diesel generator set in a noise-attenuated yellow canopy, lifting points visible",
    "carretilla-diesel": "diesel counterbalance forklift truck, industrial orange/yellow paint, forks lowered",
    "carretilla-electricas": "electric counterbalance forklift truck, battery-powered, sit-down operator cab",
    "manipuladores-telescopicos": "telehandler / telescopic handler, extended boom with forks, agricultural/construction design",
    "miniexcavadoras": "mini excavator / compact tracked excavator, yellow industrial paint, bucket attached, tracks",
    "transpaletas-electricas": "pedestrian electric pallet truck, walk-behind warehouse equipment",
    "apilador-electrico": "walk-behind electric pallet stacker, narrow chassis, industrial blue/orange",
    "compresor-de-aire": "industrial towable air compressor unit in yellow enclosure, twin wheels, tow bar",
    "dumpers": "site dumper truck, front tip skip, 4WD construction dumper, yellow or orange paint",
    "minicargadoras": "compact skid steer loader, bucket attached, industrial yellow paint",
    "rodillo-compactador": "vibratory tandem drum roller compactor, industrial yellow, road construction equipment",
}

BASE_STYLE = (
    "Professional product photography, pure seamless white background, soft diffused studio lighting, "
    "3/4 angle view, photorealistic, high resolution, sharp focus, no text or logos visible, no people, "
    "commercial catalog style."
)


def _prompt_for(product: dict) -> str:
    cat = product["parentCategory"]
    base = PROMPTS_BY_CATEGORY.get(cat, "industrial rental machinery")
    spec = product["name"].lower()
    return f"{base}. Specification: {spec}. {BASE_STYLE}"


def generate_image(product: dict, out_dir: Path, retries: int = 3) -> dict:
    key = os.environ["GEMINI_API_KEY"]
    out_path = out_dir / f"{product['machineCode']}.png"
    if out_path.exists() and out_path.stat().st_size > 0:
        return {"id": product["id"], "code": product["machineCode"], "status": "cached", "path": str(out_path)}

    prompt = _prompt_for(product)
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }

    last_err = None
    for attempt in range(retries):
        try:
            r = httpx.post(f"{API}?key={key}", json=body, timeout=180.0)
            if r.status_code == 429:
                wait = 2 ** attempt
                print(f"  {product['machineCode']}: 429, retry in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            if r.status_code != 200:
                return {"id": product["id"], "code": product["machineCode"], "status": f"http_{r.status_code}", "error": r.text[:200]}
            parts = r.json()["candidates"][0]["content"]["parts"]
            for p in parts:
                if "inlineData" in p:
                    out_path.write_bytes(base64.b64decode(p["inlineData"]["data"]))
                    return {"id": product["id"], "code": product["machineCode"], "status": "ok", "path": str(out_path)}
            return {"id": product["id"], "code": product["machineCode"], "status": "no_image_returned"}
        except httpx.HTTPError as e:
            last_err = str(e)
            time.sleep(2 ** attempt)
    return {"id": product["id"], "code": product["machineCode"], "status": "error", "error": last_err or "unknown"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(Path(__file__).parent / "products_copy.csv"))
    ap.add_argument("--out", default=str(Path(__file__).parent / "images"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", help="Only generate for this machineCode (comma-separated)")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.csv, encoding="utf-8") as f:
        products = list(csv.DictReader(f))
    for p in products:
        p["id"] = int(p["id"])
        p["price"] = float(p["price"]) if p["price"] else 0.0

    if args.only:
        codes = {c.strip() for c in args.only.split(",")}
        products = [p for p in products if p["machineCode"] in codes]
    if args.limit:
        products = products[: args.limit]

    print(f"Generating {len(products)} images with {MODEL} in {out_dir} ({args.workers} workers)...", file=sys.stderr)
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(generate_image, p, out_dir) for p in products]
        for i, fut in enumerate(as_completed(futures), 1):
            res = fut.result()
            results.append(res)
            status = res["status"]
            mark = "✓" if status in ("ok", "cached") else "✗"
            print(f"  [{i:>2}/{len(products)}] {mark} {res['code']} ({status})", file=sys.stderr)

    ok = sum(1 for r in results if r["status"] in ("ok", "cached"))
    print(f"\nDone. {ok}/{len(results)} images available in {out_dir}", file=sys.stderr)
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
