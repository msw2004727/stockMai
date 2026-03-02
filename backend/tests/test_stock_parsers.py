import unittest

from backend.app.stocks.parsers import (
    extract_stock_name,
    parse_daily_row,
    parse_float,
    parse_roc_date,
)


class StockParsersTest(unittest.TestCase):
    def test_parse_roc_date(self):
        self.assertEqual(parse_roc_date("114/03/02"), "2025-03-02")

    def test_parse_float(self):
        self.assertEqual(parse_float("+1,234.50"), 1234.50)
        with self.assertRaises(ValueError):
            parse_float("--")

    def test_extract_stock_name(self):
        title = "114年03月 2330 台積電 各日成交資訊"
        self.assertEqual(extract_stock_name(title, "2330"), "台積電")

    def test_parse_daily_row(self):
        row = [
            "114/03/02",
            "12,345",
            "0",
            "100.5",
            "105.0",
            "99.0",
            "103.0",
            "+2.5",
            "0",
            "0",
        ]
        result = parse_daily_row(row)
        self.assertIsNotNone(result)
        self.assertEqual(result["date"], "2025-03-02")
        self.assertEqual(result["volume"], 12345)
        self.assertEqual(result["open"], 100.5)
        self.assertEqual(result["high"], 105.0)
        self.assertEqual(result["low"], 99.0)
        self.assertEqual(result["close"], 103.0)
        self.assertEqual(result["change"], 2.5)


if __name__ == "__main__":
    unittest.main()
