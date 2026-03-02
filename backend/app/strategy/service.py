from __future__ import annotations

from datetime import datetime, timezone

from backend.modules.ai_gateway.consensus import parse_provider_weights
from backend.modules.feature_engineering import compute_latest_indicators
from backend.modules.sentiment_analysis import build_sentiment_context

from ..config import get_settings
from ..stocks.service import (
    DataUnavailableError as StockDataUnavailableError,
    SymbolNotFoundError as StockSymbolNotFoundError,
    get_history,
)
from .constants import DEFAULT_LOOKBACK_DAYS, DEFAULT_PROVIDERS, DEFAULT_SENTIMENT_WINDOW_DAYS
from .mapper import (
    compose_strategy_decision,
    evaluate_ai_signal,
    evaluate_indicator_signal,
    evaluate_sentiment_signal,
)
from .provider import run_ai_consensus


class StrategySymbolNotFoundError(Exception):
    pass


class StrategyDataUnavailableError(Exception):
    pass


async def build_strategy_decision(
    *,
    symbol: str,
    user_id: str,
    user_prompt: str = "",
    providers: list[str] | None = None,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    sentiment_window_days: int = DEFAULT_SENTIMENT_WINDOW_DAYS,
) -> dict:
    settings = get_settings()
    resolved_providers = _resolve_providers(
        raw_providers=providers,
        defaults_raw=settings.ai_default_providers,
    )
    provider_weights = parse_provider_weights(settings.ai_provider_weights)

    try:
        history = get_history(symbol=symbol, days=int(lookback_days))
    except StockSymbolNotFoundError as exc:
        raise StrategySymbolNotFoundError(str(exc)) from exc
    except StockDataUnavailableError as exc:
        raise StrategyDataUnavailableError(str(exc)) from exc

    indicator_context = _build_indicator_context(symbol=symbol, history=history)
    sentiment_context = _build_sentiment_context(
        symbol=symbol,
        history=history,
        window_days=int(sentiment_window_days),
    )
    ai_bundle = await run_ai_consensus(
        symbol=symbol,
        user_prompt=user_prompt,
        providers=resolved_providers,
        provider_weights=provider_weights,
        user_id=user_id,
        timeout_seconds=settings.ai_timeout_seconds,
        retry_count=settings.ai_retry_count,
        retry_backoff_seconds=settings.ai_retry_backoff_seconds,
        daily_budget_usd=settings.ai_daily_budget_usd,
        redis_url=settings.redis_url,
        indicator_context=indicator_context,
        sentiment_context=sentiment_context,
        claude_api_key=settings.anthropic_api_key,
        claude_model=settings.claude_model,
        openai_api_key=settings.openai_api_key,
        gpt_model=settings.gpt_model,
        grok_api_key=settings.grok_api_key,
        grok_model=settings.grok_model,
        gemini_api_key=settings.gemini_api_key,
        gemini_model=settings.gemini_model,
    )

    indicator_signal = evaluate_indicator_signal(indicator_context)
    sentiment_signal = evaluate_sentiment_signal(sentiment_context)
    ai_signal = evaluate_ai_signal(ai_bundle.get("consensus") or {})
    decision = compose_strategy_decision(
        indicator_signal=indicator_signal,
        sentiment_signal=sentiment_signal,
        ai_signal=ai_signal,
        sentiment_context=sentiment_context,
    )

    return {
        "symbol": symbol,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "history_source": str(history.get("source", "unknown")),
        "as_of_date": str(history.get("as_of_date", indicator_context.get("as_of_date", ""))),
        "action": decision["action"],
        "confidence": decision["confidence"],
        "risk_level": decision["risk_level"],
        "weighted_score": decision["weighted_score"],
        "reasons": decision["reasons"],
        "components": decision["components"],
        "indicator_context": indicator_context,
        "sentiment_context": sentiment_context,
        "ai_consensus": ai_bundle.get("consensus"),
        "ai_fallback_used": ai_bundle.get("fallback_used"),
        "providers_requested": resolved_providers,
        "provider_weights": provider_weights,
        "ai_results": ai_bundle.get("results"),
        "cost": ai_bundle.get("cost"),
    }


def _resolve_providers(raw_providers: list[str] | None, defaults_raw: str) -> list[str]:
    if raw_providers:
        candidates = [str(item).strip() for item in raw_providers if str(item).strip()]
    else:
        candidates = [item.strip() for item in defaults_raw.split(",") if item.strip()]

    parsed: list[str] = []
    for name in candidates:
        if name not in parsed:
            parsed.append(name)
    return parsed or list(DEFAULT_PROVIDERS)


def _build_indicator_context(symbol: str, history: dict) -> dict:
    series = history.get("series") or []
    as_of_date = str(series[-1].get("date", "")) if series else ""
    return {
        "symbol": symbol,
        "days": int(history.get("days", len(series))),
        "history_source": str(history.get("source", "unknown")),
        "as_of_date": as_of_date,
        "latest": compute_latest_indicators(series),
    }


def _build_sentiment_context(symbol: str, history: dict, window_days: int) -> dict:
    series = history.get("series") or []
    return build_sentiment_context(
        symbol=symbol,
        price_series=series,
        window_days=max(window_days, 1),
    )

