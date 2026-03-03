from __future__ import annotations

from ..config import get_settings
from .movers_repository import load_previous_day_movers


class MarketMoversUnavailableError(Exception):
    pass


def get_market_movers(limit: int = 6) -> dict:
    safe_limit = max(1, min(int(limit), 20))
    settings = get_settings()

    try:
        payload = load_previous_day_movers(
            database_url=settings.database_url,
            limit=safe_limit,
        )
    except Exception as exc:
        raise MarketMoversUnavailableError("市場排行資料暫時無法取得。") from exc

    if not isinstance(payload, dict):
        raise MarketMoversUnavailableError("市場排行資料格式錯誤。")

    return payload
