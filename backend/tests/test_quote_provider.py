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
                    "n": "TSMC",
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

    def test_parse_twse_realtime_payload_uses_order_book_when_last_trade_missing(self):
        payload = {
            "msgArray": [
                {
                    "c": "3231",
                    "n": "Wistron",
                    "z": "-",
                    "o": "132.0",
                    "h": "133.0",
                    "l": "130.5",
                    "y": "135.0",
                    "v": "8200",
                    "d": "20260303",
                    "t": "12:58:31",
                    "b": "131.5_131.0_130.5",
                    "a": "132.0_132.5_133.0",
                }
            ]
        }
        result = _parse_twse_realtime_payload(payload=payload, symbol="3231")
        self.assertIsNotNone(result)
        self.assertEqual(result["symbol"], "3231")
        self.assertEqual(result["close"], 131.75)
        self.assertTrue(result["is_realtime"])
        self.assertIn("book_mid", result["note"])

    def test_parse_twse_realtime_payload_marks_prev_close_fallback_as_non_realtime(self):
        payload = {
            "msgArray": [
                {
                    "c": "3231",
                    "n": "Wistron",
                    "z": "-",
                    "o": "-",
                    "h": "-",
                    "l": "-",
                    "y": "135.0",
                    "v": "-",
                    "d": "20260303",
                    "t": "12:59:01",
                    "b": "-",
                    "a": "-",
                }
            ]
        }
        result = _parse_twse_realtime_payload(payload=payload, symbol="3231")
        self.assertIsNotNone(result)
        self.assertEqual(result["close"], 135.0)
        self.assertFalse(result["is_realtime"])
        self.assertIn("prev_close", result["note"])

    def test_parse_twse_realtime_payload_treats_zero_last_trade_as_invalid(self):
        payload = {
            "msgArray": [
                {
                    "c": "3231",
                    "n": "Wistron",
                    "z": "0",
                    "o": "132.0",
                    "h": "133.0",
                    "l": "130.5",
                    "y": "135.0",
                    "v": "8200",
                    "d": "20260303",
                    "t": "12:58:31",
                    "b": "131.5_131.0_130.5",
                    "a": "132.0_132.5_133.0",
                }
            ]
        }
        result = _parse_twse_realtime_payload(payload=payload, symbol="3231")
        self.assertIsNotNone(result)
        self.assertEqual(result["close"], 131.75)
        self.assertTrue(result["is_realtime"])
        self.assertIn("book_mid", result["note"])

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
