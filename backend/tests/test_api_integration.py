import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.main import app


class _FakeRedis:
    def __init__(self):
        self.store = {}

    def incr(self, key: str) -> int:
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, _key: str, _ttl: int) -> bool:
        return True


def _settings(**overrides):
    base = {
        "jwt_secret": "integration-secret",
        "jwt_expire_minutes": 60,
        "api_daily_limit": 2,
        "redis_url": "redis://localhost:6379/0",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


async def _asgi_request(
    method: str,
    path: str,
    query: str = "",
    headers: dict[str, str] | None = None,
    body: bytes = b"",
) -> tuple[int, dict[str, str], bytes]:
    response_start = None
    response_body = []
    request_sent = False

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": query.encode("ascii"),
        "headers": [(b"host", b"testserver")]
        + [
            (k.lower().encode("ascii"), v.encode("utf-8"))
            for k, v in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }

    async def receive():
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}
        request_sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        nonlocal response_start
        if message["type"] == "http.response.start":
            response_start = message
        elif message["type"] == "http.response.body":
            response_body.append(message.get("body", b""))

    await app(scope, receive, send)
    assert response_start is not None

    headers_dict = {
        k.decode("latin-1"): v.decode("latin-1")
        for k, v in response_start.get("headers", [])
    }
    return response_start["status"], headers_dict, b"".join(response_body)


