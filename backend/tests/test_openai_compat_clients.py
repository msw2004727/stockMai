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
        response = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("summary", response.text)
        call = mock_post_json.call_args.kwargs
        self.assertTrue(call["url"].endswith("/responses"))
        self.assertEqual(call["payload"]["max_output_tokens"], 500)
        self.assertEqual(call["payload"]["input"], "prompt")

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
        response = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("bullish", response.text)

    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_grok_client_fallbacks_when_max_tokens_unsupported(self, mock_post_json):
        mock_post_json.side_effect = [
            (
                400,
                {},
                '{"error":{"message":"Unsupported parameter: max_tokens is not supported with this model"}}',
            ),
            (
                400,
                {},
                '{"error":{"message":"Unsupported parameter: max_tokens is not supported with this model"}}',
            ),
            (
                200,
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"summary":"ok fallback","signal":"neutral","confidence":0.6}'
                            }
                        }
                    ]
                },
                "",
            ),
        ]
        client = GrokClient(api_key="k-grok", model="grok-4.1-fast")
        response = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("ok fallback", response.text)
        self.assertEqual(mock_post_json.call_count, 3)
        third_payload = mock_post_json.call_args_list[2].kwargs["payload"]
        self.assertIn("max_completion_tokens", third_payload)

    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_grok_client_fallbacks_when_model_not_found(self, mock_post_json):
        mock_post_json.side_effect = [
            (
                400,
                {},
                '{"code":"Client specified an invalid argument","error":"Model not found: grok-4.1-fast"}',
            ),
            (
                400,
                {},
                '{"code":"Client specified an invalid argument","error":"Model not found: grok-4-1-fast"}',
            ),
            (
                200,
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"summary":"ok model fallback","signal":"neutral","confidence":0.6}'
                            }
                        }
                    ]
                },
                "",
            ),
        ]
        client = GrokClient(api_key="k-grok", model="grok-4.1-fast")
        response = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("model fallback", response.text)
        self.assertEqual(mock_post_json.call_count, 3)
        first_payload = mock_post_json.call_args_list[0].kwargs["payload"]
        second_payload = mock_post_json.call_args_list[1].kwargs["payload"]
        third_payload = mock_post_json.call_args_list[2].kwargs["payload"]
        self.assertEqual(first_payload["model"], "grok-4.1-fast")
        self.assertEqual(second_payload["model"], "grok-4-1-fast")
        self.assertEqual(third_payload["model"], "grok-4-1-fast-non-reasoning")

    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_openai_client_supports_output_text_shape(self, mock_post_json):
        mock_post_json.return_value = (
            200,
            {
                "id": "resp_123",
                "output_text": '{"summary":"ok from output_text","signal":"neutral","confidence":0.6}',
            },
            "",
        )
        client = OpenAIClient(api_key="k-openai", model="gpt-5.2")
        response = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("output_text", response.text)

    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_openai_client_supports_output_content_shape(self, mock_post_json):
        mock_post_json.return_value = (
            200,
            {
                "id": "resp_456",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"summary":"ok from output content","signal":"neutral","confidence":0.6}',
                            }
                        ],
                    }
                ],
            },
            "",
        )
        client = OpenAIClient(api_key="k-openai", model="gpt-5.2")
        response = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("output content", response.text)

    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_openai_client_supports_reasoning_content_shape(self, mock_post_json):
        mock_post_json.return_value = (
            200,
            {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "reasoning_content": '{"summary":"from reasoning","signal":"neutral","confidence":0.6}',
                        }
                    }
                ]
            },
            "",
        )
        client = OpenAIClient(api_key="k-openai", model="gpt-5.2")
        response = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("from reasoning", response.text)

    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_openai_client_falls_back_to_chat_completions_when_responses_empty(self, mock_post_json):
        mock_post_json.side_effect = [
            (200, {"id": "resp_789", "output": []}, ""),
            (
                200,
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"summary":"from fallback","signal":"neutral","confidence":0.6}'
                            }
                        }
                    ]
                },
                "",
            ),
        ]
        client = OpenAIClient(api_key="k-openai", model="gpt-5.2")
        response = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertIn("from fallback", response.text)
        self.assertEqual(mock_post_json.call_count, 2)

        first_call = mock_post_json.call_args_list[0].kwargs
        second_call = mock_post_json.call_args_list[1].kwargs
        self.assertTrue(first_call["url"].endswith("/responses"))
        self.assertEqual(first_call["payload"]["input"], "prompt")
        self.assertTrue(second_call["url"].endswith("/chat/completions"))
        self.assertEqual(second_call["payload"]["max_completion_tokens"], 500)

    @patch("backend.modules.ai_gateway.openai_client.OpenAICompatClient.post_json")
    def test_openai_client_extracts_usage_tokens(self, mock_post_json):
        mock_post_json.return_value = (
            200,
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"summary":"ok","signal":"neutral","confidence":0.6}'
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 45,
                    "total_tokens": 165,
                },
            },
            "",
        )
        client = OpenAIClient(api_key="k-openai", model="gpt-5.2")
        response = asyncio.run(client.generate("prompt", "2330", timeout_seconds=5))
        self.assertEqual(response.usage.input_tokens, 120)
        self.assertEqual(response.usage.output_tokens, 45)
        self.assertEqual(response.usage.total_tokens, 165)

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

