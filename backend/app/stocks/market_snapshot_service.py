from __future__ import annotations

from datetime import datetime, timezone

from backend.modules.data_pipeline import upsert_price_snapshots

from ..config import get_settings
from .market_snapshot_provider import fetch_twse_market_snapshots
from .search_service import get_stock_universe_size


class MarketSnapshotSyncError(Exception):
    pass


def run_market_snapshot(max_symbols: int = 3000) -> dict:
    settings = get_settings()
    safe_max_symbols = max(100, min(int(max_symbols), 5000))

    try:
        snapshot_result = fetch_twse_market_snapshots(timeout_seconds=15)
    except Exception as exc:
        raise MarketSnapshotSyncError("市場快照抓取失敗。") from exc

    snapshots = list(snapshot_result.get("snapshots") or [])
    if not snapshots:
        raise MarketSnapshotSyncError("市場快照無資料。")

    ordered = sorted(snapshots, key=lambda item: str(item.get("symbol") or ""))
    selected = ordered[:safe_max_symbols]

    inserted = upsert_price_snapshots(
        database_url=settings.database_url,
        snapshots=selected,
        source="twse_openapi_stock_day_all",
    )
    if inserted <= 0:
        raise MarketSnapshotSyncError("市場快照入庫失敗。")

    trade_date = _resolve_latest_date(selected)
    expected_universe_size = _resolve_universe_size()
    coverage_ratio = None
    if expected_universe_size > 0:
        coverage_ratio = round(len(selected) / expected_universe_size, 4)

    return {
        "ok": True,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "trade_date": trade_date,
        "source": "twse_openapi_stock_day_all",
        "fetched_rows": int(snapshot_result.get("fetched_rows") or len(snapshots)),
        "parsed_rows": int(snapshot_result.get("parsed_rows") or len(snapshots)),
        "valid_rows": int(snapshot_result.get("valid_rows") or len(snapshots)),
        "invalid_rows": int(snapshot_result.get("invalid_rows") or 0),
        "deduped_rows": int(snapshot_result.get("deduped_rows") or 0),
        "selected_rows": len(selected),
        "inserted_rows": int(inserted),
        "expected_universe_size": expected_universe_size,
        "coverage_ratio": coverage_ratio,
        "max_symbols": safe_max_symbols,
        "note": "已完成市場日資料批次同步。",
    }


def _resolve_universe_size() -> int:
    try:
        return max(int(get_stock_universe_size()), 0)
    except Exception:
        return 0


def _resolve_latest_date(snapshots: list[dict]) -> str:
    dates = sorted({str(item.get("date") or "").strip() for item in snapshots if item.get("date")})
    if not dates:
        return ""
    return dates[-1]
