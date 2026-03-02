from __future__ import annotations

import re


def parse_roc_date(raw: str) -> str:
    # TWSE date format: "114/03/02" -> 2025-03-02
    year_roc, month, day = raw.split("/")
    return f"{int(year_roc) + 1911:04d}-{int(month):02d}-{int(day):02d}"


def parse_float(raw: str) -> float:
    value = raw.replace(",", "").replace("X", "").replace("+", "").replace(" ", "")
    if value in {"", "--"}:
        raise ValueError("invalid numeric value")
    return float(value)


def parse_int(raw: str) -> int:
    return int(raw.replace(",", ""))


def extract_stock_name(title: str, symbol: str) -> str:
    # Example title: "... 2330 台積電 各日成交資訊"
    match = re.search(rf"\b{symbol}\s+(.+?)\s+各日成交資訊", title)
    if match:
        return match.group(1).strip()
    return symbol


def parse_daily_row(row: list[str]) -> dict | None:
    try:
        return {
            "date": parse_roc_date(row[0]),
            "open": parse_float(row[3]),
            "high": parse_float(row[4]),
            "low": parse_float(row[5]),
            "close": parse_float(row[6]),
            "change": parse_float(row[7]),
            "volume": parse_int(row[1]),
        }
    except Exception:
        return None


def to_ohlc_series(series: list[dict]) -> list[list]:
    return [
        [
            row["date"],
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["volume"],
        ]
        for row in series
    ]
