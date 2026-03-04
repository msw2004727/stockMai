from __future__ import annotations

from datetime import date, timedelta
import re
from urllib.parse import urlencode

from .http_client import fetch_json

TWSE_RWD_BASE_URL = "https://www.twse.com.tw/rwd/zh"
TDCC_SHAREHOLDING_URL = "https://opendata.tdcc.com.tw/getOD.ashx?id=1-5"
UNSUPPORTED_MESSAGE = "Official free dataset adapter is not available yet."

_DIGIT_RE = re.compile(r"(\d{4,6})")


def find_twse_row_by_symbol(
    *,
    path: str,
    symbol: str,
    lookback_days: int,
    query: dict[str, str],
) -> tuple[list[object] | None, date | None, bool, bool]:
    had_error = False
    had_payload = False

    for trade_date in recent_business_days(lookback_days):
        try:
            rows = fetch_twse_table(path=path, trade_date=trade_date, query=query)
        except Exception:
            had_error = True
            continue

        if not rows:
            continue

        had_payload = True
        for row in rows:
            if not isinstance(row, list):
                continue
            if extract_symbol(safe_cell(row, 0)) == symbol:
                return row, trade_date, had_error, had_payload

    return None, None, had_error, had_payload


def fetch_twse_table(*, path: str, trade_date: date, query: dict[str, str]) -> list[list[object]]:
    merged_query = {
        "response": "json",
        "date": trade_date.strftime("%Y%m%d"),
    }
    merged_query.update(query)
    url = f"{TWSE_RWD_BASE_URL}/{path}?{urlencode(merged_query)}"
    payload = fetch_json(url, timeout=10, allow_insecure_tls_fallback=True)

    if not isinstance(payload, dict):
        return []
    rows = payload.get("data")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, list)]


def recent_business_days(limit: int) -> list[date]:
    days: list[date] = []
    current = date.today()
    offset = 0
    while len(days) < max(int(limit), 1):
        candidate = current - timedelta(days=offset)
        offset += 1
        if candidate.weekday() >= 5:
            continue
        days.append(candidate)
    return days


def safe_cell(row: list[object], index: int) -> object:
    if index < 0:
        return ""
    if index >= len(row):
        return ""
    return row[index]


def extract_rows(payload: object) -> list[object]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []

    for key in ("data", "aaData", "results", "rows", "list"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return rows

    for value in payload.values():
        if isinstance(value, list):
            return value
    return []


def extract_symbol(raw: object) -> str:
    match = _DIGIT_RE.search(str(raw or ""))
    if not match:
        return ""
    return match.group(1)


def to_float(raw: object) -> float | None:
    text = str(raw or "").strip().replace(",", "")
    if text in {"", "-", "--"}:
        return None
    text = text.replace("+", "").replace("X", "")
    try:
        return float(text)
    except Exception:
        return None


def diff(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(float(left) - float(right), 4)


def sum_numbers(left: float | None, right: float | None) -> float | None:
    if left is None and right is None:
        return None
    return round(float(left or 0.0) + float(right or 0.0), 4)


def prefer_number(primary: float | None, secondary: float | None) -> float | None:
    if primary is not None:
        return round(float(primary), 4)
    if secondary is not None:
        return round(float(secondary), 4)
    return None


def ok_block(*, key: str, dataset: str, source: str, data_as_of: str, rows: list[dict]) -> dict:
    return build_block(
        key=key,
        status="ok",
        dataset=dataset,
        source=source,
        message="",
        status_code=200,
        data_as_of=data_as_of,
        rows=rows,
    )


def empty_block(*, key: str, dataset: str, source: str, message: str) -> dict:
    return build_block(
        key=key,
        status="empty",
        dataset=dataset,
        source=source,
        message=message,
        status_code=200,
        data_as_of="",
        rows=[],
    )


def error_block(*, key: str, dataset: str, source: str, message: str) -> dict:
    return build_block(
        key=key,
        status="error",
        dataset=dataset,
        source=source,
        message=message,
        status_code=503,
        data_as_of="",
        rows=[],
    )


def unsupported_block(*, key: str, dataset: str, source: str, message: str) -> dict:
    return build_block(
        key=key,
        status="error",
        dataset=dataset,
        source=source,
        message=message,
        status_code=501,
        data_as_of="",
        rows=[],
    )


def build_block(
    *,
    key: str,
    status: str,
    dataset: str,
    source: str,
    message: str,
    status_code: int,
    data_as_of: str,
    rows: list[dict],
    sections: list[dict] | None = None,
) -> dict:
    out = {
        "key": key,
        "status": status,
        "message": message,
        "status_code": int(status_code),
        "dataset": dataset,
        "source": source,
        "data_as_of": data_as_of,
        "rows": rows,
    }
    if sections is not None:
        out["sections"] = sections
    return out