class ApiIntegrationTest(unittest.TestCase):
    def _request_json(
        self,
        method: str,
        path: str,
        query: str = "",
        headers: dict[str, str] | None = None,
        payload: dict | None = None,
    ) -> tuple[int, dict]:
        request_headers = dict(headers or {})
        raw_body = b""
        if payload is not None:
            raw_body = json.dumps(payload).encode("utf-8")
            request_headers["content-type"] = "application/json"
            request_headers["content-length"] = str(len(raw_body))

        status, _resp_headers, body = asyncio.run(
            _asgi_request(
                method=method,
                path=path,
                query=query,
                headers=request_headers,
                body=raw_body,
            )
        )
        parsed = json.loads(body.decode("utf-8")) if body else {}
        return status, parsed

    def test_stocks_quote_requires_token(self):
        status, payload = self._request_json("GET", "/stocks/quote", query="symbol=2330")
        self.assertEqual(status, 401)
        self.assertEqual(payload["detail"], "Missing bearer token")

    def test_issue_token_and_access_quote_success(self):
        fake_redis = _FakeRedis()
        fake_quote = {
            "symbol": "2330",
            "name": "TSMC",
            "as_of_date": "2026-03-02",
            "open": 1000.0,
            "high": 1012.0,
            "low": 995.0,
            "close": 1008.0,
            "change": 8.0,
            "volume": 1234567,
            "source": "integration",
            "is_fallback": False,
            "note": "",
        }
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch("backend.app.stocks.routes.get_quote", return_value=fake_quote):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "integration-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    quote_status, quote_payload = self._request_json(
                        "GET",
                        "/stocks/quote",
                        query="symbol=2330",
                        headers={"authorization": f"Bearer {token}"},
                    )
                    self.assertEqual(quote_status, 200)
                    self.assertEqual(quote_payload["symbol"], "2330")
                    self.assertEqual(quote_payload["source"], "integration")

    def test_quote_returns_429_when_daily_limit_exceeded(self):
        fake_redis = _FakeRedis()
        fake_quote = {
            "symbol": "2330",
            "name": "TSMC",
            "as_of_date": "2026-03-02",
            "open": 1000.0,
            "high": 1012.0,
            "low": 995.0,
            "close": 1008.0,
            "change": 8.0,
            "volume": 1234567,
            "source": "integration",
            "is_fallback": False,
            "note": "",
        }
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=1)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch("backend.app.stocks.routes.get_quote", return_value=fake_quote):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "quota-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]
                    headers = {"authorization": f"Bearer {token}"}

                    first_status, _first_payload = self._request_json(
                        "GET",
                        "/stocks/quote",
                        query="symbol=2330",
                        headers=headers,
                    )
                    second_status, second_payload = self._request_json(
                        "GET",
                        "/stocks/quote",
                        query="symbol=2330",
                        headers=headers,
                    )

                    self.assertEqual(first_status, 200)
                    self.assertEqual(second_status, 429)
                    self.assertEqual(second_payload["detail"], "Daily quota exceeded")

    def test_stocks_indicators_requires_token(self):
        status, payload = self._request_json("GET", "/stocks/indicators", query="symbol=2330&days=60")
        self.assertEqual(status, 401)
        self.assertEqual(payload["detail"], "Missing bearer token")

    def test_stocks_indicators_success_with_token(self):
        fake_redis = _FakeRedis()
        fake_indicators = {
            "symbol": "2330",
            "days": 60,
            "as_of_date": "2026-03-02",
            "history_source": "integration",
            "is_fallback": False,
            "note": "",
            "latest": {
                "sma5": 1010.1,
                "sma20": 1002.5,
                "rsi14": 56.2,
                "macd": 1.2,
                "macd_signal": 1.0,
                "macd_hist": 0.2,
            },
            "series": [],
        }
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch("backend.app.stocks.routes.get_indicators", return_value=fake_indicators):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "indicators-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "GET",
                        "/stocks/indicators",
                        query="symbol=2330&days=60",
                        headers={"authorization": f"Bearer {token}"},
                    )
                    self.assertEqual(status, 200)
                    self.assertEqual(payload["symbol"], "2330")
                    self.assertIn("latest", payload)
                    self.assertEqual(payload["history_source"], "integration")

    def test_ai_analyze_requires_token(self):
        status, payload = self._request_json(
            "POST",
            "/ai/analyze",
            payload={"symbol": "2330", "user_prompt": "short term view"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["detail"], "Missing bearer token")

    def test_ai_analyze_success_with_token(self):
        fake_redis = _FakeRedis()
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                token_status, token_payload = self._request_json(
                    "POST",
                    "/auth/token",
                    payload={"user_id": "ai-user", "expires_minutes": 30},
                )
                self.assertEqual(token_status, 200)
                token = token_payload["access_token"]

                analyze_status, analyze_payload = self._request_json(
                    "POST",
                    "/ai/analyze",
                    headers={"authorization": f"Bearer {token}"},
                    payload={"symbol": "2330", "user_prompt": "focus on momentum"},
                )
                self.assertEqual(analyze_status, 200)
                self.assertEqual(analyze_payload["symbol"], "2330")
                self.assertGreaterEqual(len(analyze_payload["results"]), 1)
                self.assertIn("signal", analyze_payload["consensus"])
                self.assertIn("cost", analyze_payload)
                self.assertIn("indicator_context", analyze_payload)
                self.assertIn("provider_prompts", analyze_payload)

    def test_ai_analyze_returns_429_when_daily_limit_exceeded(self):
        fake_redis = _FakeRedis()
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=1)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                token_status, token_payload = self._request_json(
                    "POST",
                    "/auth/token",
                    payload={"user_id": "ai-quota-user", "expires_minutes": 30},
                )
                self.assertEqual(token_status, 200)
                token = token_payload["access_token"]
                headers = {"authorization": f"Bearer {token}"}

                first_status, _first_payload = self._request_json(
                    "POST",
                    "/ai/analyze",
                    headers=headers,
                    payload={"symbol": "2330"},
                )
                second_status, second_payload = self._request_json(
                    "POST",
                    "/ai/analyze",
                    headers=headers,
                    payload={"symbol": "2330"},
                )
                self.assertEqual(first_status, 200)
                self.assertEqual(second_status, 429)
                self.assertEqual(second_payload["detail"], "Daily quota exceeded")


if __name__ == "__main__":
    unittest.main()
