from __future__ import annotations

from datetime import date, datetime, timezone

from .intel_constants import FRESHNESS_POLICY


DEFAULT_FRESHNESS_POLICY = {
    "cadence": "unknown",
    "cadence_label": "未知",
    "expected_interval_days": 7,
    "watch_after_days": 30,
    "stale_after_days": 90,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def map_overview_block(block_key: str, raw_block: dict, fetched_at: str) -> dict:
    mapper = {
        "company_profile": _map_company_profile,
        "valuation": _map_valuation,
        "institutional_flow": _map_institutional_flow,
        "margin_short": _map_margin_short,
        "foreign_holding": _map_foreign_holding,
        "monthly_revenue": _map_monthly_revenue,
    }.get(block_key, _map_passthrough_rows)
    return mapper(raw_block, fetched_at=fetched_at)


def map_deep_block(block_key: str, raw_block: dict, fetched_at: str) -> dict:
    mapper = {
        "price_performance": _map_price_performance,
        "shareholding_distribution": _map_shareholding_distribution,
        "securities_lending": _map_securities_lending,
        "broker_branches": _map_broker_branches,
        "financial_statements": _map_financial_statements,
    }.get(block_key, _map_passthrough_rows)
    return mapper(raw_block, fetched_at=fetched_at)


def build_status_view(blocks: dict[str, dict], fetched_at: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for key, block in blocks.items():
        block_freshness = build_freshness_meta(key, str(block.get("data_as_of") or ""))
        if key == "financial_statements":
            out[key] = {
                "status": str(block.get("status") or "empty"),
                "message": str(block.get("message") or ""),
                "dataset": str(block.get("dataset") or ""),
                "data_as_of": str(block.get("data_as_of") or ""),
                "fetched_at": fetched_at,
                "freshness": block_freshness,
                "sections": [
                    {
                        "kind": str(section.get("kind") or ""),
                        "status": str((section.get("availability") or {}).get("status") or "empty"),
                        "message": str((section.get("availability") or {}).get("message") or ""),
                        "dataset": str(section.get("dataset") or ""),
                        "data_as_of": str(section.get("data_as_of") or ""),
                        "freshness": build_freshness_meta(
                            "financial_statements",
                            str(section.get("data_as_of") or ""),
                        ),
                    }
                    for section in (block.get("sections") or [])
                    if isinstance(section, dict)
                ],
            }
            continue

        out[key] = {
            "status": str(block.get("status") or "empty"),
            "message": str(block.get("message") or ""),
            "dataset": str(block.get("dataset") or ""),
            "data_as_of": str(block.get("data_as_of") or ""),
            "fetched_at": fetched_at,
            "freshness": block_freshness,
        }
    return out


def apply_block_freshness(block: dict, block_key: str) -> dict:
    out = dict(block or {})
    freshness = build_freshness_meta(block_key, str(out.get("data_as_of") or ""))
    out["freshness"] = freshness
    level = str(freshness.get("level") or "unknown")
    out["is_delayed"] = level in {"watch", "stale", "unknown"}

    if block_key == "financial_statements":
        sections = []
        for section in out.get("sections") or []:
            if not isinstance(section, dict):
                continue
            section_out = dict(section)
            section_out["freshness"] = build_freshness_meta(
                "financial_statements",
                str(section_out.get("data_as_of") or ""),
            )
            sections.append(section_out)
        out["sections"] = sections
    return out


def build_freshness_meta(block_key: str, data_as_of: str) -> dict:
    policy = dict(DEFAULT_FRESHNESS_POLICY)
    policy.update(dict(FRESHNESS_POLICY.get(block_key) or {}))

    parsed = _parse_data_as_of(data_as_of)
    if parsed is None:
        return {
            "cadence": str(policy["cadence"]),
            "cadence_label": str(policy["cadence_label"]),
            "staleness_days": None,
            "level": "unknown",
            "message": "資料日期不足，無法判斷新鮮度。",
        }

    staleness_days = max((date.today() - parsed).days, 0)
    expected = int(policy["expected_interval_days"])
    watch_after = int(policy["watch_after_days"])
    stale_after = int(policy["stale_after_days"])

    if staleness_days <= expected:
        level = "fresh"
        message = "資料新鮮。"
    elif staleness_days <= watch_after:
        level = "watch"
        message = f"資料延遲約 {staleness_days} 天，請留意。"
    elif staleness_days <= stale_after:
        level = "stale"
        message = f"資料延遲約 {staleness_days} 天，建議審慎參考。"
    else:
        level = "stale"
        message = f"資料已明顯過舊（{staleness_days} 天）。"

    return {
        "cadence": str(policy["cadence"]),
        "cadence_label": str(policy["cadence_label"]),
        "staleness_days": staleness_days,
        "level": level,
        "message": message,
    }


def _map_company_profile(raw_block: dict, *, fetched_at: str) -> dict:
    rows = list(raw_block.get("rows") or [])
    latest_row = _pick_latest_row(rows)
    summary = {
        "stock_id": _pick_text(latest_row, ("stock_id", "data_id", "stock_no", "symbol")),
        "stock_name": _pick_text(latest_row, ("stock_name", "name", "company_short_name")),
        "company_name": _pick_text(latest_row, ("company_name", "company_full_name")),
        "industry": _pick_text(latest_row, ("industry_category", "industry", "industry_name")),
        "market": _pick_text(latest_row, ("market_category", "market", "market_type")),
        "listing_type": _pick_text(latest_row, ("type", "listing_type", "exchange")),
        "chairman": _pick_text(latest_row, ("chairman", "chairman_name")),
        "address": _pick_text(latest_row, ("address", "company_address")),
        "capital": _round_or_none(_pick_number(latest_row, ("capital", "capital_stock", "paidin_capital"))),
    }
    return _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=_row_date(latest_row) or str(raw_block.get("data_as_of") or "") or fetched_at[:10],
        summary=summary,
        rows=[],
    )


def _map_valuation(raw_block: dict, *, fetched_at: str) -> dict:
    rows = list(raw_block.get("rows") or [])
    normalized = []
    for row in rows:
        day = _row_date(row)
        if not day:
            continue
        normalized.append(
            {
                "date": day,
                "per": _round_or_none(_pick_number(row, ("PER", "per", "price_earning_ratio"))),
                "pbr": _round_or_none(_pick_number(row, ("PBR", "pbr", "price_book_ratio"))),
                "dividend_yield_pct": _round_or_none(
                    _pick_number(row, ("dividend_yield", "DividendYield", "yield", "cash_dividend_yield"))
                ),
            }
        )
    normalized.sort(key=lambda item: item["date"])
    latest = normalized[-1] if normalized else {}
    return _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=str(latest.get("date") or raw_block.get("data_as_of") or ""),
        summary={
            "latest_per": latest.get("per"),
            "latest_pbr": latest.get("pbr"),
            "latest_dividend_yield_pct": latest.get("dividend_yield_pct"),
        },
        rows=normalized[-30:],
    )


