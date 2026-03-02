from __future__ import annotations

from datetime import date

from backend.modules.data_pipeline import (
    fetch_finmind_history,
    load_latest_quote,
    load_recent_history,
    upsert_price_series,
)
from backend.modules.feature_engineering import (
    compute_indicator_series,
    compute_latest_indicators,
    get_indicator_engine,
)

from ..config import get_settings
from .parsers import parse_daily_row, to_ohlc_series
from .provider import fetch_twse_month, month_candidates
from .quote_provider import QuoteProviderUnavailableError, fetch_quote_from_provider_chain


class SymbolNotFoundError(Exception):
    pass


class DataUnavailableError(Exception):
    pass


def _load_quote_from_postgres(symbol: str) -> dict | None:
    settings = get_settings()
    return load_latest_quote(
        database_url=settings.database_url,
        symbol=symbol,
        max_age_days=5,
    )


def _load_history_from_postgres(symbol: str, days: int) -> dict | None:
    settings = get_settings()
    return load_recent_history(
        database_url=settings.database_url,
        symbol=symbol,
        days=days,
        max_age_days=7,
    )


def _persist_series_to_postgres(symbol: str, series: list[dict], source: str) -> None:
    settings = get_settings()
    upsert_price_series(
        database_url=settings.database_url,
        symbol=symbol,
        series=series,
        source=source,
    )


def _fetch_history_from_finmind(symbol: str, days: int) -> dict | None:
    token = get_settings().finmind_token
    return fetch_finmind_history(symbol, days=days, token=token)


def _fetch_quote_from_provider_chain(symbol: str) -> dict | None:
    token = get_settings().finmind_token
    return fetch_quote_from_provider_chain(
        symbol=symbol,
        finmind_token=token,
        timeout_seconds=8,
    )


def _fetch_history_from_twse(symbol: str, days: int) -> dict | None:
    series_by_date = {}
    name = symbol
    has_fetch_error = False

    for month in month_candidates(date.today(), count=6):
        try:
            twse_name, rows = fetch_twse_month(symbol, month)
        except Exception as exc:
            has_fetch_error = True
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
        if has_fetch_error:
            raise RuntimeError(f"Failed to fetch TWSE history for {symbol}")
        return None

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


def _build_freshness(as_of_date: str, max_age_days: int) -> dict:
    parsed: date | None = None
    try:
        parsed = date.fromisoformat(str(as_of_date))
    except Exception:
        parsed = None

    if parsed is None:
        return {
            "as_of_date": str(as_of_date),
            "age_days": None,
            "is_fresh": False,
            "max_age_days": int(max_age_days),
        }

    age_days = (date.today() - parsed).days
    return {
        "as_of_date": parsed.isoformat(),
        "age_days": int(age_days),
        "is_fresh": age_days <= max(max_age_days, 0),
        "max_age_days": int(max_age_days),
    }


def _with_freshness(payload: dict, max_age_days: int) -> dict:
    out = dict(payload)
    as_of_date = str(out.get("as_of_date", ""))
    out["freshness"] = _build_freshness(as_of_date, max_age_days=max_age_days)
    return out


def _with_quote_runtime_meta(payload: dict, default_priority: str) -> dict:
    out = dict(payload)
    as_of_date = str(out.get("as_of_date", ""))
    out["quote_time"] = out.get("quote_time") or (f"{as_of_date} 14:00:00" if as_of_date else "")
    out["market_state"] = str(out.get("market_state") or "unknown")
    out["is_realtime"] = bool(out.get("is_realtime", False))
    out["delay_seconds"] = out.get("delay_seconds")
    out["source_priority"] = str(out.get("source_priority") or default_priority)
    return out


def get_quote(symbol: str) -> dict:
    try:
        cached = _load_quote_from_postgres(symbol)
        if cached:
            with_meta = _with_quote_runtime_meta(cached, default_priority="cache")
            return _with_freshness(with_meta, max_age_days=5)
    except Exception:
        pass

    try:
        quote = _fetch_quote_from_provider_chain(symbol)
        if quote:
            with_meta = _with_quote_runtime_meta(quote, default_priority="daily_fallback")
            _persist_series_to_postgres(
                symbol=symbol,
                series=[
                    {
                        "date": with_meta["as_of_date"],
                        "open": with_meta["open"],
                        "high": with_meta["high"],
                        "low": with_meta["low"],
                        "close": with_meta["close"],
                        "change": with_meta["change"],
                        "volume": with_meta["volume"],
                    }
                ],
                source=with_meta.get("source", "unknown"),
            )
            return _with_freshness(with_meta, max_age_days=5)
    except QuoteProviderUnavailableError:
        raise DataUnavailableError("Market data providers are temporarily unavailable.")

    raise SymbolNotFoundError(f"No quote data found for symbol={symbol}")


def get_history(symbol: str, days: int) -> dict:
    finmind_failed = False
    twse_failed = False
    twse_no_data = False

    try:
        cached = _load_history_from_postgres(symbol, days=days)
        if cached:
            return _with_history_freshness(cached, max_age_days=7)
    except Exception:
        pass

    try:
        finmind_history = _fetch_history_from_finmind(symbol, days=days)
        if finmind_history:
            _persist_series_to_postgres(
                symbol=symbol,
                series=finmind_history["series"],
                source="finmind",
            )
            return _with_history_freshness(finmind_history, max_age_days=7)
    except Exception:
        finmind_failed = True

    try:
        twse_history = _fetch_history_from_twse(symbol, days=days)
        if twse_history is None:
            twse_no_data = True
        else:
            _persist_series_to_postgres(
                symbol=symbol,
                series=twse_history["series"],
                source="twse",
            )
            return _with_history_freshness(twse_history, max_age_days=7)
    except Exception:
        twse_failed = True

    if finmind_failed and twse_failed:
        raise DataUnavailableError("Market data providers are temporarily unavailable.")

    if twse_no_data:
        raise SymbolNotFoundError(f"No history data found for symbol={symbol}")

    raise SymbolNotFoundError(f"No history data found for symbol={symbol}")


def _with_history_freshness(payload: dict, max_age_days: int) -> dict:
    out = dict(payload)
    series = out.get("series") or []
    latest_date = ""
    if series:
        latest_date = str(series[-1].get("date", ""))
    out["as_of_date"] = latest_date
    out["freshness"] = _build_freshness(latest_date, max_age_days=max_age_days)
    return out


def get_indicators(symbol: str, days: int) -> dict:
    history = get_history(symbol, days=days)
    indicator_series = compute_indicator_series(history.get("series", []))
    latest = compute_latest_indicators(history.get("series", []))

    latest_date = ""
    if indicator_series:
        latest_date = str(indicator_series[-1].get("date", ""))

    return {
        "symbol": symbol,
        "days": int(history.get("days", days)),
        "as_of_date": latest_date,
        "freshness": history.get("freshness") or _build_freshness(latest_date, max_age_days=7),
        "history_source": history.get("source", "unknown"),
        "indicator_engine": get_indicator_engine(),
        "is_fallback": bool(history.get("is_fallback", False)),
        "note": str(history.get("note", "")),
        "latest": latest,
        "series": indicator_series,
    }
