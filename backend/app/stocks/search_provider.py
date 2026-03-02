from __future__ import annotations

from .http_client import fetch_json
from .search_mapper import parse_search_row


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


def fetch_stock_universe_from_sources(
    sources: list[dict],
    *,
    timeout_seconds: int = 8,
) -> list[dict]:
    merged: dict[str, dict] = {}

    for source in sources:
        url = str(source.get("url") or "")
        if not url:
            continue

        market = str(source.get("market") or "unknown")
        source_name = str(source.get("source") or "unknown")

        try:
            payload = fetch_json(
                url,
                timeout=timeout_seconds,
                allow_insecure_tls_fallback=True,
            )
        except Exception:
            continue

        for row in _extract_rows(payload):
            mapped = parse_search_row(row, market=market, source=source_name)
            if not mapped:
                continue

            symbol = mapped["symbol"]
            existing = merged.get(symbol)
            if not existing:
                merged[symbol] = mapped
                continue

            old_name = str(existing.get("name") or symbol)
            new_name = str(mapped.get("name") or symbol)
            if old_name == symbol and new_name != symbol:
                merged[symbol] = mapped

    return list(merged.values())

