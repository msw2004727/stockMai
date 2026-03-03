import unittest
from unittest.mock import patch

from backend.app.stocks.quote_provider import QuoteProviderUnavailableError
from backend.app.stocks.quote_runtime import QuoteRateLimitExceeded
from backend.app.stocks.service import (
    DataUnavailableError,
    QuoteRateLimitedError,
    SymbolNotFoundError,
    _resolve_twse_month_count,
    get_history,
    get_indicators,
    get_quote,
)


class StockServiceTest(unittest.TestCase):
    def setUp(self):
        self._patch_load_quote = patch("backend.app.stocks.service._load_quote_from_postgres", return_value=None)
        self._patch_load_history = patch("backend.app.stocks.service._load_history_from_postgres", return_value=None)
        self._patch_persist = patch("backend.app.stocks.service._persist_series_to_postgres", return_value=None)
        self._patch_short_cache = patch("backend.app.stocks.service.load_short_quote_cache", return_value=None)
        self._patch_save_short_cache = patch("backend.app.stocks.service.save_short_quote_cache", return_value=None)
        self._patch_rate_guard = patch("backend.app.stocks.service.enforce_quote_rate_guard", return_value={})
        self._patch_load_quote.start()
        self._patch_load_history.start()
        self._patch_persist.start()
        self._patch_short_cache.start()
        self._patch_save_short_cache.start()
        self._patch_rate_guard.start()

    def tearDown(self):
        self._patch_load_quote.stop()
        self._patch_load_history.stop()
        self._patch_persist.stop()
        self._patch_short_cache.stop()
        self._patch_save_short_cache.stop()
        self._patch_rate_guard.stop()

    @patch("backend.app.stocks.service.load_short_quote_cache")
    def test_get_quote_prefers_short_cache_when_available(self, mock_short_cache):
        mock_short_cache.return_value = {
            "symbol": "2330",
            "name": "TSMC",
            "as_of_date": "2026-03-02",
            "quote_time": "2026-03-02 13:25:01",
            "open": 1001.0,
            "high": 1012.0,
            "low": 998.0,
            "close": 1009.0,
            "change": 8.0,
            "volume": 1234,
            "source": "twse_realtime",
            "source_priority": "realtime_primary",
            "market_state": "trading",
            "is_realtime": True,
            "delay_seconds": 0,
            "provider_used": "twse_realtime",
            "cache_hit": False,
            "is_fallback": False,
            "note": "",
        }
        result = get_quote("2330")
        self.assertEqual(result["source"], "twse_realtime")
        self.assertTrue(result["cache_hit"])

    @patch("backend.app.stocks.service._fetch_quote_from_provider_chain")
    def test_get_quote_uses_provider_chain(self, mock_provider_chain):
        mock_provider_chain.return_value = {
            "symbol": "2330",
            "name": "2330",
            "as_of_date": "2026-03-02",
            "quote_time": "2026-03-02 14:00:00",
            "open": 1000.0,
            "high": 1010.0,
            "low": 995.0,
            "close": 1008.0,
            "change": 8.0,
            "volume": 12345678,
            "source": "finmind",
            "source_priority": "daily_fallback",
            "market_state": "daily_close",
            "is_realtime": False,
            "delay_seconds": None,
            "is_fallback": False,
            "note": "",
        }

        result = get_quote("2330")
        self.assertEqual(result["source"], "finmind")
        self.assertEqual(result["source_priority"], "daily_fallback")
        self.assertEqual(result["is_realtime"], False)
        self.assertIn("freshness", result)
        self.assertIn("is_fresh", result["freshness"])
        mock_provider_chain.assert_called_once()
        self.assertEqual(result["cache_hit"], False)
        self.assertIsInstance(result["fetch_latency_ms"], int)

    @patch("backend.app.stocks.service._fetch_quote_from_provider_chain")
    def test_get_quote_handles_realtime_source(self, mock_provider_chain):
        mock_provider_chain.return_value = {
            "symbol": "2330",
            "name": "TSMC",
            "as_of_date": "2026-03-02",
            "quote_time": "2026-03-02 13:25:01",
            "open": 1001.0,
            "high": 1012.0,
            "low": 998.0,
            "close": 1009.0,
            "change": 8.0,
            "volume": 1234,
            "source": "twse_realtime",
            "source_priority": "realtime_primary",
            "market_state": "trading",
            "is_realtime": True,
            "delay_seconds": 0,
            "is_fallback": False,
            "note": "",
        }

        result = get_quote("2330")
        self.assertEqual(result["source"], "twse_realtime")
        self.assertEqual(result["source_priority"], "realtime_primary")
        self.assertEqual(result["is_realtime"], True)
        self.assertIn("freshness", result)
        self.assertIn("is_fresh", result["freshness"])

    @patch("backend.app.stocks.service._fetch_quote_from_provider_chain")
    @patch("backend.app.stocks.service._load_quote_from_postgres")
    def test_get_quote_prefers_provider_before_postgres_cache(self, mock_load_postgres, mock_provider_chain):
        mock_load_postgres.return_value = {
            "symbol": "2330",
            "name": "TSMC",
            "as_of_date": "2026-03-02",
            "open": 1000.0,
            "high": 1005.0,
            "low": 995.0,
            "close": 998.0,
            "change": -2.0,
            "volume": 1000,
            "source": "postgres",
            "is_fallback": False,
            "note": "",
        }
        mock_provider_chain.return_value = {
            "symbol": "2330",
            "name": "TSMC",
            "as_of_date": "2026-03-02",
            "quote_time": "2026-03-02 13:25:01",
            "open": 1001.0,
            "high": 1012.0,
            "low": 998.0,
            "close": 1009.0,
            "change": 8.0,
            "volume": 1234,
            "source": "twse_realtime",
            "source_priority": "realtime_primary",
            "market_state": "trading",
            "is_realtime": True,
            "delay_seconds": 0,
            "is_fallback": False,
            "note": "",
        }

        result = get_quote("2330")
        self.assertEqual(result["source"], "twse_realtime")
        self.assertEqual(result["provider_used"], "twse_realtime")
        mock_provider_chain.assert_called_once()

    @patch(
        "backend.app.stocks.service._fetch_quote_from_provider_chain",
        side_effect=QuoteProviderUnavailableError("All quote providers failed."),
    )
    @patch("backend.app.stocks.service._load_quote_from_postgres")
    def test_get_quote_falls_back_to_postgres_when_provider_unavailable(self, mock_load_postgres, _mock_provider_chain):
        mock_load_postgres.return_value = {
            "symbol": "2330",
            "name": "TSMC",
            "as_of_date": "2026-03-02",
            "open": 1000.0,
            "high": 1005.0,
            "low": 995.0,
            "close": 998.0,
            "change": -2.0,
            "volume": 1000,
            "source": "postgres",
            "is_fallback": False,
            "note": "",
        }

        result = get_quote("2330")
        self.assertEqual(result["source"], "postgres")
        self.assertEqual(result["provider_used"], "postgres")
        self.assertEqual(result["source_priority"], "cache")
        self.assertIn("freshness", result)

    @patch("backend.app.stocks.service._fetch_quote_from_provider_chain")
    @patch("backend.app.stocks.service._load_quote_from_postgres")
    def test_get_quote_uses_postgres_when_provider_payload_is_invalid(self, mock_load_postgres, mock_provider_chain):
        mock_load_postgres.return_value = {
            "symbol": "3231",
            "name": "Wistron",
            "as_of_date": "2026-03-03",
            "open": 131.0,
            "high": 132.0,
            "low": 130.5,
            "close": 131.5,
            "change": -2.5,
            "volume": 2000,
            "source": "postgres",
            "is_fallback": False,
            "note": "",
        }
        mock_provider_chain.return_value = {
            "symbol": "3231",
            "name": "Wistron",
            "as_of_date": "2026-03-03",
            "quote_time": "2026-03-03 12:58:31",
            "open": 0.0,
            "high": 0.0,
            "low": 0.0,
            "close": 0.0,
            "change": 0.0,
            "volume": 0,
            "source": "twse_realtime",
            "source_priority": "realtime_primary",
            "market_state": "trading",
            "is_realtime": True,
            "delay_seconds": 0,
            "is_fallback": False,
            "note": "",
        }

        result = get_quote("3231")
        self.assertEqual(result["source"], "postgres")
        self.assertEqual(result["close"], 131.5)

    @patch(
        "backend.app.stocks.service._fetch_quote_from_provider_chain",
        side_effect=QuoteProviderUnavailableError("All quote providers failed."),
    )
    def test_get_quote_raises_data_unavailable_when_all_sources_fail(self, _mock_provider_chain):
        with self.assertRaises(DataUnavailableError):
            get_quote("2330")

    @patch("backend.app.stocks.service._fetch_quote_from_provider_chain", return_value=None)
    def test_get_quote_symbol_not_found(self, _mock_provider_chain):
        with self.assertRaises(SymbolNotFoundError):
            get_quote("9999")

    @patch(
        "backend.app.stocks.service.enforce_quote_rate_guard",
        side_effect=QuoteRateLimitExceeded("Quote rate limit exceeded"),
    )
    def test_get_quote_raises_when_rate_limited(self, _mock_guard):
        with self.assertRaises(QuoteRateLimitedError):
            get_quote("2330")

    @patch("backend.app.stocks.service.get_settings")
    @patch("backend.app.stocks.service._fetch_history_from_twse")
    @patch("backend.app.stocks.service._fetch_history_from_finmind")
    def test_get_history_prefers_finmind(self, mock_finmind, mock_twse, mock_get_settings):
        class _S:
            finmind_token = "token"

        mock_get_settings.return_value = _S()

        mock_finmind.return_value = {
            "symbol": "2330",
            "name": "2330",
            "days": 5,
            "series": [
                {
                    "date": "2026-02-24",
                    "open": 1000.0,
                    "high": 1010.0,
                    "low": 998.0,
                    "close": 1005.0,
                    "change": 5.0,
                    "volume": 1000,
                }
            ]
            * 5,
            "ohlc": [["2026-02-24", 1000.0, 1010.0, 998.0, 1005.0, 1000]] * 5,
            "source": "finmind",
            "is_fallback": False,
            "note": "",
        }
        result = get_history("2330", 5)
        self.assertEqual(result["source"], "finmind")
        self.assertIn("freshness", result)
        self.assertIn("is_fresh", result["freshness"])
        mock_twse.assert_not_called()

    @patch("backend.app.stocks.service.get_settings")
    @patch("backend.app.stocks.service._fetch_history_from_twse", side_effect=RuntimeError("twse error"))
    @patch("backend.app.stocks.service._fetch_history_from_finmind", side_effect=RuntimeError("finmind error"))
    def test_get_history_raises_data_unavailable_when_all_sources_fail(
        self,
        _mock_finmind,
        _mock_twse,
        mock_get_settings,
    ):
        class _S:
            finmind_token = "token"

        mock_get_settings.return_value = _S()

        with self.assertRaises(DataUnavailableError):
            get_history("2330", 20)

    @patch("backend.app.stocks.service.get_settings")
    @patch("backend.app.stocks.service._fetch_history_from_twse", side_effect=RuntimeError("twse error"))
    def test_get_history_raises_data_unavailable_when_finmind_not_configured(
        self,
        _mock_twse,
        mock_get_settings,
    ):
        class _S:
            finmind_token = ""

        mock_get_settings.return_value = _S()

        with self.assertRaises(DataUnavailableError):
            get_history("2330", 20)

    @patch("backend.app.stocks.service._fetch_history_from_twse", return_value=None)
    @patch("backend.app.stocks.service._fetch_history_from_finmind", return_value=None)
    def test_get_history_symbol_not_found(self, _mock_finmind, _mock_twse):
        with self.assertRaises(SymbolNotFoundError):
            get_history("9999", 5)

    @patch("backend.app.stocks.service.get_history")
    def test_get_indicators_from_history(self, mock_get_history):
        mock_get_history.return_value = {
            "symbol": "2330",
            "days": 30,
            "series": [
                {
                    "date": f"2026-03-{idx:02d}",
                    "close": float(idx),
                    "open": float(idx),
                    "high": float(idx),
                    "low": float(idx),
                    "change": 0.0,
                    "volume": 1000,
                }
                for idx in range(1, 31)
            ],
            "source": "postgres",
            "is_fallback": False,
            "note": "",
        }

        result = get_indicators("2330", 30)
        self.assertEqual(result["symbol"], "2330")
        self.assertEqual(result["history_source"], "postgres")
        self.assertEqual(result["days"], 30)
        self.assertEqual(len(result["series"]), 30)
        self.assertIn("freshness", result)
        self.assertIn("is_fresh", result["freshness"])
        self.assertIn(result["indicator_engine"], {"talib", "python"})
        self.assertIn("sma5", result["latest"])
        self.assertIn("rsi14", result["latest"])
        self.assertIn("macd", result["latest"])

    @patch("backend.app.stocks.service.get_history", side_effect=SymbolNotFoundError("missing"))
    def test_get_indicators_raises_symbol_not_found(self, _mock_get_history):
        with self.assertRaises(SymbolNotFoundError):
            get_indicators("9999", 30)

    def test_resolve_twse_month_count_scales_with_days(self):
        self.assertEqual(_resolve_twse_month_count(5), 6)
        self.assertEqual(_resolve_twse_month_count(20), 6)
        self.assertEqual(_resolve_twse_month_count(90), 7)
        self.assertEqual(_resolve_twse_month_count(180), 11)
        self.assertEqual(_resolve_twse_month_count(999), 18)


if __name__ == "__main__":
    unittest.main()
