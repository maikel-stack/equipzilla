import argparse
import json
import sys

from .agent import _gather_metrics, generate_brief
from .notifiers import discord


def main() -> int:
    parser = argparse.ArgumentParser(prog="cmo", description="Equipzilla CMO daily brief")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo recopila métricas y las imprime; no llama a Claude ni a Discord.",
    )
    parser.add_argument(
        "--no-discord",
        action="store_true",
        help="Imprime el brief en stdout pero no lo envía a Discord.",
    )
    args = parser.parse_args()

    if args.dry_run:
        metrics = _gather_metrics()
        print(json.dumps(metrics, ensure_ascii=False, indent=2, default=str))
        return 0

    brief, _metrics = generate_brief()
    print(brief)

    if not args.no_discord:
        discord.send(brief)
    return 0


if __name__ == "__main__":
    sys.exit(main())
