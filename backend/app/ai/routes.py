from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.modules.ai_gateway import GatewayRequest, build_default_router
from backend.modules.ai_gateway.prompt_builder import build_analysis_prompt

from ..auth import enforce_rate_limit
from ..config import get_settings

router = APIRouter(prefix="/ai", tags=["ai"])


class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., pattern=r"^\d{4}$")
    user_prompt: str = Field("", max_length=500)
    providers: list[str] | None = None


def _parse_default_providers(raw: str) -> list[str]:
    providers = [item.strip() for item in raw.split(",") if item.strip()]
    return providers or ["claude", "gpt5", "grok", "gemini"]


@lru_cache(maxsize=1)
def _get_gateway_router():
    return build_default_router()


@router.post("/analyze")
def analyze_stock(
    payload: AnalyzeRequest,
    _quota: dict = Depends(enforce_rate_limit("ai_analyze")),
) -> dict:
    settings = get_settings()
    providers = payload.providers or _parse_default_providers(settings.ai_default_providers)
    prompt = build_analysis_prompt(payload.symbol, payload.user_prompt)

    request = GatewayRequest(
        symbol=payload.symbol,
        prompt=prompt,
        providers=providers,
        timeout_seconds=settings.ai_timeout_seconds,
    )
    gateway_result = _get_gateway_router().run(request)

    return {
        "symbol": payload.symbol,
        "providers_requested": providers,
        "prompt": prompt,
        "results": gateway_result["results"],
        "consensus": gateway_result["consensus"],
    }

