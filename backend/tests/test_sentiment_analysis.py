import unittest

from backend.modules.sentiment_analysis import build_sentiment_context


def _series(values: list[tuple[str, float, int]]) -> list[dict]:
    return [
        {
            "date": d,
            "close": close,
            "volume": volume,
        }
        for d, close, volume in values
    ]


class SentimentAnalysisTest(unittest.TestCase):
    def test_build_sentiment_context_empty(self):
        result = build_sentiment_context(symbol="2330", price_series=[])
        self.assertEqual(result["market_sentiment"], "neutral")
        self.assertEqual(result["window_days"], 0)
        self.assertEqual(result["source"], "price_action_heuristic")

    def test_build_sentiment_context_bullish_series(self):
        data = _series(
            [
                ("2026-03-01", 100.0, 1000),
                ("2026-03-02", 101.2, 1200),
                ("2026-03-03", 102.0, 1300),
                ("2026-03-04", 103.5, 1500),
                ("2026-03-05", 105.0, 1700),
            ]
        )
        result = build_sentiment_context(symbol="2330", price_series=data, window_days=20)
        self.assertEqual(result["market_sentiment"], "bullish")
        self.assertGreater(result["sentiment_score"], 0.0)
        self.assertGreater(result["price_change_pct"], 0.0)

    def test_build_sentiment_context_bearish_series(self):
        data = _series(
            [
                ("2026-03-01", 100.0, 1600),
                ("2026-03-02", 98.5, 1500),
                ("2026-03-03", 97.4, 1400),
                ("2026-03-04", 96.9, 1300),
                ("2026-03-05", 95.1, 1200),
            ]
        )
        result = build_sentiment_context(symbol="2330", price_series=data, window_days=20)
        self.assertEqual(result["market_sentiment"], "bearish")
        self.assertLess(result["sentiment_score"], 0.0)
        self.assertLess(result["price_change_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
