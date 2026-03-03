from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.stocks.market_snapshot_service import (
    MarketSnapshotSyncError,
    run_market_snapshot,
)
from backend.modules.data_pipeline.snapshot_storage import SnapshotStorageError


class MarketSnapshotServiceTest(unittest.TestCase):
    @patch("backend.app.stocks.market_snapshot_service.get_stock_universe_size", return_value=2000)
    @patch("backend.app.stocks.market_snapshot_service.get_settings")
    @patch("backend.app.stocks.market_snapshot_service.fetch_twse_market_snapshots")
    @patch("backend.app.stocks.market_snapshot_service.upsert_price_snapshots")
    def test_run_market_snapshot_success(
        self,
        mock_upsert,
        mock_fetch,
        mock_settings,
        _mock_universe,
    ):
        mock_settings.return_value = SimpleNamespace(database_url="postgresql://dummy")
        mock_fetch.return_value = {
            "snapshots": [
                {
                    "symbol": "2330",
                    "name": "2330",
                    "date": "2026-03-03",
                    "open": 1000.0,
                    "high": 1010.0,
                    "low": 995.0,
                    "close": 1008.0,
                    "change": 8.0,
                    "volume": 1000,
                },
                {
                    "symbol": "2317",
                    "name": "2317",
                    "date": "2026-03-03",
                    "open": 150.0,
                    "high": 152.0,
                    "low": 149.0,
                    "close": 151.0,
                    "change": 1.0,
                    "volume": 2000,
                },
            ],
            "fetched_rows": 4,
            "parsed_rows": 3,
            "valid_rows": 2,
            "invalid_rows": 1,
            "deduped_rows": 1,
        }
        mock_upsert.return_value = 2

        result = run_market_snapshot(max_symbols=3000)
        self.assertTrue(result["ok"])
        self.assertEqual(result["trade_date"], "2026-03-03")
        self.assertEqual(result["fetched_rows"], 4)
        self.assertEqual(result["valid_rows"], 2)
        self.assertEqual(result["inserted_rows"], 2)
        self.assertEqual(result["expected_universe_size"], 2000)
        self.assertEqual(result["coverage_ratio"], 0.001)

    @patch("backend.app.stocks.market_snapshot_service.get_settings")
    @patch(
        "backend.app.stocks.market_snapshot_service.fetch_twse_market_snapshots",
        return_value={"snapshots": [], "fetched_rows": 0},
    )
    def test_run_market_snapshot_raises_when_no_data(self, _mock_fetch, mock_settings):
        mock_settings.return_value = SimpleNamespace(database_url="postgresql://dummy")
        with self.assertRaises(MarketSnapshotSyncError):
            run_market_snapshot(max_symbols=3000)

    @patch("backend.app.stocks.market_snapshot_service.get_settings")
    @patch("backend.app.stocks.market_snapshot_service.fetch_twse_market_snapshots")
    @patch(
        "backend.app.stocks.market_snapshot_service.upsert_price_snapshots",
        side_effect=SnapshotStorageError("permission denied for table stock_daily_prices"),
    )
    def test_run_market_snapshot_raises_with_storage_detail(
        self,
        _mock_upsert,
        mock_fetch,
        mock_settings,
    ):
        mock_settings.return_value = SimpleNamespace(database_url="postgresql://dummy")
        mock_fetch.return_value = {
            "snapshots": [
                {
                    "symbol": "2330",
                    "name": "2330",
                    "date": "2026-03-03",
                    "open": 1000.0,
                    "high": 1010.0,
                    "low": 995.0,
                    "close": 1008.0,
                    "change": 8.0,
                    "volume": 1000,
                }
            ],
            "fetched_rows": 1,
            "parsed_rows": 1,
            "valid_rows": 1,
            "invalid_rows": 0,
            "deduped_rows": 0,
        }

        with self.assertRaisesRegex(MarketSnapshotSyncError, "permission denied"):
            run_market_snapshot(max_symbols=3000)


if __name__ == "__main__":
    unittest.main()
