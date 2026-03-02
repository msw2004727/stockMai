from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.modules.ai_gateway import GatewayRequest, build_default_router
from backend.modules.ai_gateway.consensus import parse_provider_weights
from backend.modules.ai_gateway.cost_tracker import CostTracker
from backend.modules.ai_gateway.prompt_builder import build_analysis_prompt, build_provider_prompts
from backend.modules.data_pipeline import load_recent_history
from backend.modules.feature_engineering import compute_latest_indicators
from backend.modules.sentiment_analysis import build_sentiment_context

from ..auth import enforce_rate_limit, get_current_user
from ..config import get_settings

router = APIRouter(prefix="/ai", tags=["ai"])


class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., pattern=r"^\d{4,6}$")
    user_prompt: str = Field("", max_length=500)
    providers: list[str] | None = None


def _parse_default_providers(raw: str) -> list[str]:
    providers = [item.strip() for item in raw.split(",") if item.strip()]
    return providers or ["claude", "gpt5", "grok", "gemini"]


@lru_cache(maxsize=8)
def _get_gateway_router(
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
def _get_cost_tracker(redis_url: str) -> CostTracker:
    return CostTracker(redis_url=redis_url)


def _load_cached_history(symbol: str, database_url: str, days: int = 60) -> dict | None:
    return load_recent_history(
        database_url=database_url,
        symbol=symbol,
        days=days,
        max_age_days=7,
    )


def _build_indicator_context(symbol: str, cached: dict | None, days: int = 60) -> dict:
    if not cached:
        return {
            "symbol": symbol,
            "days": days,
            "history_source": "none",
            "as_of_date": "",
            "latest": {},
        }

    series = cached.get("series") or []
    as_of_date = ""
    if series:
        as_of_date = str(series[-1].get("date", ""))
    return {
        "symbol": symbol,
        "days": int(cached.get("days", days)),
        "history_source": str(cached.get("source", "postgres")),
        "as_of_date": as_of_date,
        "latest": compute_latest_indicators(series),
    }


def _build_sentiment_context(symbol: str, cached: dict | None, days: int = 20) -> dict:
    if not cached:
        return build_sentiment_context(symbol=symbol, price_series=[], window_days=days)
    series = cached.get("series") or []
    return build_sentiment_context(symbol=symbol, price_series=series, window_days=days)


@router.post("/analyze")
async def analyze_stock(
    payload: AnalyzeRequest,
    user: dict = Depends(get_current_user),
    _quota: dict = Depends(enforce_rate_limit("ai_analyze")),
) -> dict:
    settings = get_settings()
    providers = payload.providers or _parse_default_providers(settings.ai_default_providers)
    provider_weights = parse_provider_weights(settings.ai_provider_weights)
    cached = _load_cached_history(
        symbol=payload.symbol,
        database_url=settings.database_url,
        days=60,
    )
    indicator_context = _build_indicator_context(
        symbol=payload.symbol,
        cached=cached,
        days=60,
    )
    sentiment_context = _build_sentiment_context(
        symbol=payload.symbol,
        cached=cached,
        days=20,
    )
    prompt = build_analysis_prompt(
        payload.symbol,
        payload.user_prompt,
        indicator_context=indicator_context,
        sentiment_context=sentiment_context,
    )
    provider_prompts = build_provider_prompts(
        symbol=payload.symbol,
        providers=providers,
        user_prompt=payload.user_prompt,
        indicator_context=indicator_context,
        sentiment_context=sentiment_context,
    )
    cost_tracker = _get_cost_tracker(settings.redis_url)

    request = GatewayRequest(
        symbol=payload.symbol,
        prompt=prompt,
        providers=providers,
        provider_prompts=provider_prompts,
        timeout_seconds=settings.ai_timeout_seconds,
        retry_count=settings.ai_retry_count,
        retry_backoff_seconds=settings.ai_retry_backoff_seconds,
        provider_weights=provider_weights,
        user_id=user["user_id"],
        daily_budget_usd=settings.ai_daily_budget_usd,
        cost_tracker=cost_tracker,
    )
    router = _get_gateway_router(
        claude_api_key=settings.anthropic_api_key,
        claude_model=settings.claude_model,
        openai_api_key=settings.openai_api_key,
        gpt_model=settings.gpt_model,
        grok_api_key=settings.grok_api_key,
        grok_model=settings.grok_model,
        gemini_api_key=settings.gemini_api_key,
        gemini_model=settings.gemini_model,
    )
    gateway_result = await router.run(request)

    return {
        "symbol": payload.symbol,
        "providers_requested": providers,
        "provider_weights": provider_weights,
        "indicator_context": indicator_context,
        "sentiment_context": sentiment_context,
        "prompt": prompt,
        "provider_prompts": provider_prompts,
        "results": gateway_result["results"],
        "consensus": gateway_result["consensus"],
        "fallback_used": gateway_result["fallback_used"],
        "cost": gateway_result["cost"],
    }
