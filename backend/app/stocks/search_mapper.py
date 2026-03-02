from __future__ import annotations

import re

_SYMBOL_RE = re.compile(r"(\d{4,6})")
_SPACE_RE = re.compile(r"\s+")

SYMBOL_KEYS = (
    "證券代號",
    "股票代號",
    "公司代號",
    "代號",
    "CODE",
    "code",
    "symbol",
    "stock_id",
)

NAME_KEYS = (
    "證券名稱",
    "股票名稱",
    "公司簡稱",
    "公司名稱",
    "名稱",
    "NAME",
    "name",
    "stock_name",
)

COMBINED_KEYS = (
    "有價證券代號及名稱",
    "證券代號及名稱",
    "股票代號及名稱",
)


def normalize_text(value: str) -> str:
    return _SPACE_RE.sub("", str(value or "")).lower().strip()


def _extract_symbol(value: object) -> str:
    raw = str(value or "").strip()
    match = _SYMBOL_RE.search(raw)
    if not match:
        return ""
    symbol = match.group(1)
    if 4 <= len(symbol) <= 6:
        return symbol
    return ""


def _extract_name_without_symbol(raw: str, symbol: str) -> str:
    cleaned = str(raw or "").strip()
    if not cleaned:
        return ""
    cleaned = re.sub(rf"^\s*{re.escape(symbol)}\s*", "", cleaned).strip()
    if not cleaned or _SYMBOL_RE.fullmatch(cleaned):
        return ""
    return cleaned


def _pick_first_dict_value(row: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def parse_search_row(row: object, market: str, source: str) -> dict | None:
    symbol = ""
    name = ""

    if isinstance(row, dict):
        symbol = _extract_symbol(_pick_first_dict_value(row, SYMBOL_KEYS))

        if not symbol:
            combined_value = _pick_first_dict_value(row, COMBINED_KEYS)
            symbol = _extract_symbol(combined_value)

        if not symbol:
            for value in row.values():
                symbol = _extract_symbol(value)
                if symbol:
                    break

        if not symbol:
            return None

        name = _pick_first_dict_value(row, NAME_KEYS)
        if not name:
            combined_value = _pick_first_dict_value(row, COMBINED_KEYS)
            name = _extract_name_without_symbol(combined_value, symbol)

        if not name:
            for value in row.values():
                if isinstance(value, str) and symbol in value:
                    possible_name = _extract_name_without_symbol(value, symbol)
                    if possible_name:
                        name = possible_name
                        break

    elif isinstance(row, list):
        tokens = [str(value).strip() for value in row if str(value).strip()]
        for index, token in enumerate(tokens):
            symbol = _extract_symbol(token)
            if not symbol:
                continue
            name = _extract_name_without_symbol(token, symbol)
            if not name and index + 1 < len(tokens):
                name = _extract_name_without_symbol(tokens[index + 1], symbol) or tokens[index + 1]
            break

        if not symbol:
            return None

    else:
        return None

    normalized_name = str(name or "").strip() or symbol
    return {
        "symbol": symbol,
        "name": normalized_name,
        "market": str(market or "unknown"),
        "source": str(source or "unknown"),
    }

