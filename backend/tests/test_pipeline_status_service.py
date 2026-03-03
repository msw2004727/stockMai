from __future__ import annotations

import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

from backend.app.stocks.pipeline_status_service import get_pipeline_status


class PipelineStatusServiceTest(unittest.TestCase):
    @patch("backend.app.stocks.pipeline_status_service.get_settings")
    @patch("backend.app.stocks.pipeline_status_service.current_taipei_now")
    @patch("backend.app.stocks.pipeline_status_service.get_stock_universe_size", return_value=1000)
    @patch("backend.app.stocks.pipeline_status_service.load_pipeline_status_snapshot")
    def test_get_pipeline_status_ok(
        self,
        mock_snapshot,
        _mock_universe,
        mock_now,
        mock_settings,
    ):
        mock_settings.return_value = SimpleNamespace(
            database_url="postgresql://dummy",
            twse_holidays="",
        )
        mock_now.return_value = datetime(2026, 3, 4, 10, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        mock_snapshot.return_value = {
            "latest_trade_date": "2026-03-03",
            "symbol_count": 900,
            "row_count": 900,
            "source_breakdown": [{"source": "twse_openapi_stock_day_all", "rows": 900}],
        }

        result = get_pipeline_status()
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["is_healthy"])
        self.assertEqual(result["expected_trade_date"], "2026-03-03")
        self.assertEqual(result["coverage_ratio"], 0.9)

    @patch("backend.app.stocks.pipeline_status_service.get_settings")
    @patch("backend.app.stocks.pipeline_status_service.current_taipei_now")
    @patch("backend.app.stocks.pipeline_status_service.get_stock_universe_size", return_value=1000)
    @patch("backend.app.stocks.pipeline_status_service.load_pipeline_status_snapshot")
    def test_get_pipeline_status_warn_when_stale(
        self,
        mock_snapshot,
        _mock_universe,
        mock_now,
        mock_settings,
    ):
        mock_settings.return_value = SimpleNamespace(
            database_url="postgresql://dummy",
            twse_holidays="",
        )
        mock_now.return_value = datetime(2026, 3, 5, 10, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        mock_snapshot.return_value = {
            "latest_trade_date": "2026-03-03",
            "symbol_count": 600,
            "row_count": 600,
            "source_breakdown": [{"source": "twse_openapi_stock_day_all", "rows": 600}],
        }

        result = get_pipeline_status()
        self.assertEqual(result["status"], "warn")
        self.assertFalse(result["is_healthy"])
        self.assertEqual(result["lag_days"], 1)
        self.assertIn("落後目標交易日", result["note"])


if __name__ == "__main__":
    unittest.main()
