import unittest

from backend.modules.ai_gateway.consensus import build_weighted_consensus, parse_provider_weights


class AIConsensusTest(unittest.TestCase):
    def test_parse_provider_weights_ignores_invalid_tokens(self):
        parsed = parse_provider_weights("claude=1.2, GPT5 =2,broken,nope=-1,gemini=abc")
        self.assertEqual(parsed, {"claude": 1.2, "gpt5": 2.0})

    def test_build_weighted_consensus_handles_empty_input(self):
        result = build_weighted_consensus([], {"claude": 1.2})
        self.assertEqual(result["signal"], "neutral")
        self.assertEqual(result["confidence"], 0.0)

    def test_build_weighted_consensus_applies_weights(self):
        successful = [
            {"provider": "claude", "signal": "bullish", "confidence": 0.6, "summary": "claude says up"},
            {"provider": "gpt5", "signal": "bearish", "confidence": 0.8, "summary": "gpt says down"},
        ]
        weights = {"claude": 2.0, "gpt5": 1.0}
        result = build_weighted_consensus(successful, weights)
        self.assertEqual(result["signal"], "bullish")
        self.assertEqual(result["source_provider"], "claude")
        self.assertAlmostEqual(result["confidence"], 0.6, places=4)


if __name__ == "__main__":
    unittest.main()
