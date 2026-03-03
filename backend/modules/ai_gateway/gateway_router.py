from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from .claude_client import ClaudeClient
from .consensus import build_weighted_consensus
from .cost_tracker import CostTracker
from .deepseek_client import DeepSeekClient
from .grok_client import GrokClient
from .mock_clients import MockAIClient
from .openai_client import OpenAIClient
from .prompt_builder import build_narrative_patch_prompt
from .provider_client import AIProviderClient, ProviderCallError
from .response_normalizer import normalize_ai_response


@dataclass
class GatewayRequest:
    symbol: str
    prompt: str
    providers: list[str]
    timeout_seconds: int
    provider_prompts: dict[str, str] = field(default_factory=dict)
    retry_count: int = 2
    retry_backoff_seconds: float = 0.35
    provider_weights: dict[str, float] = field(default_factory=dict)
    user_id: str = "anonymous"
    daily_budget_usd: float = 0.0
    cost_tracker: CostTracker | None = None


class GatewayRouter:
    def __init__(self, clients: dict[str, AIProviderClient]):
        self.clients = clients

    async def run(self, request: GatewayRequest) -> dict:
        results: list[dict] = []
        cost_entries: list[dict] = []
        fallback_used = False
        previous_failure = False
        budget_blocked = False
        user_id = _normalize_user_id(request.user_id)
        for provider in request.providers:
            client = self.clients.get(provider)
            provider_prompt = _resolve_provider_prompt(request, provider)
            if client is None:
                previous_failure = True
                results.append(
                    {
                        "provider": provider,
                        "ok": False,
                        "error": f"Provider not configured: {provider}",
                        "error_type": "config",
                    }
                )
                continue

            if request.cost_tracker is not None:
                try:
                    request.cost_tracker.check_budget_before_request(
                        user_id=user_id,
                        daily_budget_usd=request.daily_budget_usd,
                    )
                except ProviderCallError as exc:
                    previous_failure = True
                    budget_blocked = True
                    results.append(
                        {
                            "provider": provider,
                            "ok": False,
                            "error": str(exc),
                            "retryable": False,
                            "error_type": "budget",
                        }
                    )
                    break

            try:
                raw_text, attempts = await _run_with_retry(
                    client=client,
                    prompt=provider_prompt,
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
                        "error_type": "provider",
                    }
                )
                continue

            if previous_failure:
                fallback_used = True
            normalized = normalize_ai_response(provider=provider, raw_text=raw_text)
            total_attempts = attempts
            all_prompts = [provider_prompt]
            all_raw_texts = [raw_text]
            narrative_enriched = False
            missing_narratives = _missing_narrative_fields(normalized)
            if missing_narratives:
                narrative_prompt = build_narrative_patch_prompt(
                    symbol=request.symbol,
                    original_prompt=provider_prompt,
                    normalized=normalized,
                    missing_fields=missing_narratives,
                )
                try:
                    narrative_text, narrative_attempts = await _run_with_retry(
                        client=client,
                        prompt=narrative_prompt,
                        symbol=request.symbol,
                        timeout_seconds=request.timeout_seconds,
                        retry_count=request.retry_count,
                        retry_backoff_seconds=request.retry_backoff_seconds,
                    )
                    total_attempts += narrative_attempts
                    all_prompts.append(narrative_prompt)
                    all_raw_texts.append(narrative_text)
                    narrative_normalized = normalize_ai_response(provider=provider, raw_text=narrative_text)
                    normalized = _merge_narrative_fields(normalized, narrative_normalized)
                    narrative_enriched = _has_any_narrative_fields(narrative_normalized)
                except Exception:
                    # Keep primary result if enrichment call fails.
                    pass

            result_item = {
                "provider": provider,
                "ok": True,
                "data": normalized,
                "attempts": total_attempts,
            }
            if narrative_enriched:
                result_item["narrative_enriched"] = True
            usage = _track_cost_usage(
                request=request,
                user_id=user_id,
                provider=provider,
                prompt_text="\n\n".join(all_prompts),
                raw_text="\n\n".join(all_raw_texts),
            )
            if usage is not None:
                result_item["cost"] = usage
                cost_entries.append(usage)
            results.append(result_item)

        successful = [item["data"] for item in results if item.get("ok")]
        consensus = build_weighted_consensus(
            successful=successful,
            provider_weights=request.provider_weights,
        )
        cost_summary = _build_cost_summary(
            request=request,
            user_id=user_id,
            entries=cost_entries,
            budget_blocked=budget_blocked,
        )
        return {
            "results": results,
            "consensus": consensus,
            "fallback_used": fallback_used,
            "cost": cost_summary,
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


def _normalize_user_id(user_id: str) -> str:
    parsed = user_id.strip()
    return parsed if parsed else "anonymous"


def _track_cost_usage(
    request: GatewayRequest,
    user_id: str,
    provider: str,
    prompt_text: str,
    raw_text: str,
) -> dict | None:
    if request.cost_tracker is None:
        return None

    input_tokens = request.cost_tracker.estimate_tokens(prompt_text)
    output_tokens = request.cost_tracker.estimate_tokens(raw_text)
    return request.cost_tracker.record_usage(
        user_id=user_id,
        provider=provider,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        daily_budget_usd=request.daily_budget_usd,
    )


def _build_cost_summary(
    request: GatewayRequest,
    user_id: str,
    entries: list[dict],
    budget_blocked: bool,
) -> dict:
    total_request_cost = round(sum(float(item.get("request_cost_usd", 0.0)) for item in entries), 8)
    daily_total = 0.0
    if request.cost_tracker is not None:
        daily_total = round(request.cost_tracker.get_daily_total_usd(user_id), 8)

    budget_exceeded = budget_blocked or any(bool(item.get("budget_exceeded")) for item in entries)
    return {
        "enabled": request.cost_tracker is not None,
        "entries": entries,
        "total_request_cost_usd": total_request_cost,
        "daily_total_usd": daily_total,
        "daily_budget_usd": round(request.daily_budget_usd, 8),
        "budget_exceeded": budget_exceeded,
    }


def _resolve_provider_prompt(request: GatewayRequest, provider: str) -> str:
    prompt = request.provider_prompts.get(provider, request.prompt)
    parsed = prompt.strip()
    return parsed if parsed else request.prompt


def _missing_narrative_fields(normalized: dict) -> list[str]:
    required = ("bullish_view", "bearish_view", "easy_summary")
    missing: list[str] = []
    for key in required:
        value = normalized.get(key)
        if isinstance(value, str) and value.strip():
            continue
        missing.append(key)
    return missing


def _has_any_narrative_fields(normalized: dict) -> bool:
    return any(
        isinstance(normalized.get(key), str) and normalized.get(key).strip()
        for key in ("bullish_view", "bearish_view", "easy_summary")
    )


def _merge_narrative_fields(base: dict, patch: dict) -> dict:
    merged = dict(base)
    for key in ("bullish_view", "bearish_view", "easy_summary"):
        patch_value = patch.get(key)
        if isinstance(patch_value, str) and patch_value.strip():
            merged[key] = patch_value.strip()
    return merged


def build_default_router(
    claude_api_key: str,
    claude_model: str,
    openai_api_key: str,
    gpt_model: str,
    grok_api_key: str,
    grok_model: str,
    deepseek_api_key: str,
    deepseek_model: str,
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

    deepseek_client: AIProviderClient
    if deepseek_api_key.strip():
        deepseek_client = DeepSeekClient(api_key=deepseek_api_key, model=deepseek_model)
    else:
        deepseek_client = MockAIClient("deepseek")

    providers = {
        "claude": claude_client,
        "gpt5": gpt_client,
        "grok": grok_client,
        "deepseek": deepseek_client,
    }
    return GatewayRouter(clients=providers)

