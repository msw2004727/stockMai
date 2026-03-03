from __future__ import annotations

import re
from datetime import date

_SYMBOL_RE = re.compile(r"^\d{4,6}$")

SYMBOL_KEYS = ("Code", "code", "symbol", "證券代號", "股票代號", "公司代號")
NAME_KEYS = ("Name", "name", "證券名稱", "股票名稱", "公司名稱")
DATE_KEYS = ("Date", "date", "交易日期", "資料日期")
OPEN_KEYS = ("Open", "open", "開盤價")
HIGH_KEYS = ("High", "high", "最高價")
LOW_KEYS = ("Low", "low", "最低價")
CLOSE_KEYS = ("Close", "close", "收盤價")
CHANGE_KEYS = ("Change", "change", "漲跌價差", "漲跌")
VOLUME_KEYS = ("TradeVolume", "trade_volume", "volume", "成交股數", "成交量")


def parse_snapshot_row(row: object, fallback_date: date) -> dict | None:
    if not isinstance(row, dict):
        return None

    symbol = _pick_symbol(row)
    if not symbol:
        return None

    trade_date = _pick_date(row, fallback=fallback_date)
    if not trade_date:
        return None

    open_price = _pick_float(row, OPEN_KEYS)
    high = _pick_float(row, HIGH_KEYS)
    low = _pick_float(row, LOW_KEYS)
    close = _pick_float(row, CLOSE_KEYS)
    change = _pick_float(row, CHANGE_KEYS, default=0.0)
    volume = _pick_int(row, VOLUME_KEYS, default=0)

    if open_price <= 0 or high <= 0 or low <= 0 or close <= 0:
        return None

    return {
        "symbol": symbol,
        "name": _pick_name(row, symbol),
        "date": trade_date,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "change": change,
        "volume": volume,
    }


def _pick_symbol(row: dict) -> str:
    for key in SYMBOL_KEYS:
        value = str(row.get(key) or "").strip()
        if _SYMBOL_RE.fullmatch(value):
            return value
    return ""


def _pick_name(row: dict, fallback_symbol: str) -> str:
    for key in NAME_KEYS:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return fallback_symbol


def _pick_date(row: dict, fallback: date) -> str:
    for key in DATE_KEYS:
        raw = str(row.get(key) or "").strip()
        if not raw:
            continue
        parsed = _parse_date(raw)
        if parsed:
            return parsed
    return fallback.isoformat()


def _parse_date(raw: str) -> str:
    text = raw.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    if re.fullmatch(r"\d{8}", text):
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    if re.fullmatch(r"\d{3}/\d{2}/\d{2}", text):
        year_roc, month, day = text.split("/")
        return f"{int(year_roc) + 1911:04d}-{int(month):02d}-{int(day):02d}"
    return ""


def _pick_float(row: dict, keys: tuple[str, ...], default: float | None = None) -> float:
    for key in keys:
        raw = row.get(key)
        if raw in {None, ""}:
            continue
        parsed = _to_float(raw)
        if parsed is not None:
            return parsed

    if default is None:
        return 0.0
    return float(default)


def _pick_int(row: dict, keys: tuple[str, ...], default: int = 0) -> int:
    for key in keys:
        raw = row.get(key)
        if raw in {None, ""}:
            continue
        parsed = _to_int(raw)
        if parsed is not None:
            return parsed
    return int(default)


def _to_float(value: object) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    text = text.replace("+", "").replace("X", "")
    try:
        return float(text)
    except Exception:
        return None


def _to_int(value: object) -> int | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return int(float(text))
    except Exception:
        return None
