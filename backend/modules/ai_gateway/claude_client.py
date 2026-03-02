from __future__ import annotations

from typing import Any

from .base_http_client import AsyncJsonHttpClient
from .provider_client import ProviderCallError


class ClaudeClient(AsyncJsonHttpClient):
    provider = "claude"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key.strip()
        self.model = model.strip() or "claude-opus-4-6"
        self.endpoint = "https://api.anthropic.com/v1/messages"

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        if not self.api_key:
            raise ProviderCallError("Claude API key is missing.", retryable=False)

        payload = {
            "model": self.model,
            "max_tokens": 500,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        status_code, data, raw_text = await self.post_json(
            url=self.endpoint,
            payload=payload,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

        if status_code >= 500:
            raise ProviderCallError(
                f"Claude server error: HTTP {status_code}",
                retryable=True,
            )
        if status_code >= 400:
            detail = f" ({raw_text[:200]})" if raw_text else ""
            raise ProviderCallError(
                f"Claude request rejected: HTTP {status_code}{detail}",
                retryable=False,
            )

        text = _extract_text(data)
        if not text:
            raise ProviderCallError("Claude response missing text content.", retryable=True)
        return text


def _extract_text(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
            parts.append(item["text"].strip())
    return "\n".join(part for part in parts if part).strip()
