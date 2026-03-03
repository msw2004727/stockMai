from __future__ import annotations

from datetime import date
from decimal import Decimal


def upsert_price_snapshots(
    database_url: str,
    snapshots: list[dict],
    source: str,
) -> int:
    payload = _prepare_payload(snapshots=snapshots, source=source)
    if not payload:
        return 0

    try:
        with _connect(database_url) as conn:
            with conn.cursor() as cur:
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
        return 0

    return len(payload)


def _prepare_payload(snapshots: list[dict], source: str) -> list[tuple]:
    rows: list[tuple] = []
    for item in snapshots:
        symbol = str(item.get("symbol") or "").strip()
        if not symbol:
            continue

        raw_date = str(item.get("date") or "").strip()
        if not raw_date:
            continue

        try:
            trade_date = date.fromisoformat(raw_date)
        except ValueError:
            continue

        open_price = _to_positive_float(item.get("open"))
        high = _to_positive_float(item.get("high"))
        low = _to_positive_float(item.get("low"))
        close = _to_positive_float(item.get("close"))
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


def _connect(database_url: str):
    import psycopg

    return psycopg.connect(
        database_url,
        connect_timeout=3,
    )


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
