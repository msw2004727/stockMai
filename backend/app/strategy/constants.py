from __future__ import annotations

DEFAULT_LOOKBACK_DAYS = 60
DEFAULT_SENTIMENT_WINDOW_DAYS = 20
DEFAULT_PROVIDERS = ["claude", "gpt5", "grok", "gemini"]

SCORE_WEIGHTS = {
    "indicators": 0.45,
    "sentiment": 0.25,
    "ai": 0.30,
}

BUY_THRESHOLD = 0.25
SELL_THRESHOLD = -0.25

