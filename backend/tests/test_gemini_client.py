import asyncio
import unittest
from unittest.mock import patch

from backend.modules.ai_gateway.gemini_client import GeminiClient
from backend.modules.ai_gateway.provider_client import ProviderCallError


class GeminiClientTest(unittest.TestCase):
    @patch("backend.modules.ai_gateway.gemini_client.GeminiClient.post_json")
    def test_generate_success(self, mock_post_json):
        mock_post_json.return_value = (
            200,
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": '{"summary":"ok","signal":"neutral","confidence":0.6}'}
                            ]
                        }
                    }
                ]
            },
            "",
        )
        client = GeminiClient(api_key="k-gemini", model="gemini-3.1-pro-preview")
        result = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("summary", result)

    def test_generate_rejects_missing_api_key(self):
        client = GeminiClient(api_key="", model="gemini-3.1-pro-preview")
        with self.assertRaises(ProviderCallError) as ctx:
            asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertFalse(ctx.exception.retryable)

    @patch("backend.modules.ai_gateway.gemini_client.GeminiClient.post_json")
    def test_generate_handles_4xx_as_non_retryable(self, mock_post_json):
        mock_post_json.return_value = (403, {}, "Forbidden")
        client = GeminiClient(api_key="k-gemini", model="gemini-3.1-pro-preview")
        with self.assertRaises(ProviderCallError) as ctx:
            asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertFalse(ctx.exception.retryable)


if __name__ == "__main__":
    unittest.main()

