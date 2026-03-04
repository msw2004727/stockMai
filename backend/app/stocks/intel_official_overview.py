from __future__ import annotations

from datetime import date

from .search_service import get_stock_universe
from .intel_official_support import (
    UNSUPPORTED_MESSAGE,
    diff,
    empty_block,
    error_block,
    find_twse_row_by_symbol,
    ok_block,
    prefer_number,
    safe_cell,
    sum_numbers,
    to_float,
    unsupported_block,
)


def fetch_official_overview_blocks(symbol: str) -> dict[str, dict]:
    return {
        "company_profile": _fetch_company_profile(symbol),
        "valuation": _fetch_valuation(symbol),
        "institutional_flow": _fetch_institutional_flow(symbol),
        "margin_short": _fetch_margin_short(symbol),
        "foreign_holding": _fetch_foreign_holding(symbol),
        "monthly_revenue": unsupported_block(
            key="monthly_revenue",
            dataset="official_monthly_revenue",
            source="official_free_api",
            message=UNSUPPORTED_MESSAGE,
        ),
    }


def _fetch_company_profile(symbol: str) -> dict:
    try:
        universe = get_stock_universe()
    except Exception as exc:
        return error_block(
            key="company_profile",
            dataset="official_stock_universe",
            source="official_free_api",
            message=str(exc),
        )

    target = None
    for item in universe:
        if str(item.get("symbol") or "").strip() == symbol:
            target = item
            break

    if not target:
        return empty_block(
            key="company_profile",
            dataset="official_stock_universe",
            source="official_free_api",
            message=f"symbol={symbol} not found in official stock universe.",
        )

    market = str(target.get("market") or "").strip().lower()
    source = str(target.get("source") or "official_free_api").strip() or "official_free_api"
    row = {
        "stock_id": symbol,
        "stock_name": str(target.get("name") or symbol).strip() or symbol,
        "company_name": str(target.get("name") or symbol).strip() or symbol,
        "industry_category": "",
        "market_category": market.upper() if market else "UNKNOWN",
        "type": market.upper() if market else "UNKNOWN",
    }
    return ok_block(
        key="company_profile",
        dataset="official_stock_universe",
        source=source,
        data_as_of=date.today().isoformat(),
        rows=[row],
    )


def _fetch_valuation(symbol: str) -> dict:
    row, as_of, had_error, had_payload = find_twse_row_by_symbol(
        path="afterTrading/BWIBBU_d",
        symbol=symbol,
        lookback_days=12,
        query={"selectType": "ALL"},
    )
    if row:
        out_row = {
            "date": as_of.isoformat() if as_of else "",
            "PER": to_float(safe_cell(row, 4)),
            "PBR": to_float(safe_cell(row, 5)),
            "dividend_yield": to_float(safe_cell(row, 2)),
        }
        return ok_block(
            key="valuation",
            dataset="TWSE_BWIBBU_d",
            source="twse_rwd",
            data_as_of=out_row["date"],
            rows=[out_row],
        )

    if had_payload:
        return empty_block(
            key="valuation",
            dataset="TWSE_BWIBBU_d",
            source="twse_rwd",
            message=f"symbol={symbol} not found in TWSE valuation table.",
        )
    if had_error:
        return error_block(
            key="valuation",
            dataset="TWSE_BWIBBU_d",
            source="twse_rwd",
            message="TWSE valuation endpoint unavailable.",
        )
    return empty_block(
        key="valuation",
        dataset="TWSE_BWIBBU_d",
        source="twse_rwd",
        message="No official valuation rows returned.",
    )


