from __future__ import annotations

from datetime import date

from .http_client import fetch_json
from .market_clock import current_taipei_now
from .market_snapshot_parser import parse_snapshot_row

TWSE_STOCK_DAY_ALL_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"


def fetch_twse_market_snapshots(timeout_seconds: int = 15) -> list[dict]:
    payload = fetch_json(
        TWSE_STOCK_DAY_ALL_URL,
        timeout=timeout_seconds,
        allow_insecure_tls_fallback=True,
    )

    rows = _extract_rows(payload)
    fallback_date = current_taipei_now().date()
    by_symbol: dict[str, dict] = {}
    for row in rows:
        parsed = parse_snapshot_row(row, fallback_date=fallback_date)
        if not parsed:
            continue
        by_symbol[parsed["symbol"]] = parsed

    return list(by_symbol.values())


def _extract_rows(payload: object) -> list[object]:
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    for key in ("data", "aaData", "results", "rows", "list"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return rows

    for value in payload.values():
        if isinstance(value, list):
            return value

    return []
