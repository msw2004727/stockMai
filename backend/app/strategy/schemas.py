from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import DEFAULT_LOOKBACK_DAYS, DEFAULT_SENTIMENT_WINDOW_DAYS


class StrategyDecisionRequest(BaseModel):
    symbol: str = Field(..., pattern=r"^\d{4,6}$")
    user_prompt: str = Field("", max_length=500)
    providers: list[str] | None = None
    lookback_days: int = Field(
        DEFAULT_LOOKBACK_DAYS,
        ge=30,
        le=365,
    )
    sentiment_window_days: int = Field(
        DEFAULT_SENTIMENT_WINDOW_DAYS,
        ge=10,
        le=120,
    )

