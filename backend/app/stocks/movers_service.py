from __future__ import annotations

from datetime import date

from ..config import get_settings
from .market_clock import current_taipei_now, parse_holiday_dates, previous_trading_day
from .movers_repository import load_previous_day_movers
from .search_service import get_stock_universe_size


class MarketMoversUnavailableError(Exception):
    pass


def get_market_movers(limit: int = 6) -> dict:
    safe_limit = max(1, min(int(limit), 20))
    settings = get_settings()
    target_trade_date = _resolve_target_trade_date(settings.twse_holidays)

    try:
        payload = load_previous_day_movers(
            database_url=settings.database_url,
            limit=safe_limit,
            target_trade_date=target_trade_date,
        )
    except Exception as exc:
        raise MarketMoversUnavailableError("市場排行資料暫時無法取得。") from exc

    if not isinstance(payload, dict):
        raise MarketMoversUnavailableError("市場排行資料格式錯誤。")

    expected_universe_size = _resolve_universe_size()
    payload = _enrich_coverage(payload, expected_universe_size=expected_universe_size)
    payload = _enrich_trade_date_fallback_note(payload, requested_trade_date=target_trade_date)
    return payload


def _resolve_target_trade_date(twse_holidays_raw: str) -> date:
    holiday_dates = parse_holiday_dates(twse_holidays_raw)
    today = current_taipei_now().date()
    return previous_trading_day(today, holiday_dates)


def _resolve_universe_size() -> int:
    try:
        return max(int(get_stock_universe_size()), 0)
    except Exception:
        return 0


def _enrich_coverage(payload: dict, expected_universe_size: int) -> dict:
    out = dict(payload)
    actual_universe_size = int(out.get("universe_size") or 0)

    coverage_ratio = None
    if expected_universe_size > 0:
        coverage_ratio = round(actual_universe_size / expected_universe_size, 4)

    out["expected_universe_size"] = expected_universe_size
    out["coverage_ratio"] = coverage_ratio
    out["is_partial_universe"] = (
        expected_universe_size > 0 and actual_universe_size < expected_universe_size
    )

    note_parts = [str(out.get("note") or "").strip()]
    if expected_universe_size <= 0:
        note_parts.append("無法估算全市場規模，覆蓋率僅供參考。")
    elif out["is_partial_universe"]:
        note_parts.append("目前僅使用已入庫樣本計算排行，結果可能與交易所全市場排行有差異。")

    out["note"] = _join_note(note_parts)
    return out


def _enrich_trade_date_fallback_note(payload: dict, requested_trade_date: date) -> dict:
    out = dict(payload)
    requested = requested_trade_date.isoformat()
    as_of_date = str(out.get("as_of_date") or "").strip()
    out["requested_trade_date"] = requested

    note_parts = [str(out.get("note") or "").strip()]
    if as_of_date and as_of_date != requested:
        note_parts.append(f"指定交易日 {requested} 無完整資料，已回退到最近可用交易日 {as_of_date}。")
    out["note"] = _join_note(note_parts)
    return out


def _join_note(parts: list[str]) -> str:
    unique_parts: list[str] = []
    for item in parts:
        text = str(item or "").strip()
        if not text:
            continue
        if text not in unique_parts:
            unique_parts.append(text)
    return " ".join(unique_parts)
