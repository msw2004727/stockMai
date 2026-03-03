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
        result = normalize_ai_response("deepseek", raw)
        self.assertEqual(result["signal"], "neutral")
        self.assertEqual(result["confidence"], 0.5)
        self.assertEqual(result["normalized_by"], "fallback_text")

    def test_normalize_partial_json_extracts_summary_fields(self):
        raw = (
            '{"summary":"資料不足，先觀望","signal":"neutral","confidence":0.22,'
            '"key_points":["資料缺口","等待突破"'
        )
        result = normalize_ai_response("gpt5", raw)
        self.assertEqual(result["summary"], "資料不足，先觀望")
        self.assertEqual(result["signal"], "neutral")
        self.assertEqual(result["confidence"], 0.22)
        self.assertEqual(result["key_points"], ["資料缺口", "等待突破"])
        self.assertEqual(result["normalized_by"], "partial_json")

    def test_normalize_extracts_analyst_narratives(self):
        raw = (
            '{"summary":"中性","signal":"neutral","confidence":0.6,'
            '"bullish_view":"看多觀點內容","bearish_view":"看空觀點內容","easy_summary":"輕鬆總結內容"}'
        )
        result = normalize_ai_response("gpt5", raw)
        self.assertEqual(result["bullish_view"], "看多觀點內容")
        self.assertEqual(result["bearish_view"], "看空觀點內容")
        self.assertEqual(result["easy_summary"], "輕鬆總結內容")

    def test_normalize_fallback_text_includes_empty_narratives(self):
        result = normalize_ai_response("gpt5", "plain response text")
        self.assertEqual(result["bullish_view"], "")
        self.assertEqual(result["bearish_view"], "")
        self.assertEqual(result["easy_summary"], "")


if __name__ == "__main__":
    unittest.main()


