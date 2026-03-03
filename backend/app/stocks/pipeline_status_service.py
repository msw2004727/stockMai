from __future__ import annotations

from datetime import date

from ..config import get_settings
from .market_clock import current_taipei_now, parse_holiday_dates, previous_trading_day
from .pipeline_status_repository import load_pipeline_status_snapshot
from .search_service import get_stock_universe_size

COVERAGE_WARN_THRESHOLD = 0.80


class PipelineStatusUnavailableError(Exception):
    pass


def get_pipeline_status() -> dict:
    settings = get_settings()
    expected_trade_date = _resolve_expected_trade_date(settings.twse_holidays)

    try:
        snapshot = load_pipeline_status_snapshot(settings.database_url)
    except Exception as exc:
        raise PipelineStatusUnavailableError("同步狀態暫時無法取得。") from exc

    latest_trade_date = _parse_iso_date(snapshot.get("latest_trade_date"))
    symbol_count = int(snapshot.get("symbol_count") or 0)
    row_count = int(snapshot.get("row_count") or 0)
    expected_universe_size = _resolve_universe_size()

    coverage_ratio = None
    if expected_universe_size > 0:
        coverage_ratio = round(symbol_count / expected_universe_size, 4)

    lag_days = None
    if latest_trade_date is not None:
        lag_days = int((expected_trade_date - latest_trade_date).days)

    date_ok = latest_trade_date is not None and latest_trade_date >= expected_trade_date
    coverage_ok = coverage_ratio is None or coverage_ratio >= COVERAGE_WARN_THRESHOLD
    is_healthy = bool(date_ok and coverage_ok and row_count > 0)

    notes = _build_notes(
        latest_trade_date=latest_trade_date,
        expected_trade_date=expected_trade_date,
        lag_days=lag_days,
        coverage_ratio=coverage_ratio,
        expected_universe_size=expected_universe_size,
        symbol_count=symbol_count,
    )

    return {
        "status": "ok" if is_healthy else "warn",
        "is_healthy": is_healthy,
        "expected_trade_date": expected_trade_date.isoformat(),
        "latest_trade_date": latest_trade_date.isoformat() if latest_trade_date else "",
        "lag_days": lag_days,
        "row_count": row_count,
        "symbol_count": symbol_count,
        "expected_universe_size": expected_universe_size,
        "coverage_ratio": coverage_ratio,
        "coverage_warn_threshold": COVERAGE_WARN_THRESHOLD,
        "source_breakdown": list(snapshot.get("source_breakdown") or []),
        "note": " ".join(notes),
    }


def _resolve_expected_trade_date(twse_holidays_raw: str) -> date:
    holiday_dates = parse_holiday_dates(twse_holidays_raw)
    today = current_taipei_now().date()
    return previous_trading_day(today, holiday_dates)


def _resolve_universe_size() -> int:
    try:
        return max(int(get_stock_universe_size()), 0)
    except Exception:
        return 0


def _parse_iso_date(raw: object) -> date | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except Exception:
        return None


def _build_notes(
    *,
    latest_trade_date: date | None,
    expected_trade_date: date,
    lag_days: int | None,
    coverage_ratio: float | None,
    expected_universe_size: int,
    symbol_count: int,
) -> list[str]:
    notes: list[str] = []

    if latest_trade_date is None:
        notes.append("尚未建立市場批次同步資料。")
        return notes

    if lag_days is not None and lag_days > 0:
        notes.append(
            f"最新資料日 {latest_trade_date.isoformat()} 落後目標交易日 {expected_trade_date.isoformat()} 共 {lag_days} 天。"
        )

    if expected_universe_size > 0 and coverage_ratio is not None:
        notes.append(
            f"樣本覆蓋 {symbol_count}/{expected_universe_size}（{coverage_ratio * 100:.1f}%）。"
        )
        if coverage_ratio < COVERAGE_WARN_THRESHOLD:
            notes.append("覆蓋率偏低，建議先執行 pipeline snapshot 再驗收排行。")
    else:
        notes.append("無法估算全市場規模，覆蓋率僅供參考。")

    if not notes:
        notes.append("同步狀態正常。")
    return notes
