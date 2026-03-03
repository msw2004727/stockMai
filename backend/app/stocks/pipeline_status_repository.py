from __future__ import annotations

from datetime import date


def load_pipeline_status_snapshot(database_url: str) -> dict:
    with _connect(database_url) as conn:
        with conn.cursor() as cur:
            latest_trade_date = _load_latest_trade_date(cur)
            if latest_trade_date is None:
                return {
                    "latest_trade_date": "",
                    "symbol_count": 0,
                    "row_count": 0,
                    "source_breakdown": [],
                }

            symbol_count, row_count = _load_day_counts(cur, latest_trade_date)
            source_breakdown = _load_source_breakdown(cur, latest_trade_date)

    return {
        "latest_trade_date": latest_trade_date.isoformat(),
        "symbol_count": int(symbol_count),
        "row_count": int(row_count),
        "source_breakdown": source_breakdown,
    }


def _load_latest_trade_date(cur) -> date | None:
    cur.execute("SELECT MAX(trade_date) AS trade_date FROM stock_daily_prices")
    row = cur.fetchone()
    if not row:
        return None
    value = row.get("trade_date")
    if not isinstance(value, date):
        return None
    return value


def _load_day_counts(cur, trade_date: date) -> tuple[int, int]:
    cur.execute(
        """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT symbol) AS symbol_count
        FROM stock_daily_prices
        WHERE trade_date = %s
        """,
        (trade_date,),
    )
    row = cur.fetchone() or {}
    return int(row.get("symbol_count") or 0), int(row.get("row_count") or 0)


def _load_source_breakdown(cur, trade_date: date) -> list[dict]:
    cur.execute(
        """
        SELECT source, COUNT(*) AS rows
        FROM stock_daily_prices
        WHERE trade_date = %s
        GROUP BY source
        ORDER BY rows DESC, source ASC
        """,
        (trade_date,),
    )
    rows = cur.fetchall() or []
    return [
        {
            "source": str(item.get("source") or "unknown"),
            "rows": int(item.get("rows") or 0),
        }
        for item in rows
    ]


def _connect(database_url: str):
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(
        database_url,
        connect_timeout=2,
        row_factory=dict_row,
    )
