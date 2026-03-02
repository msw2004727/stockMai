import unittest
from unittest.mock import patch

from backend.app.stocks.service import DataUnavailableError, SymbolNotFoundError, get_history, get_indicators, get_quote


class StockServiceTest(unittest.TestCase):
    def setUp(self):
        self._patch_load_quote = patch("backend.app.stocks.service._load_quote_from_postgres", return_value=None)
        self._patch_load_history = patch("backend.app.stocks.service._load_history_from_postgres", return_value=None)
        self._patch_persist = patch("backend.app.stocks.service._persist_series_to_postgres", return_value=None)
        self._patch_load_quote.start()
        self._patch_load_history.start()
        self._patch_persist.start()

    def tearDown(self):
        self._patch_load_quote.stop()
        self._patch_load_history.stop()
        self._patch_persist.stop()

    @patch("backend.app.stocks.service._fetch_quote_from_twse")
    @patch("backend.app.stocks.service._fetch_quote_from_finmind")
    def test_get_quote_prefers_finmind(self, mock_finmind, mock_twse):
        mock_finmind.return_value = {
            "symbol": "2330",
            "name": "2330",
            "as_of_date": "2026-03-02",
            "open": 1000.0,
            "high": 1010.0,
            "low": 995.0,
            "close": 1008.0,
            "change": 8.0,
            "volume": 12345678,
            "source": "finmind",
            "is_fallback": False,
            "note": "",
        }

        result = get_quote("2330")
        self.assertEqual(result["source"], "finmind")
        self.assertIn("freshness", result)
        self.assertIn("is_fresh", result["freshness"])
        mock_twse.assert_not_called()

    @patch("backend.app.stocks.service._fetch_quote_from_twse")
    @patch("backend.app.stocks.service._fetch_quote_from_finmind", return_value=None)
    def test_get_quote_fallback_twse_after_finmind_miss(self, _mock_finmind, mock_twse):
        mock_twse.return_value = {
            "symbol": "2330",
            "name": "TSMC",
            "as_of_date": "2026-03-02",
            "open": 1001.0,
            "high": 1012.0,
            "low": 998.0,
            "close": 1009.0,
            "change": 8.0,
            "volume": 1234,
            "source": "twse",
            "is_fallback": False,
            "note": "",
        }

        result = get_quote("2330")
        self.assertEqual(result["source"], "twse")
        self.assertIn("freshness", result)
        self.assertIn("is_fresh", result["freshness"])

    @patch("backend.app.stocks.service._fetch_quote_from_twse", side_effect=RuntimeError("twse error"))
    @patch("backend.app.stocks.service._fetch_quote_from_finmind", side_effect=RuntimeError("finmind error"))
    def test_get_quote_raises_data_unavailable_when_all_sources_fail(self, _mock_finmind, _mock_twse):
        with self.assertRaises(DataUnavailableError):
            get_quote("2330")

    @patch("backend.app.stocks.service._fetch_quote_from_twse", return_value=None)
    @patch("backend.app.stocks.service._fetch_quote_from_finmind", return_value=None)
    def test_get_quote_symbol_not_found(self, _mock_finmind, _mock_twse):
        with self.assertRaises(SymbolNotFoundError):
            get_quote("9999")

    @patch("backend.app.stocks.service._fetch_history_from_twse")
    @patch("backend.app.stocks.service._fetch_history_from_finmind")
    def test_get_history_prefers_finmind(self, mock_finmind, mock_twse):
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

    @patch("backend.app.stocks.service._fetch_history_from_twse", side_effect=RuntimeError("twse error"))
    @patch("backend.app.stocks.service._fetch_history_from_finmind", side_effect=RuntimeError("finmind error"))
    def test_get_history_raises_data_unavailable_when_all_sources_fail(self, _mock_finmind, _mock_twse):
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


if __name__ == "__main__":
    unittest.main()
