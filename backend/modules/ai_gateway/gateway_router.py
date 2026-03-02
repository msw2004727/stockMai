from __future__ import annotations

import asyncio
from dataclasses import dataclass

from .claude_client import ClaudeClient
from .gemini_client import GeminiClient
from .grok_client import GrokClient
from .mock_clients import MockAIClient
from .openai_client import OpenAIClient
from .provider_client import AIProviderClient, ProviderCallError
from .response_normalizer import normalize_ai_response


@dataclass
class GatewayRequest:
    symbol: str
    prompt: str
    providers: list[str]
    timeout_seconds: int
    retry_count: int = 2
    retry_backoff_seconds: float = 0.35


class GatewayRouter:
    def __init__(self, clients: dict[str, AIProviderClient]):
        self.clients = clients

    async def run(self, request: GatewayRequest) -> dict:
        results = []
        fallback_used = False
        previous_failure = False
        for provider in request.providers:
            client = self.clients.get(provider)
            if client is None:
                previous_failure = True
                results.append(
                    {
                        "provider": provider,
                        "ok": False,
                        "error": f"Provider not configured: {provider}",
                    }
                )
                continue

            try:
                raw_text, attempts = await _run_with_retry(
                    client=client,
                    prompt=request.prompt,
                    symbol=request.symbol,
                    timeout_seconds=request.timeout_seconds,
                    retry_count=request.retry_count,
                    retry_backoff_seconds=request.retry_backoff_seconds,
                )
            except Exception as exc:
                previous_failure = True
                results.append(
                    {
                        "provider": provider,
                        "ok": False,
                        "error": str(exc),
                        "retryable": _is_retryable_error(exc),
                    }
                )
                continue

            if previous_failure:
                fallback_used = True
            normalized = normalize_ai_response(provider=provider, raw_text=raw_text)
            results.append(
                {
                    "provider": provider,
                    "ok": True,
                    "data": normalized,
                    "attempts": attempts,
                }
            )

        successful = [item["data"] for item in results if item.get("ok")]
        consensus = _build_consensus(successful)
        return {"results": results, "consensus": consensus, "fallback_used": fallback_used}


def _build_consensus(successful: list[dict]) -> dict:
    if not successful:
        return {
            "signal": "neutral",
            "confidence": 0.0,
            "summary": "No provider produced usable output.",
        }

    sorted_by_conf = sorted(successful, key=lambda item: item.get("confidence", 0.0), reverse=True)
    best = sorted_by_conf[0]
    return {
        "signal": best.get("signal", "neutral"),
        "confidence": best.get("confidence", 0.0),
        "summary": best.get("summary", ""),
        "source_provider": best.get("provider", ""),
    }


def _is_retryable_error(exc: Exception) -> bool:
    if isinstance(exc, ProviderCallError):
        return exc.retryable
    return True


async def _run_with_retry(
    client: AIProviderClient,
    prompt: str,
    symbol: str,
    timeout_seconds: int,
    retry_count: int,
    retry_backoff_seconds: float,
) -> tuple[str, int]:
    max_attempts = max(retry_count + 1, 1)
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            text = await client.generate(
                prompt=prompt,
                symbol=symbol,
                timeout_seconds=timeout_seconds,
            )
            return text, attempt
        except Exception as exc:
            last_exc = exc
            retryable = _is_retryable_error(exc)
            if attempt >= max_attempts or not retryable:
                break
            await asyncio.sleep(retry_backoff_seconds * (2 ** (attempt - 1)))

    assert last_exc is not None
    raise last_exc


def build_default_router(
    claude_api_key: str,
    claude_model: str,
    openai_api_key: str,
    gpt_model: str,
    grok_api_key: str,
    grok_model: str,
    gemini_api_key: str,
    gemini_model: str,
) -> GatewayRouter:
    claude_client: AIProviderClient
    if claude_api_key.strip():
        claude_client = ClaudeClient(api_key=claude_api_key, model=claude_model)
    else:
        claude_client = MockAIClient("claude")

    gpt_client: AIProviderClient
    if openai_api_key.strip():
        gpt_client = OpenAIClient(api_key=openai_api_key, model=gpt_model)
    else:
        gpt_client = MockAIClient("gpt5")

    grok_client: AIProviderClient
    if grok_api_key.strip():
        grok_client = GrokClient(api_key=grok_api_key, model=grok_model)
    else:
        grok_client = MockAIClient("grok")

    gemini_client: AIProviderClient
    if gemini_api_key.strip():
        gemini_client = GeminiClient(api_key=gemini_api_key, model=gemini_model)
    else:
        gemini_client = MockAIClient("gemini")

    providers = {
        "claude": claude_client,
        "gpt5": gpt_client,
        "grok": grok_client,
        "gemini": gemini_client,
    }
    return GatewayRouter(clients=providers)