def _map_price_performance(raw_block: dict, *, fetched_at: str) -> dict:
    rows = list(raw_block.get("rows") or [])
    normalized = []
    for row in rows:
        day = _row_date(row)
        if not day:
            continue
        close = _pick_number(row, ("close", "Close", "closing_price"))
        high = _pick_number(row, ("max", "high", "High"))
        low = _pick_number(row, ("min", "low", "Low"))
        if close is None:
            continue
        normalized.append(
            {
                "date": day,
                "close": float(close),
                "high": float(high if high is not None else close),
                "low": float(low if low is not None else close),
            }
        )

    normalized.sort(key=lambda item: item["date"])
    latest = normalized[-1] if normalized else {}
    latest_close = latest.get("close")
    close_1m_ago = _close_n_sessions_ago(normalized, 21)
    close_3m_ago = _close_n_sessions_ago(normalized, 63)
    close_1y_ago = _close_n_sessions_ago(normalized, 252)
    one_year_scope = normalized[-252:] if len(normalized) >= 252 else normalized
    high_52w = max((row["high"] for row in one_year_scope), default=None)
    low_52w = min((row["low"] for row in one_year_scope), default=None)

    view_rows = []
    for row in normalized[-90:]:
        view_rows.append(
            {
                "date": row["date"],
                "close": _round_or_none(row["close"]),
            }
        )

    return _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=str(latest.get("date") or raw_block.get("data_as_of") or ""),
        summary={
            "latest_close": _round_or_none(latest_close),
            "return_1m_pct": _calc_return_pct(latest_close, close_1m_ago),
            "return_3m_pct": _calc_return_pct(latest_close, close_3m_ago),
            "return_1y_pct": _calc_return_pct(latest_close, close_1y_ago),
            "high_52w": _round_or_none(high_52w),
            "low_52w": _round_or_none(low_52w),
        },
        rows=view_rows,
    )


