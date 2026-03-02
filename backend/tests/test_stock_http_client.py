import io
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from backend.app.stocks.http_client import fetch_json


def _response_with_json(payload: str):
    cm = MagicMock()
    cm.__enter__.return_value = io.StringIO(payload)
    cm.__exit__.return_value = False
    return cm


class StockHttpClientTest(unittest.TestCase):
    @patch("backend.app.stocks.http_client.urlopen")
    def test_fetch_json_success(self, mock_urlopen):
        mock_urlopen.return_value = _response_with_json('{"ok": true}')
        result = fetch_json("https://example.com/data", timeout=3)
        self.assertEqual(result, {"ok": True})
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("backend.app.stocks.http_client.urlopen")
    def test_fetch_json_tls_fallback_on_cert_error(self, mock_urlopen):
        cert_err = URLError("[SSL: CERTIFICATE_VERIFY_FAILED] Missing Subject Key Identifier")
        mock_urlopen.side_effect = [
            cert_err,
            _response_with_json('{"status": "ok"}'),
        ]
        result = fetch_json(
            "https://example.com/data",
            timeout=3,
            allow_insecure_tls_fallback=True,
        )
        self.assertEqual(result, {"status": "ok"})
        self.assertEqual(mock_urlopen.call_count, 2)
        self.assertIn("context", mock_urlopen.call_args_list[1].kwargs)

    @patch("backend.app.stocks.http_client.urlopen")
    def test_fetch_json_does_not_fallback_when_disabled(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("[SSL: CERTIFICATE_VERIFY_FAILED] Missing Subject Key Identifier")
        with self.assertRaises(URLError):
            fetch_json("https://example.com/data", timeout=3, allow_insecure_tls_fallback=False)


if __name__ == "__main__":
    unittest.main()
