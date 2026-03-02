from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import enforce_rate_limit
from .service import (
    DataUnavailableError,
    QuoteRateLimitedError,
    SymbolNotFoundError,
    get_history,
    get_indicators,
    get_quote,
)

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/quote")
def get_stock_quote(
    symbol: str = Query(..., pattern=r"^\d{4,6}$"),
    _quota: dict = Depends(enforce_rate_limit("stocks_quote")),
) -> dict:
    try:
        return get_quote(symbol)
    except QuoteRateLimitedError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except DataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SymbolNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/history")
def get_stock_history(
    symbol: str = Query(..., pattern=r"^\d{4,6}$"),
    days: int = Query(5, ge=3, le=30),
    _quota: dict = Depends(enforce_rate_limit("stocks_history")),
) -> dict:
    try:
        return get_history(symbol, days=days)
    except DataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SymbolNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/indicators")
def get_stock_indicators(
    symbol: str = Query(..., pattern=r"^\d{4,6}$"),
    days: int = Query(60, ge=30, le=365),
    _quota: dict = Depends(enforce_rate_limit("stocks_indicators")),
) -> dict:
    try:
        return get_indicators(symbol, days=days)
    except DataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SymbolNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
