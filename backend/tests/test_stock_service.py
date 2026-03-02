import unittest
from unittest.mock import patch

from backend.app.stocks.service import SymbolNotFoundError, get_history, get_quote


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

    @patch("backend.app.stocks.service._fetch_quote_from_twse", side_effect=RuntimeError("twse error"))
    @patch("backend.app.stocks.service._fetch_quote_from_finmind", side_effect=RuntimeError("finmind error"))
    def test_get_quote_fallback_demo(self, _mock_finmind, _mock_twse):
        result = get_quote("2330")
        self.assertEqual(result["symbol"], "2330")
        self.assertEqual(result["source"], "demo")
        self.assertTrue(result["is_fallback"])

    @patch("backend.app.stocks.service._fetch_quote_from_twse", side_effect=RuntimeError("twse error"))
    @patch("backend.app.stocks.service._fetch_quote_from_finmind", side_effect=RuntimeError("finmind error"))
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
        mock_twse.assert_not_called()

    @patch("backend.app.stocks.service._fetch_history_from_twse", side_effect=RuntimeError("twse error"))
    @patch("backend.app.stocks.service._fetch_history_from_finmind", side_effect=RuntimeError("finmind error"))
    def test_get_history_fallback_demo(self, _mock_finmind, _mock_twse):
        result = get_history("2330", 20)
        self.assertEqual(result["symbol"], "2330")
        self.assertEqual(result["days"], 20)
        self.assertEqual(result["source"], "demo")
        self.assertEqual(len(result["series"]), 20)
        self.assertEqual(len(result["ohlc"]), 20)
        self.assertEqual(len(result["ohlc"][0]), 6)

    @patch("backend.app.stocks.service._fetch_history_from_twse", side_effect=RuntimeError("twse error"))
    @patch("backend.app.stocks.service._fetch_history_from_finmind", side_effect=RuntimeError("finmind error"))
    def test_get_history_symbol_not_found(self, _mock_finmind, _mock_twse):
        with self.assertRaises(SymbolNotFoundError):
            get_history("9999", 5)


if __name__ == "__main__":
    unittest.main()
