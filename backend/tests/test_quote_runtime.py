import unittest

from backend.app.stocks.quote_runtime import (
    QuoteRateLimitExceeded,
    enforce_quote_rate_guard,
    load_short_quote_cache,
    save_short_quote_cache,
)


class QuoteRuntimeTest(unittest.TestCase):
    def test_short_cache_roundtrip_in_memory_mode(self):
        payload = {
            "symbol": "2330",
            "close": 1000.0,
            "source": "twse_realtime",
        }
        save_short_quote_cache(redis_url="", symbol="2330", payload=payload, ttl_seconds=5)
        cached = load_short_quote_cache(redis_url="", symbol="2330")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["symbol"], "2330")
        self.assertEqual(cached["source"], "twse_realtime")

    def test_quote_rate_guard_blocks_when_over_limit(self):
        redis_url = ""
        symbol = "2330"
        window_seconds = 60
        max_requests = 2

        enforce_quote_rate_guard(redis_url=redis_url, symbol=symbol, max_requests=max_requests, window_seconds=window_seconds)
        enforce_quote_rate_guard(redis_url=redis_url, symbol=symbol, max_requests=max_requests, window_seconds=window_seconds)
        with self.assertRaises(QuoteRateLimitExceeded):
            enforce_quote_rate_guard(
                redis_url=redis_url,
                symbol=symbol,
                max_requests=max_requests,
                window_seconds=window_seconds,
            )


if __name__ == "__main__":
    unittest.main()
