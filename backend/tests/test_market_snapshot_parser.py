from __future__ import annotations

import unittest
from datetime import date

from backend.app.stocks.market_snapshot_parser import parse_snapshot_row


class MarketSnapshotParserTest(unittest.TestCase):
    def test_parse_snapshot_row_supports_iso_date(self):
        row = {
            "Code": "2330",
            "Name": "TSMC",
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

    def test_parse_snapshot_row_supports_twse_openapi_fields(self):
        row = {
            "Code": "0050",
            "Name": "ETF 50",
            "Date": "1150302",
            "OpeningPrice": "79.50",
            "HighestPrice": "80.80",
            "LowestPrice": "79.15",
            "ClosingPrice": "80.35",
            "Change": "-0.8000",
            "TradeVolume": "224651381",
        }
        parsed = parse_snapshot_row(row, fallback_date=date(2026, 3, 3))
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["symbol"], "0050")
        self.assertEqual(parsed["date"], "2026-03-02")
        self.assertEqual(parsed["open"], 79.5)
        self.assertEqual(parsed["close"], 80.35)
        self.assertEqual(parsed["volume"], 224651381)

    def test_parse_snapshot_row_supports_roc_date_with_slashes(self):
        row = {
            "Code": "2317",
            "Name": "Hon Hai",
            "Date": "115/03/03",
            "OpeningPrice": "150",
            "HighestPrice": "152",
            "LowestPrice": "149",
            "ClosingPrice": "151",
            "Change": "1",
            "TradeVolume": "2,345,678",
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
