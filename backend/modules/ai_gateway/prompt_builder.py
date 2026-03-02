from __future__ import annotations

PROVIDER_ALIASES = {
    "openai": "gpt5",
    "gpt": "gpt5",
    "gpt-5": "gpt5",
    "anthropic": "claude",
    "xai": "grok",
    "google": "gemini",
}

PROVIDER_ROLE_INSTRUCTIONS = {
    "claude": (
        "Provider role: Deep semantic analyst. "
        "Prioritize policy interpretation, second-order industry-chain effects, and scenario analysis."
    ),
    "gpt5": (
        "Provider role: Technical analyst. "
        "Prioritize multi-timeframe indicator alignment, trend structure, and executable risk-reward levels."
    ),
    "grok": (
        "Provider role: Real-time intelligence scout. "
        "Prioritize event-driven catalysts, social sentiment shifts, and near-term headline risk."
    ),
    "gemini": (
        "Provider role: Capital-flow and data auditor. "
        "Prioritize abnormal volume/price behavior, consistency checks, and fast anomaly spotting."
    ),
}


def build_analysis_prompt(
    symbol: str,
    user_prompt: str = "",
    indicator_context: dict | None = None,
    provider: str | None = None,
) -> str:
    prompt = (
        "You are a Taiwan stock analysis assistant. "
        "Return JSON with fields: summary, signal, confidence, key_points. "
        "signal must be one of bullish/bearish/neutral. confidence must be 0~1.\n"
        f"Target symbol: {symbol}."
    )
    role_block = _build_role_block(provider)
    if role_block:
        prompt += f"\n{role_block}"

    prompt += "\nIf key data is missing, explicitly state assumptions and uncertainty in key_points."

    indicator_block = _build_indicator_block(indicator_context)
    if indicator_block:
        prompt += f"\n{indicator_block}"

    if user_prompt.strip():
        prompt += f"\nUser focus: {user_prompt.strip()}"

    prompt += "\nRespond in Traditional Chinese."
    return prompt


def build_provider_prompts(
    symbol: str,
    providers: list[str],
    user_prompt: str = "",
    indicator_context: dict | None = None,
) -> dict[str, str]:
    prompts: dict[str, str] = {}
    for provider in providers:
        key = str(provider).strip()
        if not key:
            continue
        prompts[key] = build_analysis_prompt(
            symbol=symbol,
            user_prompt=user_prompt,
            indicator_context=indicator_context,
            provider=key,
        )
    return prompts


def _build_role_block(provider: str | None) -> str:
    normalized = _normalize_provider(provider)
    if not normalized:
        return ""
    return PROVIDER_ROLE_INSTRUCTIONS.get(
        normalized,
        "Provider role: General analyst. Provide balanced directional judgment with transparent assumptions.",
    )


def _normalize_provider(provider: str | None) -> str:
    raw = str(provider or "").strip().lower()
    if not raw:
        return ""
    return PROVIDER_ALIASES.get(raw, raw)


def _build_indicator_block(indicator_context: dict | None) -> str:
    if not indicator_context:
        return ""

    latest = indicator_context.get("latest")
    if not isinstance(latest, dict):
        return ""

    keys = ["sma5", "sma20", "rsi14", "macd", "macd_signal", "macd_hist"]
    if not any(latest.get(key) is not None for key in keys):
        return ""

    source = str(indicator_context.get("history_source", "unknown"))
    as_of_date = str(indicator_context.get("as_of_date", ""))
    days = int(indicator_context.get("days", 0) or 0)
    parts = [f"Technical indicators (source={source}, days={days}, as_of={as_of_date}):"]
    parts.append(f"SMA5={_fmt(latest.get('sma5'))}")
    parts.append(f"SMA20={_fmt(latest.get('sma20'))}")
    parts.append(f"RSI14={_fmt(latest.get('rsi14'))}")
    parts.append(f"MACD={_fmt(latest.get('macd'))}")
    parts.append(f"MACD_SIGNAL={_fmt(latest.get('macd_signal'))}")
    parts.append(f"MACD_HIST={_fmt(latest.get('macd_hist'))}")
    return " ".join(parts)


def _fmt(raw: object) -> str:
    if raw is None:
        return "NA"
    try:
        return str(round(float(raw), 6))
    except Exception:
        return "NA"
