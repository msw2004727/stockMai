from __future__ import annotations

import statistics


def build_sentiment_context(symbol: str, price_series: list[dict], window_days: int = 20) -> dict:
    series = price_series[-max(window_days, 1) :]
    if not series:
        return {
            "symbol": symbol,
            "as_of_date": "",
            "window_days": 0,
            "market_sentiment": "neutral",
            "sentiment_score": 0.0,
            "price_change_pct": 0.0,
            "avg_daily_return_pct": 0.0,
            "volatility_pct": 0.0,
            "volume_ratio": None,
            "volatility_level": "unknown",
            "source": "price_action_heuristic",
            "signals": ["No recent price series available."],
            "summary": "No recent market data available for sentiment inference.",
        }

    closes = [_to_float(row.get("close")) for row in series]
    volumes = [_to_float(row.get("volume")) for row in series]
    as_of_date = str(series[-1].get("date", ""))

    price_change_pct = _price_change_pct(closes[0], closes[-1])
    daily_returns = _daily_return_pct_series(closes)
    avg_daily_return_pct = statistics.fmean(daily_returns) if daily_returns else 0.0
    volatility_pct = statistics.pstdev(daily_returns) if len(daily_returns) >= 2 else 0.0
    volume_ratio = _volume_ratio(volumes)
    score = _sentiment_score(
        price_change_pct=price_change_pct,
        avg_daily_return_pct=avg_daily_return_pct,
        volatility_pct=volatility_pct,
        volume_ratio=volume_ratio,
    )

    signals = [
        f"{len(series)}d price change: {price_change_pct:+.2f}%",
        f"avg daily return: {avg_daily_return_pct:+.2f}%",
        f"volatility: {volatility_pct:.2f}%",
    ]
    if volume_ratio is not None:
        signals.append(f"latest volume ratio vs prior average: {volume_ratio:.2f}x")

    market_sentiment = _sentiment_label(score)
    volatility_level = _volatility_level(volatility_pct)
    summary = (
        f"Heuristic sentiment is {market_sentiment} "
        f"(score={score:+.3f}, change={price_change_pct:+.2f}%, vol={volatility_pct:.2f}%)."
    )

    return {
        "symbol": symbol,
        "as_of_date": as_of_date,
        "window_days": len(series),
        "market_sentiment": market_sentiment,
        "sentiment_score": round(score, 4),
        "price_change_pct": round(price_change_pct, 4),
        "avg_daily_return_pct": round(avg_daily_return_pct, 4),
        "volatility_pct": round(volatility_pct, 4),
        "volume_ratio": None if volume_ratio is None else round(volume_ratio, 4),
        "volatility_level": volatility_level,
        "source": "price_action_heuristic",
        "signals": signals,
        "summary": summary,
    }


def _price_change_pct(first_close: float, latest_close: float) -> float:
    if first_close <= 0:
        return 0.0
    return ((latest_close - first_close) / first_close) * 100.0


def _daily_return_pct_series(closes: list[float]) -> list[float]:
    if len(closes) < 2:
        return []
    returns: list[float] = []
    for idx in range(1, len(closes)):
        prev_close = closes[idx - 1]
        if prev_close <= 0:
            continue
        returns.append(((closes[idx] - prev_close) / prev_close) * 100.0)
    return returns


def _volume_ratio(volumes: list[float]) -> float | None:
    if len(volumes) < 2:
        return None
    latest = volumes[-1]
    history = volumes[:-1]
    baseline = statistics.fmean(history) if history else 0.0
    if baseline <= 0:
        return None
    return latest / baseline


def _sentiment_score(
    price_change_pct: float,
    avg_daily_return_pct: float,
    volatility_pct: float,
    volume_ratio: float | None,
) -> float:
    trend = _clamp(price_change_pct / 10.0, -1.0, 1.0)
    momentum = _clamp(avg_daily_return_pct / 2.0, -1.0, 1.0)
    volume_boost = _clamp((volume_ratio - 1.0) if volume_ratio is not None else 0.0, -1.0, 1.0)
    volatility_penalty = _clamp((volatility_pct - 2.5) / 5.0, 0.0, 1.0)

    weighted = (0.40 * trend) + (0.25 * momentum) + (0.20 * volume_boost) - (0.20 * volatility_penalty)
    return _clamp(weighted, -1.0, 1.0)


def _sentiment_label(score: float) -> str:
    if score >= 0.30:
        return "bullish"
    if score <= -0.30:
        return "bearish"
    return "neutral"


def _volatility_level(volatility_pct: float) -> str:
    if volatility_pct < 1.5:
        return "low"
    if volatility_pct < 3.0:
        return "medium"
    return "high"


def _to_float(raw: object) -> float:
    try:
        return float(raw)
    except Exception:
        return 0.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))
