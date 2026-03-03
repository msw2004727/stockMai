from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import psycopg


def load_latest_quote(
    database_url: str,
    symbol: str,
    max_age_days: int = 5,
) -> dict | None:
    try:
        with _connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        symbol,
                        trade_date,
                        open,
                        high,
                        low,
                        close,
                        change,
                        volume
                    FROM stock_daily_prices
                    WHERE symbol = %s
                    ORDER BY trade_date DESC
                    LIMIT 1
                    """,
                    (symbol,),
                )
                row = cur.fetchone()
    except Exception:
        return None

    if row is None:
        return None

    trade_date = row["trade_date"]
    if not isinstance(trade_date, date):
        return None
    if _is_stale(trade_date, max_age_days):
        return None

    open_price = _to_positive_float(row["open"])
    high = _to_positive_float(row["high"])
    low = _to_positive_float(row["low"])
    close = _to_positive_float(row["close"])
    if open_price is None or high is None or low is None or close is None:
        return None

    return {
        "symbol": symbol,
        "name": symbol,
        "as_of_date": trade_date.isoformat(),
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "change": _to_float(row["change"]),
        "volume": int(row["volume"] or 0),
        "source": "postgres",
        "is_fallback": False,
        "note": "Loaded from PostgreSQL cache.",
    }


def load_recent_history(
    database_url: str,
    symbol: str,
    days: int,
    max_age_days: int = 7,
) -> dict | None:
    try:
        with _connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        symbol,
                        trade_date,
                        open,
                        high,
                        low,
                        close,
                        change,
                        volume
                    FROM stock_daily_prices
                    WHERE symbol = %s
                    ORDER BY trade_date DESC
                    LIMIT %s
                    """,
                    (symbol, days),
                )
                rows = cur.fetchall()
    except Exception:
        return None

    if len(rows) < days:
        return None

    latest_trade_date = rows[0].get("trade_date")
    if not isinstance(latest_trade_date, date):
        return None
    if _is_stale(latest_trade_date, max_age_days):
        return None

    normalized = sorted(rows, key=lambda row: row["trade_date"])
    series: list[dict] = []
    for row in normalized:
        open_price = _to_positive_float(row["open"])
        high = _to_positive_float(row["high"])
        low = _to_positive_float(row["low"])
        close = _to_positive_float(row["close"])
        if open_price is None or high is None or low is None or close is None:
            continue

        series.append(
            {
                "date": row["trade_date"].isoformat(),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "change": _to_float(row["change"]),
                "volume": int(row["volume"] or 0),
            }
        )

    if len(series) < days:
        return None

    return {
        "symbol": symbol,
        "name": symbol,
        "days": len(series),
        "series": series,
        "ohlc": _to_ohlc_series(series),
        "source": "postgres",
        "is_fallback": False,
        "note": "Loaded from PostgreSQL cache.",
    }


def upsert_price_series(
    database_url: str,
    symbol: str,
    series: list[dict],
    source: str,
) -> int:
    payload = _prepare_upsert_payload(symbol=symbol, series=series, source=source)
    if not payload:
        return 0

    try:
        with _connect(database_url) as conn:
            with conn.cursor() as cur:
                _upsert_or_replace(cur, payload)
    except Exception:
        return 0

    return len(payload)


def _upsert_or_replace(cur, payload: list[tuple]) -> None:
    try:
        cur.executemany(
            """
            INSERT INTO stock_daily_prices (
                symbol,
                trade_date,
                open,
                high,
                low,
                close,
                change,
                volume,
                source
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (symbol, trade_date)
            DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                change = EXCLUDED.change,
                volume = EXCLUDED.volume,
                source = EXCLUDED.source
            """,
            payload,
        )
    except Exception:
        keys = [(row[0], row[1]) for row in payload]
        cur.executemany(
            """
            DELETE FROM stock_daily_prices
            WHERE symbol = %s AND trade_date = %s
            """,
            keys,
        )
        cur.executemany(
            """
            INSERT INTO stock_daily_prices (
                symbol,
                trade_date,
                open,
                high,
                low,
                close,
                change,
                volume,
                source
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            payload,
        )


def _prepare_upsert_payload(symbol: str, series: list[dict], source: str) -> list[tuple]:
    rows: list[tuple] = []
    for item in series:
        raw_date = str(item.get("date", "")).strip()
        if not raw_date:
            continue
        try:
            trade_date = date.fromisoformat(raw_date)
        except ValueError:
            continue

        open_price = _to_positive_float(item.get("open", 0.0))
        high = _to_positive_float(item.get("high", 0.0))
        low = _to_positive_float(item.get("low", 0.0))
        close = _to_positive_float(item.get("close", 0.0))
        if open_price is None or high is None or low is None or close is None:
            continue

        rows.append(
            (
                symbol,
                trade_date,
                open_price,
                high,
                low,
                close,
                _to_float(item.get("change", 0.0)),
                int(item.get("volume") or 0),
                source,
            )
        )
    return rows


def _connect(database_url: str) -> "psycopg.Connection":
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(
        database_url,
        connect_timeout=2,
        row_factory=dict_row,
    )


def _is_stale(trade_date: date, max_age_days: int) -> bool:
    return (date.today() - trade_date).days > max(max_age_days, 0)


def _to_ohlc_series(series: list[dict]) -> list[list]:
    return [
        [
            row["date"],
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["volume"],
        ]
        for row in series
    ]


def _to_float(raw: object) -> float:
    if isinstance(raw, Decimal):
        return float(raw)
    try:
        return float(raw)
    except Exception:
        return 0.0


def _to_positive_float(raw: object) -> float | None:
    parsed = _to_float(raw)
    if parsed <= 0:
        return None
    return parsed
