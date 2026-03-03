from __future__ import annotations

from datetime import date, datetime
from urllib.parse import urlencode

from backend.modules.data_pipeline import fetch_finmind_quote

from .http_client import fetch_json
from .parsers import parse_daily_row
from .provider import TWSE_DAY_REPORT_URL, fetch_twse_month, month_candidates

TWSE_REALTIME_URL = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"


class QuoteProviderUnavailableError(Exception):
    pass


def fetch_quote_from_provider_chain(symbol: str, finmind_token: str, timeout_seconds: int = 8) -> dict | None:
    failed_count = 0
    provider_count = 0

    provider_count += 1
    try:
        realtime = _fetch_twse_realtime_quote(symbol=symbol, timeout=timeout_seconds)
        if realtime:
            return realtime
    except Exception:
        failed_count += 1

    if finmind_token:
        provider_count += 1
        try:
            finmind_daily = _fetch_finmind_daily_quote(symbol=symbol, token=finmind_token)
            if finmind_daily:
                return finmind_daily
        except Exception:
            failed_count += 1

    provider_count += 1
    try:
        twse_daily = _fetch_twse_daily_quote(symbol=symbol, timeout=timeout_seconds)
        if twse_daily:
            return twse_daily
    except Exception:
        failed_count += 1

    if failed_count >= provider_count:
        raise QuoteProviderUnavailableError("All quote providers failed.")

    return None


def _fetch_twse_realtime_quote(symbol: str, timeout: int = 8) -> dict | None:
    channels = [f"tse_{symbol}.tw", f"otc_{symbol}.tw"]
    for channel in channels:
        payload = _fetch_twse_realtime_payload(channel=channel, timeout=timeout)
        parsed = _parse_twse_realtime_payload(payload=payload, symbol=symbol)
        if parsed:
            return parsed
    return None


def _fetch_twse_realtime_payload(channel: str, timeout: int = 8) -> dict:
    query = urlencode(
        {
            "ex_ch": channel,
            "json": 1,
            "delay": 0,
            "_": int(datetime.now().timestamp() * 1000),
        }
    )
    return fetch_json(
        f"{TWSE_REALTIME_URL}?{query}",
        timeout=timeout,
        allow_insecure_tls_fallback=True,
    )


def _parse_twse_realtime_payload(payload: dict, symbol: str) -> dict | None:
    rows = payload.get("msgArray")
    if not isinstance(rows, list) or not rows:
        return None

    row = rows[0] if isinstance(rows[0], dict) else None
    if not row:
        return None

    last_trade = _to_float(row.get("z"))
    bid = _first_level_price(row.get("b"))
    ask = _first_level_price(row.get("a"))
    prev_close = _to_float(row.get("y"))
    close, price_source = _resolve_realtime_close(
        last_trade=last_trade,
        bid=bid,
        ask=ask,
        prev_close=prev_close,
    )
    if close is None:
        return None

    open_price = _to_float(row.get("o"))
    high = _to_float(row.get("h"))
    low = _to_float(row.get("l"))
    volume = _to_int(row.get("v")) or _to_int(row.get("tv")) or 0

    as_of_date = _parse_yyyymmdd(row.get("d")) or date.today().isoformat()
    quote_time = _build_quote_time(as_of_date=as_of_date, raw_time=row.get("t"))
    change = close - (prev_close if prev_close is not None else close)

    return {
        "symbol": symbol,
        "name": str(row.get("n") or symbol),
        "as_of_date": as_of_date,
        "quote_time": quote_time,
        "open": _fallback_price(open_price, close),
        "high": _fallback_price(high, close),
        "low": _fallback_price(low, close),
        "close": close,
        "change": round(change, 6),
        "volume": int(volume),
        "source": "twse_realtime",
        "source_priority": "realtime_primary",
        "is_realtime": bool(price_source != "prev_close"),
        "market_state": _infer_market_state(row.get("t"), close, prev_close),
        "delay_seconds": 0,
        "is_fallback": False,
        "note": _build_realtime_note(price_source),
    }


def _fetch_finmind_daily_quote(symbol: str, token: str) -> dict | None:
    quote = fetch_finmind_quote(symbol=symbol, token=token)
    if not quote:
        return None
    return _as_daily_quote_meta(quote=quote, source_priority="daily_fallback")


def _fetch_twse_daily_quote(symbol: str, timeout: int = 8) -> dict | None:
    for month in month_candidates(date.today(), count=2):
        name, rows = fetch_twse_month(symbol=symbol, month=month, timeout=timeout)
        if not rows:
            continue

        parsed_rows = [parsed for raw in rows if (parsed := parse_daily_row(raw))]
        if not parsed_rows:
            continue

        latest = parsed_rows[-1]
        quote = {
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
        return _as_daily_quote_meta(quote=quote, source_priority="daily_fallback")
    return None


def _as_daily_quote_meta(quote: dict, source_priority: str) -> dict:
    out = dict(quote)
    as_of_date = str(out.get("as_of_date", ""))
    out["quote_time"] = out.get("quote_time") or (f"{as_of_date} 14:00:00" if as_of_date else "")
    out["market_state"] = str(out.get("market_state") or "daily_close")
    out["is_realtime"] = bool(out.get("is_realtime", False))
    out["delay_seconds"] = out.get("delay_seconds")
    out["source_priority"] = str(out.get("source_priority") or source_priority)
    return out


def _parse_yyyymmdd(raw: object) -> str | None:
    text = str(raw or "").strip()
    if len(text) != 8 or not text.isdigit():
        return None
    return f"{text[:4]}-{text[4:6]}-{text[6:8]}"


def _build_quote_time(as_of_date: str, raw_time: object) -> str:
    parsed_time = str(raw_time or "").strip()
    if len(parsed_time) >= 5:
        return f"{as_of_date} {parsed_time}"
    return f"{as_of_date} 00:00:00"


def _infer_market_state(raw_time: object, close: float, prev_close: float | None) -> str:
    if str(raw_time or "").strip():
        return "trading"
    if prev_close is not None and close != prev_close:
        return "post_close"
    return "unknown"


def _resolve_realtime_close(
    *,
    last_trade: float | None,
    bid: float | None,
    ask: float | None,
    prev_close: float | None,
) -> tuple[float | None, str]:
    if last_trade is not None:
        return last_trade, "last_trade"

    if bid is not None and ask is not None:
        if ask >= bid:
            return round((bid + ask) / 2, 6), "book_mid"
        return bid, "book_bid"

    if bid is not None:
        return bid, "book_bid"
    if ask is not None:
        return ask, "book_ask"

    if prev_close is not None:
        return prev_close, "prev_close"

    return None, "none"


def _first_level_price(raw: object) -> float | None:
    text = str(raw or "").strip()
    if not text:
        return None

    for part in text.split("_"):
        parsed = _to_float(part)
        if parsed is not None:
            return parsed
    return None


def _build_realtime_note(price_source: str) -> str:
    if price_source in {"last_trade", "none"}:
        return ""
    if price_source == "prev_close":
        return "twse_realtime missing trade/book, fallback to prev_close"
    return f"twse_realtime price inferred from {price_source}"


def _to_float(raw: object) -> float | None:
    text = str(raw or "").replace(",", "").strip()
    if text in {"", "-", "--"}:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _to_int(raw: object) -> int | None:
    text = str(raw or "").replace(",", "").strip()
    if text in {"", "-", "--"}:
        return None
    try:
        return int(float(text))
    except Exception:
        return None


def _fallback_price(parsed: float | None, fallback: float) -> float:
    if parsed is None:
        return fallback
    return parsed
