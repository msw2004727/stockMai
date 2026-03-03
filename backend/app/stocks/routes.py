from fastapi import APIRouter, Depends, HTTPException, Query, Response

from ..auth import enforce_rate_limit
from .market_snapshot_service import MarketSnapshotSyncError, run_market_snapshot
from .movers_service import MarketMoversUnavailableError, get_market_movers
from .pipeline_status_service import PipelineStatusUnavailableError, get_pipeline_status
from .service import (
    DataUnavailableError,
    QuoteRateLimitedError,
    SymbolNotFoundError,
    get_history,
    get_indicators,
    get_quote,
)
from .search_service import search_stock_symbols

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/quote")
def get_stock_quote(
    response: Response,
    symbol: str = Query(..., pattern=r"^\d{4,6}$"),
    _quota: dict = Depends(enforce_rate_limit("stocks_quote")),
) -> dict:
    try:
        payload = get_quote(symbol)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return payload
    except QuoteRateLimitedError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except DataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SymbolNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/history")
def get_stock_history(
    symbol: str = Query(..., pattern=r"^\d{4,6}$"),
    days: int = Query(5, ge=3, le=180),
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


@router.get("/search")
def search_stocks(
    q: str = Query(..., min_length=1, max_length=20),
    limit: int = Query(8, ge=1, le=20),
    _quota: dict = Depends(enforce_rate_limit("stocks_search")),
) -> dict:
    return {
        "query": q,
        "limit": int(limit),
        "results": search_stock_symbols(q, limit=limit),
    }


@router.get("/movers")
def get_stock_movers(
    limit: int = Query(6, ge=3, le=20),
    _quota: dict = Depends(enforce_rate_limit("stocks_movers")),
) -> dict:
    try:
        return get_market_movers(limit=limit)
    except MarketMoversUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/pipeline/snapshot")
def sync_market_snapshot(
    max_symbols: int = Query(3000, ge=100, le=5000),
    _quota: dict = Depends(enforce_rate_limit("stocks_pipeline")),
) -> dict:
    try:
        return run_market_snapshot(max_symbols=max_symbols)
    except MarketSnapshotSyncError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/pipeline/status")
def get_snapshot_pipeline_status(
    _quota: dict = Depends(enforce_rate_limit("stocks_pipeline_status")),
) -> dict:
    try:
        return get_pipeline_status()
    except PipelineStatusUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
