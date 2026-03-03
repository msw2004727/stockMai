from __future__ import annotations

from .openai_client import OpenAICompatClient


class DeepSeekClient(OpenAICompatClient):
    def __init__(self, api_key: str, model: str):
        super().__init__(
            provider="deepseek",
            api_key=api_key,
            model=model,
            base_url="https://api.deepseek.com",
        )