def _map_institutional_flow(raw_block: dict, *, fetched_at: str) -> dict:
    rows = list(raw_block.get("rows") or [])
    latest = _latest_date(rows)
    latest_rows = [row for row in rows if _row_date(row) == latest]
    normalized = []
    for row in latest_rows:
        buy = _pick_number(row, ("buy", "buy_shares", "buy_volume", "buy_amount"))
        sell = _pick_number(row, ("sell", "sell_shares", "sell_volume", "sell_amount"))
        net = _pick_number(row, ("difference", "buy_sell", "net_buy_sell", "net"))
        if net is None:
            net = (buy or 0.0) - (sell or 0.0)
        normalized.append(
            {
                "investor": _pick_text(row, ("name", "investor", "institution", "Institutional_Investor")) or "unknown",
                "buy": _round_or_none(buy),
                "sell": _round_or_none(sell),
                "net": _round_or_none(net),
            }
        )
    normalized.sort(key=lambda item: abs(float(item.get("net") or 0.0)), reverse=True)
    summary_net = sum(float(item.get("net") or 0.0) for item in normalized)
    return _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=latest or str(raw_block.get("data_as_of") or ""),
        summary={"net_total": round(summary_net, 2), "count": len(normalized)},
        rows=normalized[:20],
    )


def _map_margin_short(raw_block: dict, *, fetched_at: str) -> dict:
    rows = list(raw_block.get("rows") or [])
    latest_row = _pick_latest_row(rows)
    summary = {
        "margin_purchase_balance": _round_or_none(
            _pick_number(latest_row, ("MarginPurchaseBalance", "margin_purchase_balance", "margin_balance", "融資餘額"))
        ),
        "short_sale_balance": _round_or_none(
            _pick_number(latest_row, ("ShortSaleBalance", "short_sale_balance", "short_balance", "融券餘額"))
        ),
        "margin_purchase_change": _round_or_none(
            _pick_number(latest_row, ("MarginPurchaseTodayBalance", "margin_purchase_change", "融資增減"))
        ),
        "short_sale_change": _round_or_none(
            _pick_number(latest_row, ("ShortSaleTodayBalance", "short_sale_change", "融券增減"))
        ),
    }
    return _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=_row_date(latest_row) or str(raw_block.get("data_as_of") or ""),
        summary=summary,
        rows=[],
    )


def _map_foreign_holding(raw_block: dict, *, fetched_at: str) -> dict:
    rows = list(raw_block.get("rows") or [])
    latest_row = _pick_latest_row(rows)
    summary = {
        "holding_ratio_pct": _round_or_none(
            _pick_number(
                latest_row,
                (
                    "Foreign_Investor_Shares_Holding_Ratio",
                    "holding_ratio",
                    "foreign_holding_ratio",
                    "ratio",
                ),
            )
        ),
        "holding_shares": _round_or_none(
            _pick_number(
                latest_row,
                (
                    "Foreign_Investor_Shares_Holding",
                    "foreign_holding_shares",
                    "holding_shares",
                    "shares",
                ),
            )
        ),
    }
    return _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=_row_date(latest_row) or str(raw_block.get("data_as_of") or ""),
        summary=summary,
        rows=[],
    )


def _map_monthly_revenue(raw_block: dict, *, fetched_at: str) -> dict:
    rows = list(raw_block.get("rows") or [])
    normalized: list[dict] = []
    for row in rows:
        month = _row_date(row)
        revenue = _pick_number(row, ("revenue", "month_revenue", "Revenue", "當月營收"))
        mom = _pick_number(row, ("revenue_month_growth_rate", "mom", "MoM"))
        yoy = _pick_number(row, ("revenue_year_growth_rate", "yoy", "YoY"))
        if not month:
            continue
        normalized.append(
            {
                "month": month,
                "revenue": _round_or_none(revenue),
                "mom_pct": _round_or_none(mom),
                "yoy_pct": _round_or_none(yoy),
            }
        )
    normalized.sort(key=lambda item: item["month"])
    latest = normalized[-1] if normalized else {}
    return _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=str(latest.get("month") or raw_block.get("data_as_of") or ""),
        summary={
            "latest_month": str(latest.get("month") or ""),
            "latest_revenue": latest.get("revenue"),
            "latest_mom_pct": latest.get("mom_pct"),
            "latest_yoy_pct": latest.get("yoy_pct"),
        },
        rows=normalized[-12:],
    )


