import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.main import app
from backend.app.stocks.service import DataUnavailableError, QuoteRateLimitedError, SymbolNotFoundError
from backend.app.strategy.service import StrategyDataUnavailableError, StrategySymbolNotFoundError


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
        self.assertEqual(payload["error_code"], "auth_missing_bearer_token")

    def test_stocks_search_requires_token(self):
        status, payload = self._request_json("GET", "/stocks/search", query="q=233")
        self.assertEqual(status, 401)
        self.assertEqual(payload["detail"], "Missing bearer token")
        self.assertEqual(payload["error_code"], "auth_missing_bearer_token")

    def test_stocks_search_success_with_token(self):
        fake_redis = _FakeRedis()
        fake_results = [
            {"symbol": "2330", "name": "台積電", "market": "twse"},
            {"symbol": "2337", "name": "旺宏", "market": "twse"},
        ]
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch("backend.app.stocks.routes.search_stock_symbols", return_value=fake_results):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "search-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "GET",
                        "/stocks/search",
                        query="q=233&limit=5",
                        headers={"authorization": f"Bearer {token}"},
                    )
                    self.assertEqual(status, 200)
                    self.assertEqual(payload["query"], "233")
                    self.assertEqual(len(payload["results"]), 2)
                    self.assertEqual(payload["results"][0]["symbol"], "2330")

    def test_stocks_movers_requires_token(self):
        status, payload = self._request_json("GET", "/stocks/movers", query="limit=6")
        self.assertEqual(status, 401)
        self.assertEqual(payload["detail"], "Missing bearer token")
        self.assertEqual(payload["error_code"], "auth_missing_bearer_token")

    def test_stocks_movers_success_with_token(self):
        fake_redis = _FakeRedis()
        fake_payload = {
            "as_of_date": "2026-03-03",
            "limit": 6,
            "source": "postgres",
            "universe_size": 128,
            "is_partial_universe": True,
            "categories": {
                "top_volume": [
                    {
                        "symbol": "2330",
                        "name": "2330",
                        "close": 1008.0,
                        "change": 8.0,
                        "change_pct": 0.8,
                        "volume": 1234567,
                    }
                ],
                "top_gainers": [],
                "top_losers": [],
            },
            "note": "test",
        }
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch("backend.app.stocks.routes.get_market_movers", return_value=fake_payload):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "movers-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "GET",
                        "/stocks/movers",
                        query="limit=6",
                        headers={"authorization": f"Bearer {token}"},
                    )
                    self.assertEqual(status, 200)
                    self.assertEqual(payload["as_of_date"], "2026-03-03")
                    self.assertIn("categories", payload)
                    self.assertIn("top_volume", payload["categories"])

    def test_stocks_pipeline_snapshot_requires_token(self):
        status, payload = self._request_json(
            "POST",
            "/stocks/pipeline/snapshot",
            query="max_symbols=3000",
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["detail"], "Missing bearer token")
        self.assertEqual(payload["error_code"], "auth_missing_bearer_token")

    def test_stocks_pipeline_snapshot_success_with_token(self):
        fake_redis = _FakeRedis()
        fake_result = {
            "ok": True,
            "triggered_at": "2026-03-03T12:00:00+00:00",
            "trade_date": "2026-03-03",
            "source": "twse_openapi_stock_day_all",
            "fetched_rows": 1000,
            "selected_rows": 1000,
            "inserted_rows": 998,
            "max_symbols": 3000,
            "note": "done",
        }
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch("backend.app.stocks.routes.run_market_snapshot", return_value=fake_result):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "pipeline-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "POST",
                        "/stocks/pipeline/snapshot",
                        query="max_symbols=3000",
                        headers={"authorization": f"Bearer {token}"},
                    )
                    self.assertEqual(status, 200)
                    self.assertTrue(payload["ok"])
                    self.assertEqual(payload["source"], "twse_openapi_stock_day_all")
                    self.assertEqual(payload["inserted_rows"], 998)

    def test_stocks_pipeline_status_requires_token(self):
        status, payload = self._request_json(
            "GET",
            "/stocks/pipeline/status",
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["detail"], "Missing bearer token")
        self.assertEqual(payload["error_code"], "auth_missing_bearer_token")

    def test_stocks_pipeline_status_success_with_token(self):
        fake_redis = _FakeRedis()
        fake_result = {
            "status": "ok",
            "is_healthy": True,
            "expected_trade_date": "2026-03-03",
            "latest_trade_date": "2026-03-03",
            "lag_days": 0,
            "row_count": 2100,
            "symbol_count": 2000,
            "expected_universe_size": 2300,
            "coverage_ratio": 0.8696,
            "coverage_warn_threshold": 0.8,
            "source_breakdown": [{"source": "twse_openapi_stock_day_all", "rows": 2100}],
            "note": "ok",
        }
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch("backend.app.stocks.routes.get_pipeline_status", return_value=fake_result):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "pipeline-status-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "GET",
                        "/stocks/pipeline/status",
                        headers={"authorization": f"Bearer {token}"},
                    )
                    self.assertEqual(status, 200)
                    self.assertEqual(payload["status"], "ok")
                    self.assertTrue(payload["is_healthy"])
                    self.assertIn("coverage_ratio", payload)

    def test_stocks_quote_invalid_symbol_returns_422_with_error_code(self):
        fake_redis = _FakeRedis()
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                token_status, token_payload = self._request_json(
                    "POST",
                    "/auth/token",
                    payload={"user_id": "invalid-symbol-user", "expires_minutes": 30},
                )
                self.assertEqual(token_status, 200)
                token = token_payload["access_token"]

                status, payload = self._request_json(
                    "GET",
                    "/stocks/quote",
                    query="symbol=ABC",
                    headers={"authorization": f"Bearer {token}"},
                )
                self.assertEqual(status, 422)
                self.assertEqual(payload["error_code"], "validation_error")
                self.assertEqual(payload["message"], "Invalid request parameters")

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
                    self.assertEqual(second_payload["error_code"], "daily_quota_exceeded")

    def test_quote_supports_five_digit_symbol(self):
        fake_redis = _FakeRedis()
        fake_quote = {
            "symbol": "00878",
            "name": "00878",
            "as_of_date": "2026-03-02",
            "open": 21.4,
            "high": 21.7,
            "low": 21.3,
            "close": 21.6,
            "change": 0.2,
            "volume": 15230000,
            "source": "integration",
            "is_fallback": False,
            "note": "",
            "freshness": {
                "as_of_date": "2026-03-02",
                "age_days": 0,
                "is_fresh": True,
                "max_age_days": 5,
            },
        }
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch("backend.app.stocks.routes.get_quote", return_value=fake_quote):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "five-digit-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "GET",
                        "/stocks/quote",
                        query="symbol=00878",
                        headers={"authorization": f"Bearer {token}"},
                    )
                    self.assertEqual(status, 200)
                    self.assertEqual(payload["symbol"], "00878")

    def test_quote_returns_503_when_market_data_unavailable(self):
        fake_redis = _FakeRedis()
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch(
                    "backend.app.stocks.routes.get_quote",
                    side_effect=DataUnavailableError("Market data providers are temporarily unavailable."),
                ):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "unavailable-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "GET",
                        "/stocks/quote",
                        query="symbol=2330",
                        headers={"authorization": f"Bearer {token}"},
                    )
                    self.assertEqual(status, 503)
                    self.assertEqual(payload["detail"], "Market data providers are temporarily unavailable.")
                    self.assertEqual(payload["error_code"], "service_unavailable")

    def test_quote_returns_429_when_quote_rate_guard_triggers(self):
        fake_redis = _FakeRedis()
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch(
                    "backend.app.stocks.routes.get_quote",
                    side_effect=QuoteRateLimitedError("Quote rate limit exceeded (max 20/10s). Please retry shortly."),
                ):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "quote-guard-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "GET",
                        "/stocks/quote",
                        query="symbol=2330",
                        headers={"authorization": f"Bearer {token}"},
                    )
                    self.assertEqual(status, 429)
                    self.assertIn("Quote rate limit exceeded", payload["detail"])
                    self.assertEqual(payload["error_code"], "rate_limited")

    def test_quote_returns_404_with_standard_error_code(self):
        fake_redis = _FakeRedis()
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch(
                    "backend.app.stocks.routes.get_quote",
                    side_effect=SymbolNotFoundError("Symbol not found: 9999"),
                ):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "not-found-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "GET",
                        "/stocks/quote",
                        query="symbol=9999",
                        headers={"authorization": f"Bearer {token}"},
                    )
                    self.assertEqual(status, 404)
                    self.assertEqual(payload["error_code"], "not_found")

    def test_stocks_indicators_requires_token(self):
        status, payload = self._request_json("GET", "/stocks/indicators", query="symbol=2330&days=60")
        self.assertEqual(status, 401)
        self.assertEqual(payload["detail"], "Missing bearer token")
        self.assertEqual(payload["error_code"], "auth_missing_bearer_token")

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
        self.assertEqual(payload["error_code"], "auth_missing_bearer_token")

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
                self.assertIn("sentiment_context", analyze_payload)
                self.assertIn("provider_prompts", analyze_payload)
                self.assertIn("model_tech_metrics", analyze_payload)

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
                self.assertEqual(second_payload["error_code"], "daily_quota_exceeded")

    def test_strategy_decision_requires_token(self):
        status, payload = self._request_json(
            "POST",
            "/strategy/decision",
            payload={"symbol": "2330"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["detail"], "Missing bearer token")
        self.assertEqual(payload["error_code"], "auth_missing_bearer_token")

    def test_strategy_decision_success_with_token(self):
        fake_redis = _FakeRedis()
        fake_decision = {
            "symbol": "2330",
            "generated_at": "2026-03-02T12:00:00+00:00",
            "history_source": "integration",
            "as_of_date": "2026-03-02",
            "action": "hold",
            "confidence": 0.55,
            "risk_level": "medium",
            "weighted_score": 0.1,
            "reasons": ["測試策略結果"],
            "components": {
                "indicators": {"label": "neutral", "score": 0.0},
                "sentiment": {"label": "neutral", "score": 0.0},
                "ai_consensus": {"label": "neutral", "score": 0.0},
            },
            "indicator_context": {"symbol": "2330", "latest": {}},
            "sentiment_context": {"symbol": "2330", "market_sentiment": "neutral"},
            "ai_consensus": {"signal": "neutral", "confidence": 0.5},
            "ai_fallback_used": False,
            "providers_requested": ["claude"],
            "provider_weights": {"claude": 1.0},
            "ai_results": [],
            "cost": {"enabled": True},
        }
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch("backend.app.strategy.routes.build_strategy_decision", return_value=fake_decision):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "strategy-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "POST",
                        "/strategy/decision",
                        headers={"authorization": f"Bearer {token}"},
                        payload={"symbol": "2330"},
                    )
                    self.assertEqual(status, 200)
                    self.assertEqual(payload["symbol"], "2330")
                    self.assertEqual(payload["action"], "hold")
                    self.assertIn("components", payload)

    def test_strategy_decision_returns_503_when_data_unavailable(self):
        fake_redis = _FakeRedis()
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch(
                    "backend.app.strategy.routes.build_strategy_decision",
                    side_effect=StrategyDataUnavailableError("Market data providers are temporarily unavailable."),
                ):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "strategy-unavailable-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "POST",
                        "/strategy/decision",
                        headers={"authorization": f"Bearer {token}"},
                        payload={"symbol": "2330"},
                    )
                    self.assertEqual(status, 503)
                    self.assertEqual(payload["error_code"], "service_unavailable")

    def test_strategy_decision_returns_404_when_symbol_not_found(self):
        fake_redis = _FakeRedis()
        with patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=5)):
            with patch("backend.app.auth.get_redis_client", return_value=fake_redis):
                with patch(
                    "backend.app.strategy.routes.build_strategy_decision",
                    side_effect=StrategySymbolNotFoundError("No history data found for symbol=9999"),
                ):
                    token_status, token_payload = self._request_json(
                        "POST",
                        "/auth/token",
                        payload={"user_id": "strategy-not-found-user", "expires_minutes": 30},
                    )
                    self.assertEqual(token_status, 200)
                    token = token_payload["access_token"]

                    status, payload = self._request_json(
                        "POST",
                        "/strategy/decision",
                        headers={"authorization": f"Bearer {token}"},
                        payload={"symbol": "9999"},
                    )
                    self.assertEqual(status, 404)
                    self.assertEqual(payload["error_code"], "not_found")


if __name__ == "__main__":
    unittest.main()
