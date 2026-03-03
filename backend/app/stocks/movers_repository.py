from __future__ import annotations

from datetime import date
from decimal import Decimal

from backend.modules.data_pipeline.schema import ensure_stock_daily_prices_table


def load_previous_day_movers(
    database_url: str,
    limit: int = 6,
    target_trade_date: date | None = None,
) -> dict:
    safe_limit = max(1, min(int(limit), 20))

    with _connect(database_url) as conn:
        with conn.cursor() as cur:
            ensure_stock_daily_prices_table(cur)
            if target_trade_date is None:
                trade_date = _load_latest_trade_date(cur)
            else:
                trade_date = _load_latest_trade_date_on_or_before(cur, target_trade_date)

            if trade_date is None:
                return _empty_payload(limit=safe_limit, requested_trade_date=target_trade_date)

            universe_size = _load_universe_size(cur, trade_date=trade_date)
            top_volume = _load_top_volume(cur, trade_date=trade_date, limit=safe_limit)
            top_gainers = _load_top_gainers(cur, trade_date=trade_date, limit=safe_limit)
            top_losers = _load_top_losers(cur, trade_date=trade_date, limit=safe_limit)

    return {
        "as_of_date": trade_date.isoformat(),
        "requested_trade_date": target_trade_date.isoformat() if target_trade_date else "",
        "limit": safe_limit,
        "source": "postgres",
        "universe_size": int(universe_size),
        "is_partial_universe": True,
        "categories": {
            "top_volume": top_volume,
            "top_gainers": top_gainers,
            "top_losers": top_losers,
        },
        "note": "目前排行依現有快取資料計算，尚未覆蓋全市場。",
    }


def _load_latest_trade_date(cur) -> date | None:
    cur.execute("SELECT MAX(trade_date) AS trade_date FROM stock_daily_prices")
    row = cur.fetchone()
    if not row:
        return None
    trade_date = row.get("trade_date")
    if not isinstance(trade_date, date):
        return None
    return trade_date


def _load_latest_trade_date_on_or_before(cur, target_trade_date: date) -> date | None:
    cur.execute(
        """
        SELECT MAX(trade_date) AS trade_date
        FROM stock_daily_prices
        WHERE trade_date <= %s
        """,
        (target_trade_date,),
    )
    row = cur.fetchone()
    if not row:
        return None
    trade_date = row.get("trade_date")
    if not isinstance(trade_date, date):
        return None
    return trade_date


def _load_universe_size(cur, trade_date: date) -> int:
    cur.execute(
        """
        SELECT COUNT(*) AS total
        FROM stock_daily_prices
        WHERE trade_date = %s
        """,
        (trade_date,),
    )
    row = cur.fetchone() or {}
    return int(row.get("total") or 0)


def _load_top_volume(cur, trade_date: date, limit: int) -> list[dict]:
    cur.execute(
        """
        SELECT
            symbol,
            close,
            change,
            volume,
            (change / NULLIF(close - change, 0)) * 100 AS change_pct
        FROM stock_daily_prices
        WHERE trade_date = %s
          AND close > 0
          AND volume > 0
        ORDER BY volume DESC, symbol ASC
        LIMIT %s
        """,
        (trade_date, limit),
    )
    return _normalize_rows(cur.fetchall())


def _load_top_gainers(cur, trade_date: date, limit: int) -> list[dict]:
    cur.execute(
        """
        SELECT
            symbol,
            close,
            change,
            volume,
            (change / NULLIF(close - change, 0)) * 100 AS change_pct
        FROM stock_daily_prices
        WHERE trade_date = %s
          AND close > 0
          AND (change / NULLIF(close - change, 0)) * 100 > 0
        ORDER BY change_pct DESC, symbol ASC
        LIMIT %s
        """,
        (trade_date, limit),
    )
    return _normalize_rows(cur.fetchall())


def _load_top_losers(cur, trade_date: date, limit: int) -> list[dict]:
    cur.execute(
        """
        SELECT
            symbol,
            close,
            change,
            volume,
            (change / NULLIF(close - change, 0)) * 100 AS change_pct
        FROM stock_daily_prices
        WHERE trade_date = %s
          AND close > 0
          AND (change / NULLIF(close - change, 0)) * 100 < 0
        ORDER BY change_pct ASC, symbol ASC
        LIMIT %s
        """,
        (trade_date, limit),
    )
    return _normalize_rows(cur.fetchall())


def _normalize_rows(rows: list[dict]) -> list[dict]:
    result: list[dict] = []
    for row in rows:
        symbol = str(row.get("symbol") or "").strip()
        if not symbol:
            continue

        close = _to_float(row.get("close"))
        change = _to_float(row.get("change"))
        change_pct = _to_float(row.get("change_pct"))
        volume = int(row.get("volume") or 0)

        if close <= 0 or volume < 0:
            continue

        result.append(
            {
                "symbol": symbol,
                "name": symbol,
                "close": round(close, 4),
                "change": round(change, 4),
                "change_pct": round(change_pct, 4),
                "volume": volume,
            }
        )
    return result


def _to_float(raw: object) -> float:
    if isinstance(raw, Decimal):
        return float(raw)
    try:
        return float(raw)
    except Exception:
        return 0.0


def _empty_payload(limit: int, requested_trade_date: date | None) -> dict:
    return {
        "as_of_date": "",
        "requested_trade_date": requested_trade_date.isoformat() if requested_trade_date else "",
        "limit": int(limit),
        "source": "postgres",
        "universe_size": 0,
        "is_partial_universe": True,
        "categories": {
            "top_volume": [],
            "top_gainers": [],
            "top_losers": [],
        },
        "note": "目前尚無可用排行資料。",
    }


def _connect(database_url: str):
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(
        database_url,
        connect_timeout=2,
        row_factory=dict_row,
    )
