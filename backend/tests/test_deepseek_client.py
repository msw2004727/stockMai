import asyncio
import unittest
from unittest.mock import patch

from backend.modules.ai_gateway.deepseek_client import DeepSeekClient
from backend.modules.ai_gateway.provider_client import ProviderCallError


class DeepSeekClientTest(unittest.TestCase):
    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_generate_success(self, mock_post_json):
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
        client = DeepSeekClient(api_key="k-deepseek", model="deepseek-chat")
        response = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("summary", response.text)

    def test_generate_rejects_missing_api_key(self):
        client = DeepSeekClient(api_key="", model="deepseek-chat")
        with self.assertRaises(ProviderCallError) as ctx:
            asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertFalse(ctx.exception.retryable)

    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_generate_handles_4xx_as_non_retryable(self, mock_post_json):
        mock_post_json.return_value = (403, {}, "Forbidden")
        client = DeepSeekClient(api_key="k-deepseek", model="deepseek-chat")
        with self.assertRaises(ProviderCallError) as ctx:
            asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertFalse(ctx.exception.retryable)

    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_generate_retries_without_temperature_when_model_rejects_it(self, mock_post_json):
        mock_post_json.side_effect = [
            (
                400,
                {},
                '{"error":{"message":"Unsupported parameter: temperature is not supported with this model"}}',
            ),
            (
                200,
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"summary":"ok no temp","signal":"neutral","confidence":0.6}'
                            }
                        }
                    ]
                },
                "",
            ),
        ]
        client = DeepSeekClient(api_key="k-deepseek", model="deepseek-reasoner")
        response = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("ok no temp", response.text)
        self.assertEqual(mock_post_json.call_count, 2)
        first_payload = mock_post_json.call_args_list[0].kwargs["payload"]
        second_payload = mock_post_json.call_args_list[1].kwargs["payload"]
        self.assertIn("temperature", first_payload)
        self.assertNotIn("temperature", second_payload)


if __name__ == "__main__":
    unittest.main()
