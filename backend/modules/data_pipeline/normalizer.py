from __future__ import annotations

from datetime import date


def _to_float(value: object) -> float:
    if value in {None, ""}:
        raise ValueError("empty numeric value")
    return float(str(value).replace(",", "").strip())


def _to_int(value: object) -> int:
    if value in {None, ""}:
        raise ValueError("empty integer value")
    return int(float(str(value).replace(",", "").strip()))


def _to_iso_date(raw: object) -> str:
    if not isinstance(raw, str):
        raise ValueError("date must be string")
    return date.fromisoformat(raw.strip()).isoformat()


def normalize_price_row(row: dict) -> dict | None:
    """Map FinMind raw row to internal OHLC schema."""
    try:
        open_price = _to_float(row.get("open"))
        close_price = _to_float(row.get("close"))
        change = row.get("spread")
        if change in {None, ""}:
            change = round(close_price - open_price, 2)
        else:
            change = _to_float(change)

        return {
            "date": _to_iso_date(row.get("date")),
            "open": open_price,
            "high": _to_float(row.get("max")),
            "low": _to_float(row.get("min")),
            "close": close_price,
            "change": change,
            "volume": _to_int(row.get("Trading_Volume")),
        }
    except Exception:
        return None


def normalize_price_series(rows: list[dict]) -> list[dict]:
    """Filter invalid rows, dedupe by date, and sort ascending."""
    by_date: dict[str, dict] = {}
    for row in rows:
        normalized = normalize_price_row(row)
        if normalized:
            by_date[normalized["date"]] = normalized

    return [by_date[d] for d in sorted(by_date.keys())]

