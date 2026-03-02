from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import enforce_rate_limit, get_current_user
from .schemas import StrategyDecisionRequest
from .service import (
    StrategyDataUnavailableError,
    StrategySymbolNotFoundError,
    build_strategy_decision,
)

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.post("/decision")
async def get_strategy_decision(
    payload: StrategyDecisionRequest,
    user: dict = Depends(get_current_user),
    _quota: dict = Depends(enforce_rate_limit("strategy_decision")),
) -> dict:
    try:
        return await build_strategy_decision(
            symbol=payload.symbol,
            user_id=user["user_id"],
            user_prompt=payload.user_prompt,
            providers=payload.providers,
            lookback_days=payload.lookback_days,
            sentiment_window_days=payload.sentiment_window_days,
        )
    except StrategyDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StrategySymbolNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

