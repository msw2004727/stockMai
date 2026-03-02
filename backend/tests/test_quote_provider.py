import unittest
from unittest.mock import patch

from backend.app.stocks.quote_provider import (
    QuoteProviderUnavailableError,
    _parse_twse_realtime_payload,
    fetch_quote_from_provider_chain,
)


class QuoteProviderTest(unittest.TestCase):
    def test_parse_twse_realtime_payload_success(self):
        payload = {
            "msgArray": [
                {
                    "c": "2330",
                    "n": "台積電",
                    "z": "1010",
                    "o": "1001",
                    "h": "1015",
                    "l": "998",
                    "y": "1000",
                    "v": "15234",
                    "d": "20260302",
                    "t": "13:25:01",
                }
            ]
        }
        result = _parse_twse_realtime_payload(payload=payload, symbol="2330")
        self.assertIsNotNone(result)
        self.assertEqual(result["symbol"], "2330")
        self.assertEqual(result["source"], "twse_realtime")
        self.assertEqual(result["source_priority"], "realtime_primary")
        self.assertTrue(result["is_realtime"])
        self.assertEqual(result["close"], 1010.0)
        self.assertEqual(result["change"], 10.0)
        self.assertEqual(result["as_of_date"], "2026-03-02")
        self.assertEqual(result["quote_time"], "2026-03-02 13:25:01")

    @patch("backend.app.stocks.quote_provider._fetch_twse_daily_quote")
    @patch("backend.app.stocks.quote_provider._fetch_finmind_daily_quote")
    @patch("backend.app.stocks.quote_provider._fetch_twse_realtime_quote")
    def test_chain_prefers_realtime(self, mock_realtime, mock_finmind, mock_twse_daily):
        mock_realtime.return_value = {
            "symbol": "2330",
            "name": "TSMC",
            "as_of_date": "2026-03-02",
            "quote_time": "2026-03-02 10:30:00",
            "open": 1000.0,
            "high": 1012.0,
            "low": 998.0,
            "close": 1011.0,
            "change": 11.0,
            "volume": 1000,
            "source": "twse_realtime",
            "source_priority": "realtime_primary",
            "is_realtime": True,
            "market_state": "trading",
            "delay_seconds": 0,
            "is_fallback": False,
            "note": "",
        }
        result = fetch_quote_from_provider_chain(symbol="2330", finmind_token="token", timeout_seconds=5)
        self.assertEqual(result["source"], "twse_realtime")
        mock_finmind.assert_not_called()
        mock_twse_daily.assert_not_called()

    @patch("backend.app.stocks.quote_provider._fetch_twse_daily_quote")
    @patch("backend.app.stocks.quote_provider._fetch_finmind_daily_quote")
    @patch("backend.app.stocks.quote_provider._fetch_twse_realtime_quote", return_value=None)
    def test_chain_fallbacks_to_finmind(self, _mock_realtime, mock_finmind, mock_twse_daily):
        mock_finmind.return_value = {
            "symbol": "2330",
            "name": "2330",
            "as_of_date": "2026-03-02",
            "quote_time": "2026-03-02 14:00:00",
            "open": 1000.0,
            "high": 1012.0,
            "low": 998.0,
            "close": 1011.0,
            "change": 11.0,
            "volume": 1000,
            "source": "finmind",
            "source_priority": "daily_fallback",
            "is_realtime": False,
            "market_state": "daily_close",
            "delay_seconds": None,
            "is_fallback": False,
            "note": "",
        }
        result = fetch_quote_from_provider_chain(symbol="2330", finmind_token="token", timeout_seconds=5)
        self.assertEqual(result["source"], "finmind")
        mock_twse_daily.assert_not_called()

    @patch("backend.app.stocks.quote_provider._fetch_twse_daily_quote", side_effect=RuntimeError("twse daily err"))
    @patch("backend.app.stocks.quote_provider._fetch_finmind_daily_quote", side_effect=RuntimeError("finmind err"))
    @patch("backend.app.stocks.quote_provider._fetch_twse_realtime_quote", side_effect=RuntimeError("twse realtime err"))
    def test_chain_raises_when_all_providers_fail(self, _mock_realtime, _mock_finmind, _mock_twse_daily):
        with self.assertRaises(QuoteProviderUnavailableError):
            fetch_quote_from_provider_chain(symbol="2330", finmind_token="token", timeout_seconds=5)

    @patch("backend.app.stocks.quote_provider._fetch_finmind_daily_quote")
    @patch("backend.app.stocks.quote_provider._fetch_twse_daily_quote", side_effect=RuntimeError("twse daily err"))
    @patch("backend.app.stocks.quote_provider._fetch_twse_realtime_quote", side_effect=RuntimeError("twse realtime err"))
    def test_chain_raises_when_twse_fail_and_finmind_not_configured(
        self,
        _mock_realtime,
        _mock_twse_daily,
        mock_finmind,
    ):
        with self.assertRaises(QuoteProviderUnavailableError):
            fetch_quote_from_provider_chain(symbol="2330", finmind_token="", timeout_seconds=5)
        mock_finmind.assert_not_called()


if __name__ == "__main__":
    unittest.main()
