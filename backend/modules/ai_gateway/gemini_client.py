from __future__ import annotations

from typing import Any

from .base_http_client import AsyncJsonHttpClient
from .provider_client import ProviderCallError


class GeminiClient(AsyncJsonHttpClient):
    provider = "gemini"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key.strip()
        self.model = model.strip()

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        if not self.api_key:
            raise ProviderCallError("gemini API key is missing.", retryable=False)
        if not self.model:
            raise ProviderCallError("gemini model is missing.", retryable=False)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 600,
            },
        }
        headers = {"Content-Type": "application/json"}
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        status_code, data, raw_text = await self.post_json(
            url=endpoint,
            payload=payload,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

        if status_code >= 500:
            raise ProviderCallError(
                f"gemini server error: HTTP {status_code}",
                retryable=True,
            )
        if status_code >= 400:
            detail = f" ({raw_text[:200]})" if raw_text else ""
            raise ProviderCallError(
                f"gemini request rejected: HTTP {status_code}{detail}",
                retryable=False,
            )

        text = _extract_gemini_text(data)
        if not text:
            raise ProviderCallError(
                "gemini response missing text content.",
                retryable=True,
            )
        return text


def _extract_gemini_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""

    content = candidates[0].get("content")
    if not isinstance(content, dict):
        return ""

    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""

    texts = []
    for item in parts:
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            texts.append(item["text"].strip())
    return "\n".join(part for part in texts if part).strip()

