import unittest
from unittest.mock import patch

from backend.app.stocks.service import SymbolNotFoundError, get_history, get_quote


class StockServiceTest(unittest.TestCase):
    @patch("backend.app.stocks.service._fetch_quote_from_twse", side_effect=RuntimeError("twse error"))
    def test_get_quote_fallback_demo(self, _mock_fetch):
        result = get_quote("2330")
        self.assertEqual(result["symbol"], "2330")
        self.assertEqual(result["source"], "demo")
        self.assertTrue(result["is_fallback"])

    @patch("backend.app.stocks.service._fetch_quote_from_twse", side_effect=RuntimeError("twse error"))
    def test_get_quote_symbol_not_found(self, _mock_fetch):
        with self.assertRaises(SymbolNotFoundError):
            get_quote("9999")

    @patch("backend.app.stocks.service._fetch_history_from_twse", side_effect=RuntimeError("twse error"))
    def test_get_history_fallback_demo(self, _mock_fetch):
        result = get_history("2330", 20)
        self.assertEqual(result["symbol"], "2330")
        self.assertEqual(result["days"], 20)
        self.assertEqual(result["source"], "demo")
        self.assertEqual(len(result["series"]), 20)
        self.assertEqual(len(result["ohlc"]), 20)
        self.assertEqual(len(result["ohlc"][0]), 6)

    @patch("backend.app.stocks.service._fetch_history_from_twse", side_effect=RuntimeError("twse error"))
    def test_get_history_symbol_not_found(self, _mock_fetch):
        with self.assertRaises(SymbolNotFoundError):
            get_history("9999", 5)


if __name__ == "__main__":
    unittest.main()
