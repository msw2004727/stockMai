from __future__ import annotations

from dataclasses import dataclass

from .mock_clients import MockAIClient
from .provider_client import AIProviderClient
from .response_normalizer import normalize_ai_response


@dataclass
class GatewayRequest:
    symbol: str
    prompt: str
    providers: list[str]
    timeout_seconds: int


class GatewayRouter:
    def __init__(self, clients: dict[str, AIProviderClient]):
        self.clients = clients

    def run(self, request: GatewayRequest) -> dict:
        results = []
        for provider in request.providers:
            client = self.clients.get(provider)
            if client is None:
                results.append(
                    {
                        "provider": provider,
                        "ok": False,
                        "error": f"Provider not configured: {provider}",
                    }
                )
                continue

            try:
                raw_text = client.generate(
                    prompt=request.prompt,
                    symbol=request.symbol,
                    timeout_seconds=request.timeout_seconds,
                )
            except Exception as exc:
                results.append(
                    {
                        "provider": provider,
                        "ok": False,
                        "error": str(exc),
                    }
                )
                continue

            normalized = normalize_ai_response(provider=provider, raw_text=raw_text)
            results.append(
                {
                    "provider": provider,
                    "ok": True,
                    "data": normalized,
                }
            )

        successful = [item["data"] for item in results if item.get("ok")]
        consensus = _build_consensus(successful)
        return {"results": results, "consensus": consensus}


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


def build_default_router() -> GatewayRouter:
    providers = {
        "claude": MockAIClient("claude"),
        "gpt5": MockAIClient("gpt5"),
        "grok": MockAIClient("grok"),
        "gemini": MockAIClient("gemini"),
    }
    return GatewayRouter(clients=providers)

