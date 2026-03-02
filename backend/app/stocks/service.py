from __future__ import annotations

from datetime import date
import math
import time

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
from .quote_runtime import (
    QuoteRateLimitExceeded,
    enforce_quote_rate_guard,
    load_short_quote_cache,
    save_short_quote_cache,
)
from .market_clock import infer_market_state, parse_holiday_dates


class SymbolNotFoundError(Exception):
    pass


class DataUnavailableError(Exception):
    pass


class QuoteRateLimitedError(Exception):
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

    month_count = _resolve_twse_month_count(days)
    for month in month_candidates(date.today(), count=month_count):
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


def _resolve_twse_month_count(days: int) -> int:
    safe_days = max(int(days), 1)
    # TWSE daily history is month-scoped; add a small buffer for holidays.
    estimated = math.ceil(safe_days / 20) + 2
    return max(6, min(estimated, 18))


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


def _with_quote_runtime_meta(payload: dict, default_priority: str, twse_holidays_raw: str) -> dict:
    out = dict(payload)
    as_of_date = str(out.get("as_of_date", ""))
    out["quote_time"] = out.get("quote_time") or (f"{as_of_date} 14:00:00" if as_of_date else "")
    out["is_realtime"] = bool(out.get("is_realtime", False))
    out["market_state"] = infer_market_state(
        market_state=str(out.get("market_state") or "unknown"),
        as_of_date=as_of_date,
        quote_time=str(out.get("quote_time") or ""),
        is_realtime=bool(out.get("is_realtime", False)),
        holiday_dates=parse_holiday_dates(twse_holidays_raw),
    )
    out["delay_seconds"] = out.get("delay_seconds")
    out["source_priority"] = str(out.get("source_priority") or default_priority)
    out["provider_used"] = str(out.get("provider_used") or out.get("source") or "unknown")
    out["fetch_latency_ms"] = out.get("fetch_latency_ms")
    out["cache_hit"] = bool(out.get("cache_hit", False))
    return out


def get_quote(symbol: str) -> dict:
    settings = get_settings()
    short_cache = load_short_quote_cache(settings.redis_url, symbol=symbol)
    if short_cache:
        with_meta = _with_quote_runtime_meta(
            short_cache,
            default_priority="short_cache",
            twse_holidays_raw=settings.twse_holidays,
        )
        with_meta["cache_hit"] = True
        return _with_freshness(with_meta, max_age_days=5)

    try:
        cached = _load_quote_from_postgres(symbol)
        if cached:
            with_meta = _with_quote_runtime_meta(
                cached,
                default_priority="cache",
                twse_holidays_raw=settings.twse_holidays,
            )
            with_meta["provider_used"] = "postgres"
            with_meta["cache_hit"] = False
            return _with_freshness(with_meta, max_age_days=5)
    except Exception:
        pass

    try:
        try:
            enforce_quote_rate_guard(
                redis_url=settings.redis_url,
                symbol=symbol,
                max_requests=settings.quote_fetch_rate_limit,
                window_seconds=settings.quote_fetch_rate_window_seconds,
            )
        except QuoteRateLimitExceeded as exc:
            raise QuoteRateLimitedError(str(exc)) from exc

        started = time.perf_counter()
        quote = _fetch_quote_from_provider_chain(symbol)
        fetch_latency_ms = int((time.perf_counter() - started) * 1000)
        if quote:
            with_meta = _with_quote_runtime_meta(
                quote,
                default_priority="daily_fallback",
                twse_holidays_raw=settings.twse_holidays,
            )
            with_meta["provider_used"] = with_meta.get("source", "unknown")
            with_meta["fetch_latency_ms"] = fetch_latency_ms
            with_meta["cache_hit"] = False
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
            save_short_quote_cache(
                redis_url=settings.redis_url,
                symbol=symbol,
                payload=with_meta,
                ttl_seconds=settings.quote_short_cache_ttl_seconds,
            )
            return _with_freshness(with_meta, max_age_days=5)
    except QuoteProviderUnavailableError:
        raise DataUnavailableError("Market data providers are temporarily unavailable.")

    raise SymbolNotFoundError(f"No quote data found for symbol={symbol}")


def get_history(symbol: str, days: int) -> dict:
    settings = get_settings()
    finmind_failed = False
    finmind_skipped = False
    twse_failed = False
    twse_no_data = False

    try:
        cached = _load_history_from_postgres(symbol, days=days)
        if cached:
            return _with_history_freshness(cached, max_age_days=7)
    except Exception:
        pass

    if settings.finmind_token:
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
    else:
        finmind_skipped = True

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

    if twse_failed and (finmind_failed or finmind_skipped):
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
