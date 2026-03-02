from __future__ import annotations

from datetime import date, timedelta

from backend.modules.data_pipeline import fetch_finmind_history, fetch_finmind_quote

from ..config import get_settings
from .constants import DEMO_QUOTES
from .parsers import parse_daily_row, to_ohlc_series
from .provider import fetch_twse_month, month_candidates


class SymbolNotFoundError(Exception):
    pass


def _fetch_quote_from_finmind(symbol: str) -> dict | None:
    token = get_settings().finmind_token
    return fetch_finmind_quote(symbol, token=token)


def _fetch_history_from_finmind(symbol: str, days: int) -> dict | None:
    token = get_settings().finmind_token
    return fetch_finmind_history(symbol, days=days, token=token)


def _fetch_quote_from_twse(symbol: str) -> dict:
    last_error = None
    for month in month_candidates(date.today(), count=2):
        try:
            name, rows = fetch_twse_month(symbol, month)
        except Exception as exc:
            last_error = exc
            continue

        if not rows:
            continue

        parsed_rows = [parsed for raw in rows if (parsed := parse_daily_row(raw))]
        if not parsed_rows:
            continue

        latest = parsed_rows[-1]
        return {
            "symbol": symbol,
            "name": name,
            "as_of_date": latest["date"],
            "open": latest["open"],
            "high": latest["high"],
            "low": latest["low"],
            "close": latest["close"],
            "change": latest["change"],
            "volume": latest["volume"],
            "source": "twse",
            "is_fallback": False,
            "note": "",
        }

    raise RuntimeError(f"Failed to fetch TWSE quote for {symbol}") from last_error


def _fetch_history_from_twse(symbol: str, days: int) -> dict:
    series_by_date = {}
    name = symbol
    last_error = None

    for month in month_candidates(date.today(), count=6):
        try:
            twse_name, rows = fetch_twse_month(symbol, month)
        except Exception as exc:
            last_error = exc
            continue

        if not rows:
            continue

        name = twse_name
        for raw in rows:
            parsed = parse_daily_row(raw)
            if parsed:
                series_by_date[parsed["date"]] = parsed

        if len(series_by_date) >= days:
            break

    if not series_by_date:
        raise RuntimeError(f"Failed to fetch TWSE history for {symbol}") from last_error

    series = [series_by_date[d] for d in sorted(series_by_date.keys())][-days:]
    return {
        "symbol": symbol,
        "name": name,
        "days": len(series),
        "series": series,
        "ohlc": to_ohlc_series(series),
        "source": "twse",
        "is_fallback": False,
        "note": "",
    }


def _build_demo_history(symbol: str, days: int) -> list[dict]:
    base = DEMO_QUOTES[symbol]
    today = date.today()
    delta_pattern = [-0.017, -0.011, -0.006, 0.002, 0.007, 0.013, 0.008, -0.003, 0.004, 0.009]
    series = []

    for idx in range(days):
        d = today - timedelta(days=days - 1 - idx)
        ratio = delta_pattern[idx % len(delta_pattern)]
        close = round(base["close"] * (1 + ratio), 2)
        open_price = round(close * (1 - 0.003 + (idx % 3) * 0.001), 2)
        high = round(max(open_price, close) * 1.004, 2)
        low = round(min(open_price, close) * 0.996, 2)
        series.append(
            {
                "date": d.isoformat(),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "change": round(close - open_price, 2),
                "volume": int(base["volume"] * (0.82 + (idx % 5) * 0.045)),
            }
        )

    return series


def get_quote(symbol: str) -> dict:
    try:
        finmind_quote = _fetch_quote_from_finmind(symbol)
        if finmind_quote:
            return finmind_quote
    except Exception:
        pass

    try:
        return _fetch_quote_from_twse(symbol)
    except Exception:
        demo = DEMO_QUOTES.get(symbol)
        if not demo:
            raise SymbolNotFoundError(f"No quote data found for symbol={symbol}")

        return {
            "symbol": symbol,
            "name": demo["name"],
            "as_of_date": date.today().isoformat(),
            "open": demo["open"],
            "high": demo["high"],
            "low": demo["low"],
            "close": demo["close"],
            "change": demo["change"],
            "volume": demo["volume"],
            "source": "demo",
            "is_fallback": True,
            "note": "TWSE data fetch failed; returned local demo data.",
        }


def get_history(symbol: str, days: int) -> dict:
    try:
        finmind_history = _fetch_history_from_finmind(symbol, days=days)
        if finmind_history:
            return finmind_history
    except Exception:
        pass

    try:
        return _fetch_history_from_twse(symbol, days=days)
    except Exception:
        demo = DEMO_QUOTES.get(symbol)
        if not demo:
            raise SymbolNotFoundError(f"No history data found for symbol={symbol}")

        series = _build_demo_history(symbol, days)
        return {
            "symbol": symbol,
            "name": demo["name"],
            "days": days,
            "series": series,
            "ohlc": to_ohlc_series(series),
            "source": "demo",
            "is_fallback": True,
            "note": "TWSE data fetch failed; returned local demo history data.",
        }
