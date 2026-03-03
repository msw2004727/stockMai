from __future__ import annotations

from .http_client import fetch_json
from .market_clock import current_taipei_now
from .market_snapshot_parser import parse_snapshot_row

TWSE_STOCK_DAY_ALL_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"


def fetch_twse_market_snapshots(timeout_seconds: int = 15) -> dict:
    payload = fetch_json(
        TWSE_STOCK_DAY_ALL_URL,
        timeout=timeout_seconds,
        allow_insecure_tls_fallback=True,
    )

    rows = _extract_rows(payload)
    fetched_rows = len(rows)
    fallback_date = current_taipei_now().date()

    by_symbol: dict[str, dict] = {}
    parsed_rows = 0
    for row in rows:
        parsed = parse_snapshot_row(row, fallback_date=fallback_date)
        if not parsed:
            continue
        parsed_rows += 1
        by_symbol[parsed["symbol"]] = parsed

    snapshots = list(by_symbol.values())
    valid_rows = len(snapshots)
    invalid_rows = max(fetched_rows - parsed_rows, 0)
    deduped_rows = max(parsed_rows - valid_rows, 0)

    return {
        "snapshots": snapshots,
        "fetched_rows": fetched_rows,
        "parsed_rows": parsed_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "deduped_rows": deduped_rows,
    }


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
