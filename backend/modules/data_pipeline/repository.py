from __future__ import annotations

from datetime import date, timedelta

from .finmind_client import fetch_taiwan_stock_price
from .normalizer import normalize_price_series


def _date_window(lookback_days: int) -> tuple[str, str]:
    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)
    return start_date.isoformat(), end_date.isoformat()


def _to_ohlc_series(series: list[dict]) -> list[list]:
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


def fetch_finmind_quote(symbol: str, token: str) -> dict | None:
    start_date, end_date = _date_window(lookback_days=45)
    rows = fetch_taiwan_stock_price(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        token=token,
    )
    series = normalize_price_series(rows)
    if not series:
        return None

    latest = series[-1]
    return {
        "symbol": symbol,
        "name": symbol,
        "as_of_date": latest["date"],
        "open": latest["open"],
        "high": latest["high"],
        "low": latest["low"],
        "close": latest["close"],
        "change": latest["change"],
        "volume": latest["volume"],
        "source": "finmind",
        "is_fallback": False,
        "note": "",
    }


def fetch_finmind_history(symbol: str, days: int, token: str) -> dict | None:
    lookback_days = max(days * 4, 90)
    start_date, end_date = _date_window(lookback_days=lookback_days)
    rows = fetch_taiwan_stock_price(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        token=token,
    )
    series = normalize_price_series(rows)
    if not series:
        return None

    recent = series[-days:]
    return {
        "symbol": symbol,
        "name": symbol,
        "days": len(recent),
        "series": recent,
        "ohlc": _to_ohlc_series(recent),
        "source": "finmind",
        "is_fallback": False,
        "note": "",
    }

