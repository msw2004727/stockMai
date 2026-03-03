from __future__ import annotations

import unittest
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

from backend.app.stocks.movers_service import get_market_movers


class MoversServiceTest(unittest.TestCase):
    @patch("backend.app.stocks.movers_service.get_stock_universe_size", return_value=1000)
    @patch("backend.app.stocks.movers_service.load_previous_day_movers")
    @patch("backend.app.stocks.movers_service.get_settings")
    @patch("backend.app.stocks.movers_service.current_taipei_now")
    def test_get_market_movers_enriches_coverage(
        self,
        mock_now,
        mock_settings,
        mock_load,
        _mock_universe,
    ):
        mock_now.return_value = datetime(2026, 3, 3, 10, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        mock_settings.return_value = SimpleNamespace(
            database_url="postgresql://dummy",
            twse_holidays="",
        )
        mock_load.return_value = {
            "as_of_date": "2026-03-02",
            "requested_trade_date": "2026-03-02",
            "limit": 6,
            "source": "postgres",
            "universe_size": 128,
            "is_partial_universe": True,
            "categories": {
                "top_volume": [],
                "top_gainers": [],
                "top_losers": [],
            },
            "note": "base",
        }

        result = get_market_movers(limit=6)
        self.assertEqual(result["requested_trade_date"], "2026-03-02")
        self.assertEqual(result["expected_universe_size"], 1000)
        self.assertEqual(result["coverage_ratio"], 0.128)
        self.assertTrue(result["is_partial_universe"])
        self.assertIn("樣本", result["note"])

    @patch("backend.app.stocks.movers_service.get_stock_universe_size", return_value=0)
    @patch("backend.app.stocks.movers_service.load_previous_day_movers")
    @patch("backend.app.stocks.movers_service.get_settings")
    @patch("backend.app.stocks.movers_service.current_taipei_now")
    def test_get_market_movers_appends_fallback_note(
        self,
        mock_now,
        mock_settings,
        mock_load,
        _mock_universe,
    ):
        mock_now.return_value = datetime(2026, 3, 3, 10, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        mock_settings.return_value = SimpleNamespace(
            database_url="postgresql://dummy",
            twse_holidays=str(date(2026, 3, 2)),
        )
        mock_load.return_value = {
            "as_of_date": "2026-02-27",
            "requested_trade_date": "2026-02-27",
            "limit": 6,
            "source": "postgres",
            "universe_size": 128,
            "is_partial_universe": True,
            "categories": {
                "top_volume": [],
                "top_gainers": [],
                "top_losers": [],
            },
            "note": "base",
        }

        result = get_market_movers(limit=6)
        self.assertEqual(result["requested_trade_date"], "2026-02-27")
        self.assertIn("覆蓋率僅供參考", result["note"])


if __name__ == "__main__":
    unittest.main()
