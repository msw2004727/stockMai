from __future__ import annotations

from datetime import date

from .http_client import fetch_json
from .parsers import parse_daily_row
from .provider import fetch_twse_month, month_candidates
from .intel_official_support import (
    TDCC_SHAREHOLDING_URL,
    UNSUPPORTED_MESSAGE,
    build_block,
    empty_block,
    error_block,
    extract_rows,
    extract_symbol,
    ok_block,
    to_float,
    unsupported_block,
)


def fetch_official_deep_blocks(symbol: str) -> dict[str, dict]:
    return {
        "price_performance": _fetch_price_performance(symbol),
        "shareholding_distribution": _fetch_shareholding_distribution(symbol),
        "securities_lending": unsupported_block(
            key="securities_lending",
            dataset="official_securities_lending",
            source="official_free_api",
            message=UNSUPPORTED_MESSAGE,
        ),
        "broker_branches": unsupported_block(
            key="broker_branches",
            dataset="official_broker_branches",
            source="official_free_api",
            message=UNSUPPORTED_MESSAGE,
        ),
        "financial_statements": _unsupported_financial_block(),
    }


def _fetch_price_performance(symbol: str) -> dict:
    rows_by_date: dict[str, dict] = {}
    had_error = False

    for month in month_candidates(date.today(), count=14):
        try:
            _name, rows = fetch_twse_month(symbol=symbol, month=month, timeout=8)
        except Exception:
            had_error = True
            continue

        for raw in rows:
            parsed = parse_daily_row(raw)
            if not parsed:
                continue
            rows_by_date[parsed["date"]] = {
                "date": parsed["date"],
                "close": parsed["close"],
                "max": parsed["high"],
                "min": parsed["low"],
            }

    if rows_by_date:
        sorted_rows = [rows_by_date[key] for key in sorted(rows_by_date.keys())]
        return ok_block(
            key="price_performance",
            dataset="TWSE_STOCK_DAY",
            source="twse_exchange_report",
            data_as_of=sorted_rows[-1]["date"],
            rows=sorted_rows,
        )

    if had_error:
        return error_block(
            key="price_performance",
            dataset="TWSE_STOCK_DAY",
            source="twse_exchange_report",
            message="TWSE historical endpoint unavailable.",
        )
    return empty_block(
        key="price_performance",
        dataset="TWSE_STOCK_DAY",
        source="twse_exchange_report",
        message=f"symbol={symbol} not found in TWSE daily report.",
    )


def _fetch_shareholding_distribution(symbol: str) -> dict:
    try:
        payload = fetch_json(
            TDCC_SHAREHOLDING_URL,
            timeout=10,
            allow_insecure_tls_fallback=True,
        )
    except Exception as exc:
        return error_block(
            key="shareholding_distribution",
            dataset="TDCC_OD_1-5",
            source="tdcc_open_data",
            message=str(exc),
        )

    rows = extract_rows(payload)
    matched_rows: list[dict] = []
    best_date = ""
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_symbol = extract_symbol(
            row.get("stock_id") or row.get("symbol") or row.get("code") or row.get("stock_no") or row.get("id")
        )
        if row_symbol != symbol:
            continue

        day = str(row.get("date") or row.get("data_date") or row.get("trade_date") or "").strip()
        if day and day > best_date:
            best_date = day

        matched_rows.append(
            {
                "date": day,
                "HoldingSharesLevel": str(
                    row.get("level")
                    or row.get("holding_level")
                    or row.get("shareholding_level")
                    or row.get("range")
                    or "--"
                ).strip(),
                "people": to_float(row.get("people") or row.get("holders")),
                "percent": to_float(row.get("ratio") or row.get("holding_ratio") or row.get("percent")),
            }
        )

    if matched_rows:
        return ok_block(
            key="shareholding_distribution",
            dataset="TDCC_OD_1-5",
            source="tdcc_open_data",
            data_as_of=best_date,
            rows=matched_rows,
        )

    return empty_block(
        key="shareholding_distribution",
        dataset="TDCC_OD_1-5",
        source="tdcc_open_data",
        message=f"symbol={symbol} not found in TDCC dataset.",
    )


def _unsupported_financial_block() -> dict:
    return build_block(
        key="financial_statements",
        status="error",
        dataset="official_financial_statements",
        source="official_free_api",
        message=UNSUPPORTED_MESSAGE,
        status_code=501,
        data_as_of="",
        rows=[],
        sections=[],
    )
