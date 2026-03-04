from __future__ import annotations

from .intel_mapper import build_status_view, map_deep_block, map_overview_block, now_iso
from .intel_provider import build_finmind_client, fetch_deep_blocks, fetch_overview_blocks
from .service import get_quote
from ..config import get_settings


class StockIntelUnavailableError(Exception):
    pass


OVERVIEW_BLOCK_KEYS = (
    "company_profile",
    "valuation",
    "institutional_flow",
    "margin_short",
    "foreign_holding",
    "monthly_revenue",
)

DEEP_BLOCK_KEYS = (
    "price_performance",
    "shareholding_distribution",
    "securities_lending",
    "broker_branches",
    "financial_statements",
)


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
    block_views = {key: _mapped_or_default(mapped_blocks, key, fetched_at=fetched_at) for key in OVERVIEW_BLOCK_KEYS}
    return {
        "symbol": symbol,
        "source": "finmind",
        "fetched_at": fetched_at,
        "quote_summary": quote_summary,
        "company_profile": block_views["company_profile"],
        "valuation": block_views["valuation"],
        "institutional_flow": block_views["institutional_flow"],
        "margin_short": block_views["margin_short"],
        "foreign_holding": block_views["foreign_holding"],
        "monthly_revenue": block_views["monthly_revenue"],
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
    block_views = {key: _mapped_or_default(mapped_blocks, key, fetched_at=fetched_at) for key in DEEP_BLOCK_KEYS}

    return {
        "symbol": symbol,
        "source": "finmind",
        "fetched_at": fetched_at,
        "price_performance": block_views["price_performance"],
        "shareholding_distribution": block_views["shareholding_distribution"],
        "securities_lending": block_views["securities_lending"],
        "broker_branches": block_views["broker_branches"],
        "financial_statements": block_views["financial_statements"],
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


def _mapped_or_default(mapped_blocks: dict[str, dict], key: str, *, fetched_at: str) -> dict:
    block = mapped_blocks.get(key)
    if isinstance(block, dict):
        return block
    fallback = {
        "source": "finmind",
        "dataset": "",
        "availability": {"status": "empty", "message": "Dataset missing in response."},
        "status_code": 200,
        "fetched_at": fetched_at,
        "data_as_of": "",
        "is_delayed": True,
        "summary": {},
        "rows": [],
    }
    if key == "financial_statements":
        fallback["sections"] = []
    return fallback
