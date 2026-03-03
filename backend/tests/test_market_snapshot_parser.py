from __future__ import annotations

import unittest
from datetime import date

from backend.app.stocks.market_snapshot_parser import parse_snapshot_row


class MarketSnapshotParserTest(unittest.TestCase):
    def test_parse_snapshot_row_supports_iso_date(self):
        row = {
            "Code": "2330",
            "Name": "台積電",
            "Date": "2026-03-03",
            "Open": "1000.0",
            "High": "1012.0",
            "Low": "998.0",
            "Close": "1008.0",
            "Change": "+8.0",
            "TradeVolume": "12,345,678",
        }
        parsed = parse_snapshot_row(row, fallback_date=date(2026, 3, 3))
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["symbol"], "2330")
        self.assertEqual(parsed["date"], "2026-03-03")
        self.assertEqual(parsed["close"], 1008.0)
        self.assertEqual(parsed["volume"], 12345678)

    def test_parse_snapshot_row_supports_roc_date(self):
        row = {
            "證券代號": "2317",
            "證券名稱": "鴻海",
            "交易日期": "115/03/03",
            "開盤價": "150",
            "最高價": "152",
            "最低價": "149",
            "收盤價": "151",
            "漲跌價差": "1",
            "成交股數": "2,345,678",
        }
        parsed = parse_snapshot_row(row, fallback_date=date(2026, 3, 3))
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["symbol"], "2317")
        self.assertEqual(parsed["date"], "2026-03-03")
        self.assertEqual(parsed["volume"], 2345678)

    def test_parse_snapshot_row_rejects_invalid_prices(self):
        row = {
            "Code": "2330",
            "Date": "20260303",
            "Open": "0",
            "High": "1012.0",
            "Low": "998.0",
            "Close": "1008.0",
            "TradeVolume": "1234",
        }
        parsed = parse_snapshot_row(row, fallback_date=date(2026, 3, 3))
        self.assertIsNone(parsed)


if __name__ == "__main__":
    unittest.main()
