from __future__ import annotations

from datetime import date, timedelta
from urllib.parse import urlencode

from .http_client import fetch_json
from .parsers import extract_stock_name

TWSE_DAY_REPORT_URL = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"


def month_candidates(today: date, count: int) -> list[date]:
    months = [today.replace(day=1)]
    while len(months) < count:
        prev = (months[-1] - timedelta(days=1)).replace(day=1)
        months.append(prev)
    return months


def fetch_twse_month(symbol: str, month: date, timeout: int = 8) -> tuple[str, list[list[str]]]:
    query = urlencode(
        {
            "response": "json",
            "date": month.strftime("%Y%m%d"),
            "stockNo": symbol,
        }
    )
    payload = fetch_json(
        f"{TWSE_DAY_REPORT_URL}?{query}",
        timeout=timeout,
        allow_insecure_tls_fallback=True,
    )

    rows = payload.get("data") or []
    if payload.get("stat") != "OK" or not rows:
        return symbol, []

    return extract_stock_name(payload.get("title", ""), symbol), rows