def _map_shareholding_distribution(raw_block: dict, *, fetched_at: str) -> dict:
    rows = list(raw_block.get("rows") or [])
    latest = _latest_date(rows)
    latest_rows = [row for row in rows if _row_date(row) == latest]
    normalized = []
    for row in latest_rows:
        normalized.append(
            {
                "level": _pick_text(row, ("HoldingSharesLevel", "holding_level", "level", "持股分級")) or "--",
                "people": _round_or_none(_pick_number(row, ("people", "People", "人數"))),
                "ratio_pct": _round_or_none(_pick_number(row, ("percent", "ratio", "holding_ratio", "占比"))),
            }
        )
    return _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=latest or str(raw_block.get("data_as_of") or ""),
        summary={"count": len(normalized)},
        rows=normalized[:30],
    )


def _map_securities_lending(raw_block: dict, *, fetched_at: str) -> dict:
    rows = list(raw_block.get("rows") or [])
    latest_row = _pick_latest_row(rows)
    summary = {
        "lending_balance": _round_or_none(_pick_number(latest_row, ("lending_balance", "SecuritiesLendingBalance"))),
        "lending_sell": _round_or_none(_pick_number(latest_row, ("lending_sell", "SecuritiesLendingSell"))),
        "lending_return": _round_or_none(_pick_number(latest_row, ("lending_return", "SecuritiesLendingReturn"))),
    }
    return _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=_row_date(latest_row) or str(raw_block.get("data_as_of") or ""),
        summary=summary,
        rows=[],
    )


def _map_broker_branches(raw_block: dict, *, fetched_at: str) -> dict:
    rows = list(raw_block.get("rows") or [])
    latest = _latest_date(rows)
    latest_rows = [row for row in rows if _row_date(row) == latest]
    normalized = []
    for row in latest_rows:
        buy = _pick_number(row, ("buy", "buy_shares", "Buy", "買進股數"))
        sell = _pick_number(row, ("sell", "sell_shares", "Sell", "賣出股數"))
        net = _pick_number(row, ("difference", "net", "buy_sell", "買賣超股數"))
        if net is None:
            net = (buy or 0.0) - (sell or 0.0)
        normalized.append(
            {
                "broker": _pick_text(row, ("securities_trader", "broker", "券商", "branch")) or "unknown",
                "buy": _round_or_none(buy),
                "sell": _round_or_none(sell),
                "net": _round_or_none(net),
            }
        )
    normalized.sort(key=lambda item: abs(float(item.get("net") or 0.0)), reverse=True)
    return _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=latest or str(raw_block.get("data_as_of") or ""),
        summary={"count": len(normalized)},
        rows=normalized[:20],
    )


def _map_financial_statements(raw_block: dict, *, fetched_at: str) -> dict:
    sections = []
    latest = ""
    for section in raw_block.get("sections") or []:
        if not isinstance(section, dict):
            continue
        sec_rows = list(section.get("rows") or [])
        latest_date = _latest_date(sec_rows)
        if latest_date and latest_date > latest:
            latest = latest_date

        normalized_rows = []
        scoped_rows = [row for row in sec_rows if _row_date(row) == latest_date] if latest_date else sec_rows
        for row in scoped_rows[:60]:
            subject = _pick_text(row, ("type", "subject", "accounting_item", "name", "科目")) or "--"
            value = _pick_number(row, ("value", "amount", "Val", "數值"))
            if value is None:
                value = _pick_largest_numeric(row)
            normalized_rows.append({"subject": subject, "value": _round_or_none(value)})

        sections.append(
            {
                "kind": str(section.get("kind") or ""),
                "dataset": str(section.get("dataset") or ""),
                "availability": dict(section.get("availability") or {}),
                "data_as_of": latest_date or str(section.get("data_as_of") or ""),
                "rows": normalized_rows[:30],
            }
        )

    out = _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=latest or str(raw_block.get("data_as_of") or ""),
        summary={"section_count": len(sections)},
        rows=[],
    )
    out["sections"] = sections
    return out


