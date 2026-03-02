from __future__ import annotations


def build_analysis_prompt(symbol: str, user_prompt: str = "") -> str:
    prompt = (
        "You are a Taiwan stock analysis assistant. "
        "Return JSON with fields: summary, signal, confidence, key_points.\n"
        f"Target symbol: {symbol}."
    )
    if user_prompt.strip():
        prompt += f"\nUser focus: {user_prompt.strip()}"
    return prompt

