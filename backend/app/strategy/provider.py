from __future__ import annotations

from functools import lru_cache

from backend.modules.ai_gateway import GatewayRequest, build_default_router
from backend.modules.ai_gateway.cost_tracker import CostTracker
from backend.modules.ai_gateway.prompt_builder import build_analysis_prompt, build_provider_prompts


@lru_cache(maxsize=8)
def get_strategy_gateway_router(
    *,
    claude_api_key: str,
    claude_model: str,
    openai_api_key: str,
    gpt_model: str,
    grok_api_key: str,
    grok_model: str,
    gemini_api_key: str,
    gemini_model: str,
):
    return build_default_router(
        claude_api_key=claude_api_key,
        claude_model=claude_model,
        openai_api_key=openai_api_key,
        gpt_model=gpt_model,
        grok_api_key=grok_api_key,
        grok_model=grok_model,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
    )


@lru_cache(maxsize=4)
def get_strategy_cost_tracker(redis_url: str) -> CostTracker:
    return CostTracker(redis_url=redis_url)


async def run_ai_consensus(
    *,
    symbol: str,
    user_prompt: str,
    providers: list[str],
    provider_weights: dict[str, float],
    user_id: str,
    timeout_seconds: int,
    retry_count: int,
    retry_backoff_seconds: float,
    daily_budget_usd: float,
    redis_url: str,
    indicator_context: dict,
    sentiment_context: dict,
    claude_api_key: str,
    claude_model: str,
    openai_api_key: str,
    gpt_model: str,
    grok_api_key: str,
    grok_model: str,
    gemini_api_key: str,
    gemini_model: str,
) -> dict:
    prompt = build_analysis_prompt(
        symbol=symbol,
        user_prompt=user_prompt,
        indicator_context=indicator_context,
        sentiment_context=sentiment_context,
    )
    provider_prompts = build_provider_prompts(
        symbol=symbol,
        providers=providers,
        user_prompt=user_prompt,
        indicator_context=indicator_context,
        sentiment_context=sentiment_context,
    )
    request = GatewayRequest(
        symbol=symbol,
        prompt=prompt,
        providers=providers,
        provider_prompts=provider_prompts,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
        retry_backoff_seconds=retry_backoff_seconds,
        provider_weights=provider_weights,
        user_id=user_id,
        daily_budget_usd=daily_budget_usd,
        cost_tracker=get_strategy_cost_tracker(redis_url=redis_url),
    )
    router = get_strategy_gateway_router(
        claude_api_key=claude_api_key,
        claude_model=claude_model,
        openai_api_key=openai_api_key,
        gpt_model=gpt_model,
        grok_api_key=grok_api_key,
        grok_model=grok_model,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
    )
    result = await router.run(request)
    return {
        "prompt": prompt,
        "provider_prompts": provider_prompts,
        "results": result["results"],
        "consensus": result["consensus"],
        "fallback_used": result["fallback_used"],
        "cost": result["cost"],
    }