def _map_passthrough_rows(raw_block: dict, *, fetched_at: str) -> dict:
    return _base_block(
        raw_block,
        fetched_at=fetched_at,
        data_as_of=str(raw_block.get("data_as_of") or ""),
        summary={},
        rows=list(raw_block.get("rows") or []),
    )


def _base_block(raw_block: dict, *, fetched_at: str, data_as_of: str, summary: dict, rows: list[dict]) -> dict:
    return {
        "source": "finmind",
        "dataset": str(raw_block.get("dataset") or ""),
        "availability": {
            "status": str(raw_block.get("status") or "empty"),
            "message": str(raw_block.get("message") or ""),
        },
        "status_code": int(raw_block.get("status_code") or 200),
        "fetched_at": fetched_at,
        "data_as_of": data_as_of,
        "is_delayed": _is_delayed(data_as_of),
        "summary": summary,
        "rows": rows,
    }


def _latest_date(rows: list[dict]) -> str:
    latest = ""
    for row in rows:
        current = _row_date(row)
        if current and current > latest:
            latest = current
    return latest


def _pick_latest_row(rows: list[dict]) -> dict:
    if not rows:
        return {}
    latest = _latest_date(rows)
    if not latest:
        return rows[-1] if isinstance(rows[-1], dict) else {}
    for row in reversed(rows):
        if isinstance(row, dict) and _row_date(row) == latest:
            return row
    return {}


def _row_date(row: dict) -> str:
    for key in ("date", "Date", "trade_date", "data_date", "month", "stat_date", "ym", "year_month"):
        raw = str(row.get(key) or "").strip()
        if raw:
            return raw[:10]
    year = str(row.get("year") or "").strip()
    month = str(row.get("month") or "").strip()
    if year.isdigit() and month.isdigit():
        return f"{int(year):04d}-{int(month):02d}"
    return ""


def _pick_text(row: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def _pick_number(row: dict, keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key not in row:
            continue
        parsed = _to_float(row.get(key))
        if parsed is not None:
            return parsed
    return None


def _pick_largest_numeric(row: dict) -> float | None:
    numbers: list[float] = []
    for key, value in row.items():
        text = str(key or "").strip().lower()
        if text in {"stock_id", "data_id", "name", "date", "type", "month", "year", "note"}:
            continue
        parsed = _to_float(value)
        if parsed is not None:
            numbers.append(parsed)
    if not numbers:
        return None
    numbers.sort(key=abs, reverse=True)
    return numbers[0]


def _close_n_sessions_ago(rows: list[dict], sessions: int) -> float | None:
    if not rows:
        return None
    index = len(rows) - 1 - int(sessions)
    if index < 0:
        return None
    value = rows[index].get("close")
    return float(value) if isinstance(value, (int, float)) else _to_float(value)


def _calc_return_pct(current: float | None, base: float | None) -> float | None:
    if current is None or base is None:
        return None
    if not isinstance(current, (int, float)) or not isinstance(base, (int, float)):
        return None
    if base == 0:
        return None
    return round(((float(current) - float(base)) / float(base)) * 100, 4)


def _parse_data_as_of(raw: str) -> date | None:
    text = str(raw or "").strip()
    if not text:
        return None

    normalized = text.replace("/", "-")
    try:
        if len(normalized) >= 10:
            return date.fromisoformat(normalized[:10])
        if len(normalized) == 7:
            year, month = normalized.split("-")
            return date(int(year), int(month), 1)
        if len(normalized) == 6 and normalized.isdigit():
            return date(int(normalized[:4]), int(normalized[4:6]), 1)
    except Exception:
        return None
    return None


def _to_float(raw: object) -> float | None:
    text = str(raw or "").strip().replace(",", "")
    if not text or text in {"-", "--", "nan", "None"}:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _round_or_none(raw: float | None) -> float | None:
    if raw is None:
        return None
    return round(raw, 4)


def _is_delayed(data_as_of: str) -> bool:
    parsed = str(data_as_of or "").strip()
    if not parsed:
        return True
    try:
        normalized = parsed.replace("/", "-")
        if len(normalized) == 7:
            y, m = normalized.split("-")
            target = date(int(y), int(m), 1)
            today = date.today().replace(day=1)
            return target < today
        target_day = date.fromisoformat(normalized[:10])
        return target_day < date.today()
    except Exception:
        return True
