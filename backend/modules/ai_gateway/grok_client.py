from __future__ import annotations

from .openai_client import OpenAICompatClient


class GrokClient(OpenAICompatClient):
    def __init__(self, api_key: str, model: str):
        super().__init__(
            provider="grok",
            api_key=api_key,
            model=model,
            base_url="https://api.x.ai/v1",
        )

