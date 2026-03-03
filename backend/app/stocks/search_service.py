from __future__ import annotations

import re
import time
from threading import Lock

from .search_constants import FALLBACK_STOCK_UNIVERSE, OPEN_DATA_SOURCES, SEARCH_CACHE_TTL_SECONDS
from .search_mapper import normalize_text
from .search_provider import fetch_stock_universe_from_sources

_DIGITS_ONLY_RE = re.compile(r"^\d+$")
_CACHE_LOCK = Lock()
_CACHE_LOADED_AT = 0.0
_CACHE_UNIVERSE = list(FALLBACK_STOCK_UNIVERSE)


def _merge_with_fallback(fetched: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}

    for item in fetched:
        symbol = str(item.get("symbol") or "").strip()
        if not symbol:
            continue
        merged[symbol] = {
            "symbol": symbol,
            "name": str(item.get("name") or symbol).strip() or symbol,
            "market": str(item.get("market") or "unknown"),
            "source": str(item.get("source") or "unknown"),
        }

    for fallback in FALLBACK_STOCK_UNIVERSE:
        symbol = fallback["symbol"]
        if symbol in merged:
            continue
        merged[symbol] = dict(fallback)

    return list(merged.values())


def _load_universe() -> list[dict]:
    global _CACHE_LOADED_AT
    global _CACHE_UNIVERSE

    now = time.time()
    with _CACHE_LOCK:
        if _CACHE_UNIVERSE and now - _CACHE_LOADED_AT < SEARCH_CACHE_TTL_SECONDS:
            return list(_CACHE_UNIVERSE)

    fetched = fetch_stock_universe_from_sources(OPEN_DATA_SOURCES, timeout_seconds=8)
    merged = _merge_with_fallback(fetched)

    with _CACHE_LOCK:
        _CACHE_UNIVERSE = merged
        _CACHE_LOADED_AT = now
        return list(_CACHE_UNIVERSE)


def _score_match(query: str, item: dict) -> int | None:
    symbol = str(item.get("symbol") or "")
    name = str(item.get("name") or "")
    if not symbol:
        return None

    normalized_query = normalize_text(query)
    if not normalized_query:
        return None

    normalized_name = normalize_text(name)

    if _DIGITS_ONLY_RE.fullmatch(normalized_query):
        if symbol == normalized_query:
            return 0
        if symbol.startswith(normalized_query):
            return 1
        if normalized_query in symbol:
            return 2
        return None

    if normalized_name == normalized_query:
        return 0
    if normalized_name.startswith(normalized_query):
        return 1
    if normalized_query in normalized_name:
        return 2
    if normalized_query in symbol:
        return 3
    return None


def search_stock_symbols(query: str, *, limit: int = 8) -> list[dict]:
    trimmed_query = str(query or "").strip()
    if not trimmed_query:
        return []

    capped_limit = max(1, min(int(limit), 20))
    universe = _load_universe()

    scored: list[tuple[int, str, dict]] = []
    for item in universe:
        score = _score_match(trimmed_query, item)
        if score is None:
            continue
        scored.append((score, str(item.get("symbol") or ""), item))

    scored.sort(key=lambda row: (row[0], row[1]))
    return [
        {
            "symbol": item["symbol"],
            "name": item["name"],
            "market": item.get("market", "unknown"),
        }
        for _, _, item in scored[:capped_limit]
    ]


def get_stock_universe_size() -> int:
    return len(_load_universe())
