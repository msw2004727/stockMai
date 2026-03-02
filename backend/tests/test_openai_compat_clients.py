import asyncio
import unittest
from unittest.mock import patch

from backend.modules.ai_gateway.grok_client import GrokClient
from backend.modules.ai_gateway.openai_client import OpenAIClient
from backend.modules.ai_gateway.provider_client import ProviderCallError


class OpenAICompatClientsTest(unittest.TestCase):
    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_openai_client_success(self, mock_post_json):
        mock_post_json.return_value = (
            200,
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"summary":"ok","signal":"neutral","confidence":0.6}'
                        }
                    }
                ]
            },
            "",
        )
        client = OpenAIClient(api_key="k-openai", model="gpt-5.2")
        text = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("summary", text)

    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_grok_client_success(self, mock_post_json):
        mock_post_json.return_value = (
            200,
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"summary":"ok","signal":"bullish","confidence":0.7}'
                        }
                    }
                ]
            },
            "",
        )
        client = GrokClient(api_key="k-grok", model="grok-4.1-fast")
        text = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("bullish", text)

    def test_openai_client_rejects_missing_key(self):
        client = OpenAIClient(api_key="", model="gpt-5.2")
        with self.assertRaises(ProviderCallError) as ctx:
            asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertFalse(ctx.exception.retryable)

    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_openai_client_handles_4xx_non_retryable(self, mock_post_json):
        mock_post_json.return_value = (401, {}, "Unauthorized")
        client = OpenAIClient(api_key="k-openai", model="gpt-5.2")
        with self.assertRaises(ProviderCallError) as ctx:
            asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertFalse(ctx.exception.retryable)


if __name__ == "__main__":
    unittest.main()

