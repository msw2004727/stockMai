import unittest
from unittest.mock import patch

from backend.modules.data_pipeline.normalizer import normalize_price_row, normalize_price_series
from backend.modules.data_pipeline.repository import fetch_finmind_history, fetch_finmind_quote


class DataPipelineNormalizerTest(unittest.TestCase):
    def test_normalize_price_row_success(self):
        row = {
            "date": "2026-03-01",
            "open": 100.5,
            "max": 105.0,
            "min": 99.0,
            "close": 103.2,
            "spread": 2.7,
            "Trading_Volume": 1200000,
        }
        result = normalize_price_row(row)
        self.assertIsNotNone(result)
        self.assertEqual(result["date"], "2026-03-01")
        self.assertEqual(result["open"], 100.5)
        self.assertEqual(result["high"], 105.0)
        self.assertEqual(result["low"], 99.0)
        self.assertEqual(result["close"], 103.2)
        self.assertEqual(result["change"], 2.7)
        self.assertEqual(result["volume"], 1200000)

    def test_normalize_price_series_filters_invalid_and_sorts(self):
        rows = [
            {
                "date": "2026-03-02",
                "open": 101,
                "max": 106,
                "min": 100,
                "close": 104,
                "spread": 3,
                "Trading_Volume": 2000,
            },
            {"date": "2026-03-03", "open": None},  # invalid
            {
                "date": "2026-03-01",
                "open": 100,
                "max": 103,
                "min": 99,
                "close": 102,
                "spread": 2,
                "Trading_Volume": 1000,
            },
        ]
        series = normalize_price_series(rows)
        self.assertEqual(len(series), 2)
        self.assertEqual(series[0]["date"], "2026-03-01")
        self.assertEqual(series[1]["date"], "2026-03-02")


class DataPipelineRepositoryTest(unittest.TestCase):
    @patch(
        "backend.modules.data_pipeline.repository.fetch_taiwan_stock_price",
        return_value=[
            {
                "date": "2026-02-27",
                "open": 100.0,
                "max": 102.0,
                "min": 99.0,
                "close": 101.0,
                "spread": 1.0,
                "Trading_Volume": 1000,
            },
            {
                "date": "2026-02-28",
                "open": 101.0,
                "max": 104.0,
                "min": 100.0,
                "close": 103.0,
                "spread": 2.0,
                "Trading_Volume": 2000,
            },
        ],
    )
    def test_fetch_finmind_quote_success(self, _mock_fetch):
        result = fetch_finmind_quote("2330", token="abc")
        self.assertIsNotNone(result)
        self.assertEqual(result["symbol"], "2330")
        self.assertEqual(result["source"], "finmind")
        self.assertFalse(result["is_fallback"])
        self.assertEqual(result["as_of_date"], "2026-02-28")

    @patch(
        "backend.modules.data_pipeline.repository.fetch_taiwan_stock_price",
        return_value=[
            {
                "date": "2026-02-26",
                "open": 100.0,
                "max": 101.0,
                "min": 99.0,
                "close": 100.5,
                "spread": 0.5,
                "Trading_Volume": 1000,
            },
            {
                "date": "2026-02-27",
                "open": 100.5,
                "max": 102.0,
                "min": 100.0,
                "close": 101.2,
                "spread": 0.7,
                "Trading_Volume": 1100,
            },
            {
                "date": "2026-02-28",
                "open": 101.2,
                "max": 103.0,
                "min": 100.8,
                "close": 102.1,
                "spread": 0.9,
                "Trading_Volume": 1200,
            },
        ],
    )
    def test_fetch_finmind_history_trim_to_days(self, _mock_fetch):
        result = fetch_finmind_history("2330", days=2, token="abc")
        self.assertIsNotNone(result)
        self.assertEqual(result["days"], 2)
        self.assertEqual(len(result["series"]), 2)
        self.assertEqual(len(result["ohlc"]), 2)
        self.assertEqual(result["series"][0]["date"], "2026-02-27")

    def test_fetch_finmind_quote_without_token_returns_none(self):
        result = fetch_finmind_quote("2330", token="")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

