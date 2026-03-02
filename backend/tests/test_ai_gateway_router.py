import unittest

from backend.modules.ai_gateway.gateway_router import GatewayRequest, GatewayRouter, build_default_router


class _ErrorClient:
    provider = "broken"

    def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        raise RuntimeError("provider failure")


class AIGatewayRouterTest(unittest.TestCase):
    def test_run_with_default_router(self):
        router = build_default_router()
        request = GatewayRequest(
            symbol="2330",
            prompt="test prompt",
            providers=["claude", "gpt5"],
            timeout_seconds=10,
        )
        result = router.run(request)
        self.assertEqual(len(result["results"]), 2)
        self.assertTrue(all(item["ok"] for item in result["results"]))
        self.assertIn("consensus", result)
        self.assertIn("signal", result["consensus"])

    def test_run_handles_unknown_provider(self):
        router = build_default_router()
        request = GatewayRequest(
            symbol="2330",
            prompt="test prompt",
            providers=["unknown-provider"],
            timeout_seconds=10,
        )
        result = router.run(request)
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
        result = router.run(request)
        self.assertFalse(result["results"][0]["ok"])
        self.assertIn("provider failure", result["results"][0]["error"])


if __name__ == "__main__":
    unittest.main()

