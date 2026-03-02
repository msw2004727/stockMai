import asyncio
import json
import unittest

from backend.modules.ai_gateway.cost_tracker import CostTracker
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


class _StaticResponseClient:
    def __init__(self, provider: str, signal: str, confidence: float):
        self.provider = provider
        self.signal = signal
        self.confidence = confidence

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        return json.dumps(
            {
                "summary": f"{self.provider} view for {symbol}",
                "signal": self.signal,
                "confidence": self.confidence,
            }
        )


class _CapturePromptClient:
    def __init__(self, provider: str):
        self.provider = provider
        self.last_prompt = ""

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        self.last_prompt = prompt
        return json.dumps(
            {
                "summary": f"{self.provider} captured prompt for {symbol}",
                "signal": "neutral",
                "confidence": 0.5,
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
            deepseek_api_key="",
            deepseek_model="deepseek-chat",
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
        self.assertIn("cost", result)

    def test_run_handles_unknown_provider(self):
        router = build_default_router(
            claude_api_key="",
            claude_model="claude-opus-4-6",
            openai_api_key="",
            gpt_model="gpt-5.2",
            grok_api_key="",
            grok_model="grok-4.1-fast",
            deepseek_api_key="",
            deepseek_model="deepseek-chat",
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

    def test_run_weighted_consensus_prefers_high_weight_provider(self):
        router = GatewayRouter(
            clients={
                "p1": _StaticResponseClient(provider="p1", signal="bullish", confidence=0.7),
                "p2": _StaticResponseClient(provider="p2", signal="bearish", confidence=0.9),
            }
        )
        request = GatewayRequest(
            symbol="2330",
            prompt="test prompt",
            providers=["p1", "p2"],
            provider_weights={"p1": 2.0, "p2": 1.0},
            timeout_seconds=10,
            retry_count=0,
        )
        result = asyncio.run(router.run(request))
        self.assertEqual(result["consensus"]["signal"], "bullish")
        self.assertEqual(result["consensus"]["source_provider"], "p1")
        self.assertAlmostEqual(result["consensus"]["confidence"], 0.6087, places=4)

    def test_run_tracks_cost_when_cost_tracker_enabled(self):
        cost_tracker = CostTracker(redis_url="")
        router = GatewayRouter(clients={"p1": _StaticResponseClient(provider="p1", signal="neutral", confidence=0.6)})
        request = GatewayRequest(
            symbol="2330",
            prompt="test prompt",
            providers=["p1"],
            timeout_seconds=10,
            retry_count=0,
            user_id="cost-user",
            daily_budget_usd=1.0,
            cost_tracker=cost_tracker,
        )
        result = asyncio.run(router.run(request))
        self.assertTrue(result["results"][0]["ok"])
        self.assertTrue(result["cost"]["enabled"])
        self.assertEqual(len(result["cost"]["entries"]), 1)
        self.assertGreater(result["cost"]["total_request_cost_usd"], 0)
        self.assertIn("cost", result["results"][0])

    def test_run_blocks_when_budget_already_exceeded(self):
        cost_tracker = CostTracker(redis_url="")
        cost_tracker.record_usage(
            user_id="budget-user",
            provider="claude",
            input_tokens=1_000_000,
            output_tokens=0,
            daily_budget_usd=1.0,
        )

        router = GatewayRouter(clients={"claude": _StaticResponseClient(provider="claude", signal="neutral", confidence=0.5)})
        request = GatewayRequest(
            symbol="2330",
            prompt="test prompt",
            providers=["claude"],
            timeout_seconds=10,
            retry_count=0,
            user_id="budget-user",
            daily_budget_usd=0.5,
            cost_tracker=cost_tracker,
        )
        result = asyncio.run(router.run(request))
        self.assertFalse(result["results"][0]["ok"])
        self.assertEqual(result["results"][0]["error_type"], "budget")
        self.assertTrue(result["cost"]["budget_exceeded"])
        self.assertEqual(len(result["cost"]["entries"]), 0)

    def test_run_uses_provider_specific_prompts(self):
        c1 = _CapturePromptClient(provider="claude")
        c2 = _CapturePromptClient(provider="gpt5")
        router = GatewayRouter(
            clients={
                "claude": c1,
                "gpt5": c2,
            }
        )
        request = GatewayRequest(
            symbol="2330",
            prompt="base prompt",
            providers=["claude", "gpt5"],
            provider_prompts={
                "claude": "claude prompt",
                "gpt5": "gpt prompt",
            },
            timeout_seconds=10,
            retry_count=0,
        )

        result = asyncio.run(router.run(request))

        self.assertTrue(result["results"][0]["ok"])
        self.assertTrue(result["results"][1]["ok"])
        self.assertEqual(c1.last_prompt, "claude prompt")
        self.assertEqual(c2.last_prompt, "gpt prompt")


if __name__ == "__main__":
    unittest.main()

