from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.modules.data_pipeline import fetch_finmind_history, upsert_price_series


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill stock price history into PostgreSQL.")
    parser.add_argument(
        "--symbols",
        default="2330,2317,0050",
        help="Comma-separated stock symbols. Example: 2330,2317,0050",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=180,
        help="How many recent days to fetch from FinMind.",
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", ""),
        help="PostgreSQL connection string. Defaults to env DATABASE_URL.",
    )
    parser.add_argument(
        "--finmind-token",
        default=os.getenv("FINMIND_TOKEN", ""),
        help="FinMind token. Defaults to env FINMIND_TOKEN.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    symbols = [token.strip() for token in args.symbols.split(",") if token.strip()]

    if not args.database_url:
        print("Error: missing DATABASE_URL (use --database-url or env).")
        return 1
    if not args.finmind_token:
        print("Error: missing FINMIND_TOKEN (use --finmind-token or env).")
        return 1
    if not symbols:
        print("Error: no symbols provided.")
        return 1

    total_rows = 0
    for symbol in symbols:
        history = fetch_finmind_history(symbol=symbol, days=max(args.days, 1), token=args.finmind_token)
        if not history:
            print(f"[{symbol}] no data fetched.")
            continue

        rows = upsert_price_series(
            database_url=args.database_url,
            symbol=symbol,
            series=history["series"],
            source="finmind",
        )
        total_rows += rows
        print(f"[{symbol}] upserted {rows} rows.")

    print(f"Done. Total upserted rows: {total_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
