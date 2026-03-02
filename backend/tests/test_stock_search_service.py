import unittest
from unittest.mock import patch

from backend.app.stocks.search_service import search_stock_symbols


class StockSearchServiceTest(unittest.TestCase):
    def test_search_by_chinese_name(self):
        universe = [
            {"symbol": "2330", "name": "台積電", "market": "twse"},
            {"symbol": "2317", "name": "鴻海", "market": "twse"},
            {"symbol": "00878", "name": "國泰永續高股息", "market": "twse"},
        ]
        with patch("backend.app.stocks.search_service._load_universe", return_value=universe):
            results = search_stock_symbols("台積", limit=5)
            self.assertGreaterEqual(len(results), 1)
            self.assertEqual(results[0]["symbol"], "2330")
            self.assertEqual(results[0]["name"], "台積電")

    def test_search_by_symbol_prefix(self):
        universe = [
            {"symbol": "2330", "name": "台積電", "market": "twse"},
            {"symbol": "2337", "name": "旺宏", "market": "twse"},
            {"symbol": "2317", "name": "鴻海", "market": "twse"},
        ]
        with patch("backend.app.stocks.search_service._load_universe", return_value=universe):
            results = search_stock_symbols("23", limit=5)
            self.assertEqual([item["symbol"] for item in results[:2]], ["2317", "2330"])

    def test_search_returns_empty_for_blank_query(self):
        results = search_stock_symbols("   ", limit=5)
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
