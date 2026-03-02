from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen

FINMIND_DATA_URL = "https://api.finmindtrade.com/api/v4/data"


def fetch_taiwan_stock_price(
    symbol: str,
    start_date: str,
    end_date: str,
    token: str,
    timeout: int = 8,
) -> list[dict]:
    """Fetch raw daily stock prices from FinMind."""
    if not token:
        return []

    query = urlencode(
        {
            "dataset": "TaiwanStockPrice",
            "data_id": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "token": token,
        }
    )
    with urlopen(f"{FINMIND_DATA_URL}?{query}", timeout=timeout) as response:
        payload = json.load(response)

    status = payload.get("status")
    if status not in {200, "200"}:
        return []

    return payload.get("data") or []

