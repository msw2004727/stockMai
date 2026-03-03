from __future__ import annotations

import re

from .resolve_constants import (
    COMMON_TYPO_ALIASES,
    DEFAULT_LIMIT,
    HIGH_CONFIDENCE_MIN,
    LOW_CONFIDENCE_MIN,
    MAX_LIMIT,
    MIN_MARGIN,
)
from .search_mapper import normalize_text
from .search_service import get_stock_universe

_DIGITS_ONLY_RE = re.compile(r"^\d{4,6}$")


def _levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    prev = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        curr = [i]
        for j, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _max_typo_distance(query: str) -> int:
    length = len(query)
    if length <= 2:
        return 0
    if length <= 4:
        return 1
    return 2


def _build_match(
    *,
    score: int,
    reason: str,
    symbol: str,
    name: str,
    market: str,
) -> dict:
    return {
        "symbol": symbol,
        "name": name,
        "market": market,
        "score": int(score),
        "reason": reason,
        "confidence": _confidence_label(score),
    }


def _confidence_label(score: int) -> str:
    if score >= HIGH_CONFIDENCE_MIN:
        return "high"
    if score >= LOW_CONFIDENCE_MIN:
        return "medium"
    return "low"


def _score_candidate(
    *,
    normalized_query: str,
    raw_query: str,
    alias_target: str,
    item: dict,
) -> dict | None:
    symbol = str(item.get("symbol") or "").strip()
    if not symbol:
        return None
    name = str(item.get("name") or symbol).strip() or symbol
    market = str(item.get("market") or "unknown")
    normalized_name = normalize_text(name)

    is_digits_query = bool(_DIGITS_ONLY_RE.fullmatch(normalized_query))

    if is_digits_query:
        if symbol == normalized_query:
            return _build_match(score=100, reason="exact_symbol", symbol=symbol, name=name, market=market)
        if symbol.startswith(normalized_query):
            return _build_match(score=88, reason="prefix_symbol", symbol=symbol, name=name, market=market)
        if normalized_query in symbol:
            return _build_match(score=70, reason="contains_symbol", symbol=symbol, name=name, market=market)
        return None

    best: dict | None = None

    if normalized_name == normalized_query:
        best = _build_match(score=100, reason="exact_name", symbol=symbol, name=name, market=market)
    elif normalized_name.startswith(normalized_query):
        best = _build_match(score=90, reason="prefix_name", symbol=symbol, name=name, market=market)
    elif normalized_query in normalized_name:
        best = _build_match(score=78, reason="contains_name", symbol=symbol, name=name, market=market)
    elif normalized_query in symbol:
        best = _build_match(score=72, reason="contains_symbol", symbol=symbol, name=name, market=market)

    if alias_target and normalized_name == alias_target:
        alias_match = _build_match(score=95, reason="alias_match", symbol=symbol, name=name, market=market)
        if best is None or alias_match["score"] > best["score"]:
            best = alias_match

    if normalized_name:
        distance = _levenshtein_distance(normalized_query, normalized_name)
        if distance <= _max_typo_distance(normalized_query):
            max_len = max(len(normalized_query), len(normalized_name))
            similarity = 1 - (distance / max_len if max_len else 0)
            typo_score = max(0, min(100, int(round(84 - 12 * distance + similarity * 6))))
            typo_match = _build_match(
                score=typo_score,
                reason=f"typo_distance_d{distance}",
                symbol=symbol,
                name=name,
                market=market,
            )
            if best is None or typo_match["score"] > best["score"]:
                best = typo_match

    # Slightly relax matching for queries that differ only in punctuation or spacing.
    if best is None and raw_query and normalize_text(raw_query) == normalized_name:
        best = _build_match(score=92, reason="normalized_name", symbol=symbol, name=name, market=market)

    return best


def _classify_resolution(candidates: list[dict]) -> tuple[str, dict | None]:
    if not candidates:
        return "not_found", None

    best = candidates[0]
    second_score = candidates[1]["score"] if len(candidates) > 1 else 0
    margin = int(best["score"]) - int(second_score)

    if int(best["score"]) >= HIGH_CONFIDENCE_MIN and margin >= MIN_MARGIN:
        return "resolved", best
    if int(best["score"]) >= LOW_CONFIDENCE_MIN:
        return "ambiguous", best
    return "low_confidence", best


def resolve_stock_query(query: str, *, limit: int = DEFAULT_LIMIT) -> dict:
    raw_query = str(query or "").strip()
    normalized_query = normalize_text(raw_query)
    capped_limit = max(1, min(int(limit), MAX_LIMIT))

    if not normalized_query:
        return {
            "query": raw_query,
            "normalized_query": normalized_query,
            "resolution": {
                "status": "not_found",
                "best": None,
                "candidates": [],
                "thresholds": {
                    "high_confidence_min": HIGH_CONFIDENCE_MIN,
                    "min_margin": MIN_MARGIN,
                },
            },
        }

    normalized_aliases = {normalize_text(key): normalize_text(value) for key, value in COMMON_TYPO_ALIASES.items()}
    alias_target = normalized_aliases.get(normalized_query, "")

    scored: list[dict] = []
    for item in get_stock_universe():
        matched = _score_candidate(
            normalized_query=normalized_query,
            raw_query=raw_query,
            alias_target=alias_target,
            item=item,
        )
        if not matched:
            continue
        scored.append(matched)

    scored.sort(key=lambda row: (-int(row["score"]), str(row["symbol"])))
    deduped: list[dict] = []
    seen_symbols: set[str] = set()
    for row in scored:
        symbol = str(row["symbol"])
        if symbol in seen_symbols:
            continue
        deduped.append(row)
        seen_symbols.add(symbol)
        if len(deduped) >= capped_limit:
            break

    status, best = _classify_resolution(deduped)

    return {
        "query": raw_query,
        "normalized_query": normalized_query,
        "resolution": {
            "status": status,
            "best": best,
            "candidates": deduped,
            "thresholds": {
                "high_confidence_min": HIGH_CONFIDENCE_MIN,
                "min_margin": MIN_MARGIN,
            },
        },
    }
