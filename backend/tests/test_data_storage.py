from __future__ import annotations

import unittest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from backend.modules.data_pipeline.storage import (
    load_latest_quote,
    load_recent_history,
    upsert_price_series,
)


class _FakeCursor:
    def __init__(self, row: dict | None = None, rows: list[dict] | None = None):
        self._row = row
        self._rows = rows or []
        self.executemany_payload = None

    def execute(self, _sql: str, _params=None) -> None:
        return None

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows

    def executemany(self, _sql: str, payload) -> None:
        self.executemany_payload = list(payload)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DataStorageTest(unittest.TestCase):
    def test_load_latest_quote_returns_postgres_payload(self):
        fake_row = {
            "symbol": "2330",
            "trade_date": date.today(),
            "open": Decimal("100"),
            "high": Decimal("101"),
            "low": Decimal("99"),
            "close": Decimal("100.5"),
            "change": Decimal("0.5"),
            "volume": 1234,
        }
        fake_cursor = _FakeCursor(row=fake_row)
        fake_connection = _FakeConnection(cursor=fake_cursor)

        with patch("backend.modules.data_pipeline.storage._connect", return_value=fake_connection):
            result = load_latest_quote("postgresql://dummy", "2330")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["symbol"], "2330")
        self.assertEqual(result["source"], "postgres")
        self.assertEqual(result["close"], 100.5)

    def test_load_latest_quote_returns_none_when_stale(self):
        fake_row = {
            "symbol": "2330",
            "trade_date": date.today() - timedelta(days=20),
            "open": Decimal("100"),
            "high": Decimal("101"),
            "low": Decimal("99"),
            "close": Decimal("100.5"),
            "change": Decimal("0.5"),
            "volume": 1234,
        }
        fake_cursor = _FakeCursor(row=fake_row)
        fake_connection = _FakeConnection(cursor=fake_cursor)

        with patch("backend.modules.data_pipeline.storage._connect", return_value=fake_connection):
            result = load_latest_quote("postgresql://dummy", "2330", max_age_days=7)

        self.assertIsNone(result)

    def test_load_latest_quote_returns_none_when_non_positive_close(self):
        fake_row = {
            "symbol": "2330",
            "trade_date": date.today(),
            "open": Decimal("100"),
            "high": Decimal("101"),
            "low": Decimal("99"),
            "close": Decimal("0"),
            "change": Decimal("0"),
            "volume": 1234,
        }
        fake_cursor = _FakeCursor(row=fake_row)
        fake_connection = _FakeConnection(cursor=fake_cursor)

        with patch("backend.modules.data_pipeline.storage._connect", return_value=fake_connection):
            result = load_latest_quote("postgresql://dummy", "2330")

        self.assertIsNone(result)

    def test_load_recent_history_returns_none_when_insufficient_rows(self):
        fake_rows = [
            {
                "symbol": "2330",
                "trade_date": date.today(),
                "open": Decimal("100"),
                "high": Decimal("101"),
                "low": Decimal("99"),
                "close": Decimal("100.5"),
                "change": Decimal("0.5"),
                "volume": 1234,
            }
        ]
        fake_cursor = _FakeCursor(rows=fake_rows)
        fake_connection = _FakeConnection(cursor=fake_cursor)

        with patch("backend.modules.data_pipeline.storage._connect", return_value=fake_connection):
            result = load_recent_history("postgresql://dummy", "2330", days=2)

        self.assertIsNone(result)

    def test_upsert_price_series_returns_inserted_count(self):
        fake_cursor = _FakeCursor()
        fake_connection = _FakeConnection(cursor=fake_cursor)
        series = [
            {
                "date": "2026-03-01",
                "open": 100.0,
                "high": 101.0,
                "low": 99.5,
                "close": 100.5,
                "change": 0.5,
                "volume": 1000,
            },
            {
                "date": "2026-03-02",
                "open": 100.5,
                "high": 102.0,
                "low": 100.0,
                "close": 101.2,
                "change": 0.7,
                "volume": 1200,
            },
        ]

        with patch("backend.modules.data_pipeline.storage._connect", return_value=fake_connection):
            count = upsert_price_series("postgresql://dummy", "2330", series=series, source="finmind")

        self.assertEqual(count, 2)
        self.assertEqual(len(fake_cursor.executemany_payload or []), 2)

    def test_upsert_price_series_skips_non_positive_rows(self):
        fake_cursor = _FakeCursor()
        fake_connection = _FakeConnection(cursor=fake_cursor)
        series = [
            {
                "date": "2026-03-01",
                "open": 100.0,
                "high": 101.0,
                "low": 99.5,
                "close": 100.5,
                "change": 0.5,
                "volume": 1000,
            },
            {
                "date": "2026-03-02",
                "open": 0.0,
                "high": 0.0,
                "low": 0.0,
                "close": 0.0,
                "change": 0.0,
                "volume": 1200,
            },
        ]

        with patch("backend.modules.data_pipeline.storage._connect", return_value=fake_connection):
            count = upsert_price_series("postgresql://dummy", "2330", series=series, source="twse")

        self.assertEqual(count, 1)
        self.assertEqual(len(fake_cursor.executemany_payload or []), 1)


if __name__ == "__main__":
    unittest.main()
