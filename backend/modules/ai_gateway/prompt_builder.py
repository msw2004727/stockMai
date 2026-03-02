from __future__ import annotations


def build_analysis_prompt(
    symbol: str,
    user_prompt: str = "",
    indicator_context: dict | None = None,
) -> str:
    prompt = (
        "You are a Taiwan stock analysis assistant. "
        "Return JSON with fields: summary, signal, confidence, key_points.\n"
        f"Target symbol: {symbol}."
    )
    indicator_block = _build_indicator_block(indicator_context)
    if indicator_block:
        prompt += f"\n{indicator_block}"
    if user_prompt.strip():
        prompt += f"\nUser focus: {user_prompt.strip()}"
    return prompt


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
