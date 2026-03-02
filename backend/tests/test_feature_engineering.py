import unittest

from backend.modules.feature_engineering import compute_indicator_series, compute_latest_indicators


def _build_series(start: int, end: int) -> list[dict]:
    rows = []
    for idx, close in enumerate(range(start, end + 1), start=1):
        rows.append(
            {
                "date": f"2026-03-{idx:02d}",
                "close": float(close),
            }
        )
    return rows


class FeatureEngineeringTest(unittest.TestCase):
    def test_compute_indicator_series_empty(self):
        rows = compute_indicator_series([])
        self.assertEqual(rows, [])

    def test_sma_values_are_correct(self):
        series = _build_series(1, 30)
        indicators = compute_indicator_series(series)

        self.assertIsNone(indicators[3]["sma5"])
        self.assertAlmostEqual(indicators[4]["sma5"], 3.0, places=6)
        self.assertAlmostEqual(indicators[29]["sma5"], 28.0, places=6)

        self.assertIsNone(indicators[18]["sma20"])
        self.assertAlmostEqual(indicators[19]["sma20"], 10.5, places=6)
        self.assertAlmostEqual(indicators[29]["sma20"], 20.5, places=6)

    def test_rsi_for_strict_uptrend_reaches_high_value(self):
        series = _build_series(1, 30)
        indicators = compute_indicator_series(series)
        self.assertEqual(indicators[14]["rsi14"], 100.0)
        self.assertEqual(indicators[29]["rsi14"], 100.0)

    def test_macd_fields_exist_and_are_numeric(self):
        series = _build_series(1, 30)
        indicators = compute_indicator_series(series)
        latest = indicators[-1]

        self.assertIsInstance(latest["macd"], float)
        self.assertIsInstance(latest["macd_signal"], float)
        self.assertIsInstance(latest["macd_hist"], float)

    def test_compute_latest_indicators(self):
        series = _build_series(1, 30)
        latest = compute_latest_indicators(series)
        self.assertAlmostEqual(latest["sma5"], 28.0, places=6)
        self.assertAlmostEqual(latest["sma20"], 20.5, places=6)
        self.assertEqual(latest["rsi14"], 100.0)


if __name__ == "__main__":
    unittest.main()
