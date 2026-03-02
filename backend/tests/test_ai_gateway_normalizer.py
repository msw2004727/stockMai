import unittest

from backend.modules.ai_gateway.response_normalizer import normalize_ai_response


class AIGatewayNormalizerTest(unittest.TestCase):
    def test_normalize_plain_json(self):
        raw = '{"summary":"Uptrend","signal":"bullish","confidence":0.82,"key_points":["a","b"]}'
        result = normalize_ai_response("gpt5", raw)
        self.assertEqual(result["signal"], "bullish")
        self.assertEqual(result["confidence"], 0.82)
        self.assertEqual(result["normalized_by"], "plain_json")
        self.assertEqual(len(result["key_points"]), 2)

    def test_normalize_markdown_json_fence(self):
        raw = '```json\n{"summary":"Range","signal":"neutral","confidence":0.5}\n```'
        result = normalize_ai_response("claude", raw)
        self.assertEqual(result["signal"], "neutral")
        self.assertEqual(result["normalized_by"], "markdown_fence")

    def test_normalize_embedded_json(self):
        raw = 'analysis start {"summary":"Weak","signal":"bearish","confidence":0.33} end'
        result = normalize_ai_response("grok", raw)
        self.assertEqual(result["signal"], "bearish")
        self.assertEqual(result["normalized_by"], "embedded_json")

    def test_normalize_fallback_text(self):
        raw = "not a json payload"
        result = normalize_ai_response("gemini", raw)
        self.assertEqual(result["signal"], "neutral")
        self.assertEqual(result["confidence"], 0.5)
        self.assertEqual(result["normalized_by"], "fallback_text")


if __name__ == "__main__":
    unittest.main()

