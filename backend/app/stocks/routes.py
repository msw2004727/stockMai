from fastapi import APIRouter, HTTPException, Query

from .service import SymbolNotFoundError, get_history, get_quote

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/quote")
def get_stock_quote(symbol: str = Query(..., pattern=r"^\d{4}$")) -> dict:
    try:
        return get_quote(symbol)
    except SymbolNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/history")
def get_stock_history(
    symbol: str = Query(..., pattern=r"^\d{4}$"),
    days: int = Query(5, ge=3, le=30),
) -> dict:
    try:
        return get_history(symbol, days=days)
    except SymbolNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
