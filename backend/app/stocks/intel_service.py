from __future__ import annotations

from .intel_mapper import build_status_view, map_deep_block, map_overview_block, now_iso
from .intel_provider import build_finmind_client, fetch_deep_blocks, fetch_overview_blocks
from .service import get_quote
from ..config import get_settings


class StockIntelUnavailableError(Exception):
    pass


def get_stock_intel_overview(symbol: str) -> dict:
    settings = get_settings()
    token = str(settings.finmind_token or "").strip()
    if not token:
        raise StockIntelUnavailableError("FINMIND_TOKEN is not configured.")

    fetched_at = now_iso()
    client = build_finmind_client(token)
    raw_blocks = fetch_overview_blocks(client=client, symbol=symbol)
    mapped_blocks = {key: map_overview_block(key, block, fetched_at=fetched_at) for key, block in raw_blocks.items()}

    quote_summary = _safe_quote(symbol)
    return {
        "symbol": symbol,
        "source": "finmind",
        "fetched_at": fetched_at,
        "quote_summary": quote_summary,
        "institutional_flow": mapped_blocks["institutional_flow"],
        "margin_short": mapped_blocks["margin_short"],
        "foreign_holding": mapped_blocks["foreign_holding"],
        "monthly_revenue": mapped_blocks["monthly_revenue"],
        "datasets": build_status_view(raw_blocks, fetched_at=fetched_at),
    }


def get_stock_intel_deep(symbol: str) -> dict:
    settings = get_settings()
    token = str(settings.finmind_token or "").strip()
    if not token:
        raise StockIntelUnavailableError("FINMIND_TOKEN is not configured.")

    fetched_at = now_iso()
    client = build_finmind_client(token)
    raw_blocks = fetch_deep_blocks(client=client, symbol=symbol)
    mapped_blocks = {key: map_deep_block(key, block, fetched_at=fetched_at) for key, block in raw_blocks.items()}

    return {
        "symbol": symbol,
        "source": "finmind",
        "fetched_at": fetched_at,
        "shareholding_distribution": mapped_blocks["shareholding_distribution"],
        "securities_lending": mapped_blocks["securities_lending"],
        "broker_branches": mapped_blocks["broker_branches"],
        "financial_statements": mapped_blocks["financial_statements"],
        "datasets": build_status_view(raw_blocks, fetched_at=fetched_at),
    }


def get_stock_intel_status(symbol: str) -> dict:
    settings = get_settings()
    token = str(settings.finmind_token or "").strip()
    if not token:
        raise StockIntelUnavailableError("FINMIND_TOKEN is not configured.")

    fetched_at = now_iso()
    client = build_finmind_client(token)
    overview_blocks = fetch_overview_blocks(client=client, symbol=symbol)
    deep_blocks = fetch_deep_blocks(client=client, symbol=symbol)
    all_blocks = {**overview_blocks, **deep_blocks}

    return {
        "symbol": symbol,
        "source": "finmind",
        "fetched_at": fetched_at,
        "datasets": build_status_view(all_blocks, fetched_at=fetched_at),
    }


def _safe_quote(symbol: str) -> dict:
    try:
        payload = get_quote(symbol)
    except Exception as exc:
        return {
            "availability": {"status": "error", "message": str(exc)},
            "data": None,
        }
    return {
        "availability": {"status": "ok", "message": ""},
        "data": payload,
    }
