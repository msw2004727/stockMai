import unittest
from unittest.mock import patch

from backend.app.stocks.resolve_service import resolve_stock_query


class StockResolveServiceTest(unittest.TestCase):
    def test_resolve_exact_chinese_name(self):
        universe = [
            {"symbol": "2330", "name": "台積電", "market": "twse"},
            {"symbol": "2317", "name": "鴻海", "market": "twse"},
        ]
        with patch("backend.app.stocks.resolve_service.get_stock_universe", return_value=universe):
            payload = resolve_stock_query("台積電", limit=5)

        self.assertEqual(payload["resolution"]["status"], "resolved")
        self.assertEqual(payload["resolution"]["best"]["symbol"], "2330")
        self.assertEqual(payload["resolution"]["best"]["reason"], "exact_name")

    def test_resolve_typo_alias(self):
        universe = [
            {"symbol": "2330", "name": "台積電", "market": "twse"},
            {"symbol": "2454", "name": "聯發科", "market": "twse"},
        ]
        with patch("backend.app.stocks.resolve_service.get_stock_universe", return_value=universe):
            payload = resolve_stock_query("台機電", limit=5)

        self.assertEqual(payload["resolution"]["best"]["symbol"], "2330")
        self.assertEqual(payload["resolution"]["best"]["reason"], "alias_match")

    def test_resolve_symbol_prefix_returns_ambiguous(self):
        universe = [
            {"symbol": "2330", "name": "台積電", "market": "twse"},
            {"symbol": "2337", "name": "旺宏", "market": "twse"},
            {"symbol": "2317", "name": "鴻海", "market": "twse"},
        ]
        with patch("backend.app.stocks.resolve_service.get_stock_universe", return_value=universe):
            payload = resolve_stock_query("23", limit=5)

        self.assertEqual(payload["resolution"]["status"], "ambiguous")
        self.assertGreaterEqual(len(payload["resolution"]["candidates"]), 2)

    def test_resolve_not_found(self):
        universe = [
            {"symbol": "2330", "name": "台積電", "market": "twse"},
            {"symbol": "2454", "name": "聯發科", "market": "twse"},
        ]
        with patch("backend.app.stocks.resolve_service.get_stock_universe", return_value=universe):
            payload = resolve_stock_query("不存在股票", limit=5)

        self.assertEqual(payload["resolution"]["status"], "not_found")
        self.assertEqual(payload["resolution"]["candidates"], [])
        self.assertIsNone(payload["resolution"]["best"])


if __name__ == "__main__":
    unittest.main()
