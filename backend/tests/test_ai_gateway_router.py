import asyncio
import json
import unittest

from backend.modules.ai_gateway.gateway_router import GatewayRequest, GatewayRouter, build_default_router
from backend.modules.ai_gateway.provider_client import ProviderCallError


class _ErrorClient:
    provider = "broken"

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        raise RuntimeError("provider failure")


class _FlakyClient:
    provider = "flaky"

    def __init__(self, fail_times: int):
        self.fail_times = fail_times
        self.calls = 0

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ProviderCallError("temporary timeout", retryable=True)
        return json.dumps(
            {
                "summary": f"Recovered for {symbol}",
                "signal": "neutral",
                "confidence": 0.61,
            }
        )


class _FirstFailThenSuccessClient:
    provider = "p1"

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        raise ProviderCallError("provider A timeout", retryable=True)


class _SuccessClient:
    provider = "p2"

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        return json.dumps(
            {
                "summary": f"Fallback success for {symbol}",
                "signal": "bullish",
                "confidence": 0.72,
            }
        )


class AIGatewayRouterAsyncTest(unittest.TestCase):
    def test_run_with_default_router(self):
        router = build_default_router(
            claude_api_key="",
            claude_model="claude-opus-4-6",
            openai_api_key="",
            gpt_model="gpt-5.2",
            grok_api_key="",
            grok_model="grok-4.1-fast",
            gemini_api_key="",
            gemini_model="gemini-3.1-pro-preview",
        )
        request = GatewayRequest(
            symbol="2330",
            prompt="test prompt",
            providers=["claude", "gpt5"],
            timeout_seconds=10,
        )
        result = asyncio.run(router.run(request))
        self.assertEqual(len(result["results"]), 2)
        self.assertTrue(all(item["ok"] for item in result["results"]))
        self.assertIn("consensus", result)
        self.assertIn("signal", result["consensus"])
        self.assertFalse(result["fallback_used"])

    def test_run_handles_unknown_provider(self):
        router = build_default_router(
            claude_api_key="",
            claude_model="claude-opus-4-6",
            openai_api_key="",
            gpt_model="gpt-5.2",
            grok_api_key="",
            grok_model="grok-4.1-fast",
            gemini_api_key="",
            gemini_model="gemini-3.1-pro-preview",
        )
        request = GatewayRequest(
            symbol="2330",
            prompt="test prompt",
            providers=["unknown-provider"],
            timeout_seconds=10,
        )
        result = asyncio.run(router.run(request))
        self.assertEqual(len(result["results"]), 1)
        self.assertFalse(result["results"][0]["ok"])
        self.assertEqual(result["consensus"]["confidence"], 0.0)

    def test_run_handles_provider_exception(self):
        router = GatewayRouter(clients={"broken": _ErrorClient()})
        request = GatewayRequest(
            symbol="2330",
            prompt="test prompt",
            providers=["broken"],
            timeout_seconds=10,
        )
        result = asyncio.run(router.run(request))
        self.assertFalse(result["results"][0]["ok"])
        self.assertIn("provider failure", result["results"][0]["error"])

    def test_run_retries_retryable_error_and_then_succeeds(self):
        flaky = _FlakyClient(fail_times=1)
        router = GatewayRouter(clients={"flaky": flaky})
        request = GatewayRequest(
            symbol="2330",
            prompt="test prompt",
            providers=["flaky"],
            timeout_seconds=10,
            retry_count=2,
            retry_backoff_seconds=0.001,
        )
        result = asyncio.run(router.run(request))
        self.assertTrue(result["results"][0]["ok"])
        self.assertEqual(result["results"][0]["attempts"], 2)

    def test_run_uses_fallback_when_first_provider_fails(self):
        router = GatewayRouter(
            clients={
                "p1": _FirstFailThenSuccessClient(),
                "p2": _SuccessClient(),
            }
        )
        request = GatewayRequest(
            symbol="2330",
            prompt="test prompt",
            providers=["p1", "p2"],
            timeout_seconds=10,
            retry_count=0,
        )
        result = asyncio.run(router.run(request))
        self.assertFalse(result["results"][0]["ok"])
        self.assertTrue(result["results"][1]["ok"])
        self.assertTrue(result["fallback_used"])


if __name__ == "__main__":
    unittest.main()