def _fetch_institutional_flow(symbol: str) -> dict:
    row, as_of, had_error, had_payload = find_twse_row_by_symbol(
        path="fund/T86",
        symbol=symbol,
        lookback_days=12,
        query={"selectType": "ALL"},
    )
    if row:
        as_of_date = as_of.isoformat() if as_of else ""

        foreign_buy = to_float(safe_cell(row, 2))
        foreign_sell = to_float(safe_cell(row, 3))
        foreign_net = prefer_number(to_float(safe_cell(row, 4)), diff(foreign_buy, foreign_sell))

        trust_buy = to_float(safe_cell(row, 8))
        trust_sell = to_float(safe_cell(row, 9))
        trust_net = prefer_number(to_float(safe_cell(row, 10)), diff(trust_buy, trust_sell))

        dealer_buy = sum_numbers(to_float(safe_cell(row, 11)), to_float(safe_cell(row, 14)))
        dealer_sell = sum_numbers(to_float(safe_cell(row, 12)), to_float(safe_cell(row, 15)))
        dealer_net = prefer_number(
            to_float(safe_cell(row, 17)),
            prefer_number(to_float(safe_cell(row, 16)), diff(dealer_buy, dealer_sell)),
        )

        return ok_block(
            key="institutional_flow",
            dataset="TWSE_T86",
            source="twse_rwd",
            data_as_of=as_of_date,
            rows=[
                {"date": as_of_date, "name": "foreign", "buy": foreign_buy, "sell": foreign_sell, "difference": foreign_net},
                {"date": as_of_date, "name": "investment_trust", "buy": trust_buy, "sell": trust_sell, "difference": trust_net},
                {"date": as_of_date, "name": "dealer", "buy": dealer_buy, "sell": dealer_sell, "difference": dealer_net},
            ],
        )

    if had_payload:
        return empty_block(
            key="institutional_flow",
            dataset="TWSE_T86",
            source="twse_rwd",
            message=f"symbol={symbol} not found in TWSE institutional table.",
        )
    if had_error:
        return error_block(
            key="institutional_flow",
            dataset="TWSE_T86",
            source="twse_rwd",
            message="TWSE institutional endpoint unavailable.",
        )
    return empty_block(
        key="institutional_flow",
        dataset="TWSE_T86",
        source="twse_rwd",
        message="No official institutional rows returned.",
    )


def _fetch_margin_short(symbol: str) -> dict:
    row, as_of, had_error, had_payload = find_twse_row_by_symbol(
        path="marginTrading/MI_MARGN",
        symbol=symbol,
        lookback_days=12,
        query={"selectType": "ALL"},
    )
    if row:
        as_of_date = as_of.isoformat() if as_of else ""
        margin_prev = to_float(safe_cell(row, 5))
        margin_balance = to_float(safe_cell(row, 6))
        short_prev = to_float(safe_cell(row, 11))
        short_balance = to_float(safe_cell(row, 12))
        return ok_block(
            key="margin_short",
            dataset="TWSE_MI_MARGN",
            source="twse_rwd",
            data_as_of=as_of_date,
            rows=[
                {
                    "date": as_of_date,
                    "MarginPurchaseBalance": margin_balance,
                    "ShortSaleBalance": short_balance,
                    "MarginPurchaseTodayBalance": diff(margin_balance, margin_prev),
                    "ShortSaleTodayBalance": diff(short_balance, short_prev),
                }
            ],
        )

    if had_payload:
        return empty_block(
            key="margin_short",
            dataset="TWSE_MI_MARGN",
            source="twse_rwd",
            message=f"symbol={symbol} not found in TWSE margin table.",
        )
    if had_error:
        return error_block(
            key="margin_short",
            dataset="TWSE_MI_MARGN",
            source="twse_rwd",
            message="TWSE margin endpoint unavailable.",
        )
    return empty_block(
        key="margin_short",
        dataset="TWSE_MI_MARGN",
        source="twse_rwd",
        message="No official margin rows returned.",
    )


def _fetch_foreign_holding(symbol: str) -> dict:
    row, as_of, had_error, had_payload = find_twse_row_by_symbol(
        path="fund/TWT38U",
        symbol=symbol,
        lookback_days=12,
        query={},
    )
    if row:
        as_of_date = as_of.isoformat() if as_of else ""
        return ok_block(
            key="foreign_holding",
            dataset="TWSE_TWT38U",
            source="twse_rwd",
            data_as_of=as_of_date,
            rows=[
                {
                    "date": as_of_date,
                    "Foreign_Investor_Shares_Holding": to_float(safe_cell(row, 3)),
                    "Foreign_Investor_Shares_Holding_Ratio": to_float(safe_cell(row, 4)),
                }
            ],
        )

    if had_payload:
        return empty_block(
            key="foreign_holding",
            dataset="TWSE_TWT38U",
            source="twse_rwd",
            message=f"symbol={symbol} not found in TWSE foreign-holding table.",
        )
    if had_error:
        return error_block(
            key="foreign_holding",
            dataset="TWSE_TWT38U",
            source="twse_rwd",
            message="TWSE foreign-holding endpoint unavailable.",
        )
    return empty_block(
        key="foreign_holding",
        dataset="TWSE_TWT38U",
        source="twse_rwd",
        message="No official foreign-holding rows returned.",
    )
