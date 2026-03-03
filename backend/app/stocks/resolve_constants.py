from __future__ import annotations

HIGH_CONFIDENCE_MIN = 88
LOW_CONFIDENCE_MIN = 70
MIN_MARGIN = 8

DEFAULT_LIMIT = 5
MAX_LIMIT = 10

# Common typo aliases can be expanded from real-world query logs.
COMMON_TYPO_ALIASES: dict[str, str] = {
    "台機電": "台積電",
    "連發科": "聯發科",
}
