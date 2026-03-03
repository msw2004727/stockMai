from __future__ import annotations

from datetime import datetime, timezone

from backend.modules.data_pipeline import upsert_price_snapshots

from ..config import get_settings
from .market_snapshot_provider import fetch_twse_market_snapshots


class MarketSnapshotSyncError(Exception):
    pass


def run_market_snapshot(max_symbols: int = 3000) -> dict:
    settings = get_settings()
    safe_max_symbols = max(100, min(int(max_symbols), 5000))

    try:
        snapshots = fetch_twse_market_snapshots(timeout_seconds=15)
    except Exception as exc:
        raise MarketSnapshotSyncError("市場快照抓取失敗。") from exc

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
    return {
        "ok": True,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "trade_date": trade_date,
        "source": "twse_openapi_stock_day_all",
        "fetched_rows": len(snapshots),
        "selected_rows": len(selected),
        "inserted_rows": int(inserted),
        "max_symbols": safe_max_symbols,
        "note": "已完成市場日資料批次同步。",
    }


def _resolve_latest_date(snapshots: list[dict]) -> str:
    dates = sorted({str(item.get("date") or "").strip() for item in snapshots if item.get("date")})
    if not dates:
        return ""
    return dates[-1]
