from __future__ import annotations

from typing import Any

from .base_http_client import AsyncJsonHttpClient
from .provider_client import ProviderCallError


class OpenAICompatClient(AsyncJsonHttpClient):
    provider = "openai"

    def __init__(self, provider: str, api_key: str, model: str, base_url: str):
        self.provider = provider
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.base_url = base_url.rstrip("/")

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        if not self.api_key:
            raise ProviderCallError(f"{self.provider} API key is missing.", retryable=False)
        if not self.model:
            raise ProviderCallError(f"{self.provider} model is missing.", retryable=False)

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 500,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        status_code, data, raw_text = await self.post_json(
            url=f"{self.base_url}/chat/completions",
            payload=payload,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

        if status_code >= 500:
            raise ProviderCallError(
                f"{self.provider} server error: HTTP {status_code}",
                retryable=True,
            )
        if status_code >= 400:
            detail = f" ({raw_text[:200]})" if raw_text else ""
            raise ProviderCallError(
                f"{self.provider} request rejected: HTTP {status_code}{detail}",
                retryable=False,
            )

        text = _extract_openai_text(data)
        if not text:
            raise ProviderCallError(
                f"{self.provider} response missing message content.",
                retryable=True,
            )
        return text


class OpenAIClient(OpenAICompatClient):
    def __init__(self, api_key: str, model: str):
        super().__init__(
            provider="gpt5",
            api_key=api_key,
            model=model,
            base_url="https://api.openai.com/v1",
        )


def _extract_openai_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""

    message = choices[0].get("message")
    if not isinstance(message, dict):
        return ""

    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"].strip())
        return "\n".join(part for part in parts if part).strip()
    return ""
