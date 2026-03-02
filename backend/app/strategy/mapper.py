from __future__ import annotations

from .constants import BUY_THRESHOLD, SELL_THRESHOLD, SCORE_WEIGHTS


def evaluate_indicator_signal(indicator_context: dict) -> dict:
    latest = indicator_context.get("latest") or {}

    sma5 = _to_float_or_none(latest.get("sma5"))
    sma20 = _to_float_or_none(latest.get("sma20"))
    rsi14 = _to_float_or_none(latest.get("rsi14"))
    macd = _to_float_or_none(latest.get("macd"))
    macd_signal = _to_float_or_none(latest.get("macd_signal"))

    score = 0.0
    reasons: list[str] = []

    if sma5 is not None and sma20 is not None:
        if sma5 > sma20:
            score += 0.35
            reasons.append("短均線高於長均線，趨勢偏多。")
        elif sma5 < sma20:
            score -= 0.35
            reasons.append("短均線低於長均線，趨勢偏空。")

    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            score += 0.25
            reasons.append("MACD 高於訊號線，動能偏多。")
        elif macd < macd_signal:
            score -= 0.25
            reasons.append("MACD 低於訊號線，動能偏空。")

    if rsi14 is not None:
        if rsi14 < 30:
            score += 0.15
            reasons.append("RSI 低檔，可能有反彈機會。")
        elif rsi14 > 70:
            score -= 0.15
            reasons.append("RSI 偏高，短線追價風險上升。")
        elif rsi14 >= 55:
            score += 0.05
        elif rsi14 <= 45:
            score -= 0.05

    score = _clamp(score, -1.0, 1.0)
    return {
        "label": _score_to_label(score),
        "score": round(score, 4),
        "reasons": reasons,
    }


def evaluate_sentiment_signal(sentiment_context: dict) -> dict:
    score = _clamp(_to_float(sentiment_context.get("sentiment_score", 0.0)), -1.0, 1.0)
    label = str(sentiment_context.get("market_sentiment", "")).strip().lower() or _score_to_label(score)
    summary = str(sentiment_context.get("summary", "")).strip()

    reasons: list[str] = []
    if summary:
        reasons.append(f"情緒判讀：{summary}")
    volatility_level = str(sentiment_context.get("volatility_level", "unknown"))
    reasons.append(f"波動等級：{volatility_level}")

    return {
        "label": label,
        "score": round(score, 4),
        "reasons": reasons,
    }


def evaluate_ai_signal(ai_consensus: dict) -> dict:
    signal = str(ai_consensus.get("signal", "neutral")).strip().lower()
    confidence = _clamp(_to_float(ai_consensus.get("confidence", 0.0)), 0.0, 1.0)

    score = 0.0
    if signal == "bullish":
        score = confidence
    elif signal == "bearish":
        score = -confidence

    summary = str(ai_consensus.get("summary", "")).strip()
    reasons = [f"AI 共識：{summary}"] if summary else []
    return {
        "label": signal if signal in {"bullish", "bearish", "neutral"} else "neutral",
        "score": round(_clamp(score, -1.0, 1.0), 4),
        "reasons": reasons,
    }


def compose_strategy_decision(
    *,
    indicator_signal: dict,
    sentiment_signal: dict,
    ai_signal: dict,
    sentiment_context: dict,
) -> dict:
    indicator_score = _to_float(indicator_signal.get("score", 0.0))
    sentiment_score = _to_float(sentiment_signal.get("score", 0.0))
    ai_score = _to_float(ai_signal.get("score", 0.0))

    weighted_score = (
        (SCORE_WEIGHTS["indicators"] * indicator_score)
        + (SCORE_WEIGHTS["sentiment"] * sentiment_score)
        + (SCORE_WEIGHTS["ai"] * ai_score)
    )
    weighted_score = _clamp(weighted_score, -1.0, 1.0)

    action = _score_to_action(weighted_score)
    confidence = _decision_confidence(weighted_score=weighted_score, ai_signal=ai_signal)
    risk_level = _resolve_risk_level(sentiment_context=sentiment_context, weighted_score=weighted_score)

    reasons = _unique_lines(
        [
            *indicator_signal.get("reasons", []),
            *sentiment_signal.get("reasons", []),
            *ai_signal.get("reasons", []),
        ]
    )[:6]

    return {
        "action": action,
        "confidence": confidence,
        "risk_level": risk_level,
        "weighted_score": round(weighted_score, 4),
        "components": {
            "indicators": {"label": indicator_signal.get("label", "neutral"), "score": round(indicator_score, 4)},
            "sentiment": {"label": sentiment_signal.get("label", "neutral"), "score": round(sentiment_score, 4)},
            "ai_consensus": {"label": ai_signal.get("label", "neutral"), "score": round(ai_score, 4)},
        },
        "reasons": reasons,
    }


def _score_to_action(score: float) -> str:
    if score >= BUY_THRESHOLD:
        return "buy"
    if score <= SELL_THRESHOLD:
        return "sell"
    return "hold"


def _score_to_label(score: float) -> str:
    if score >= 0.25:
        return "bullish"
    if score <= -0.25:
        return "bearish"
    return "neutral"


def _decision_confidence(weighted_score: float, ai_signal: dict) -> float:
    ai_abs = abs(_to_float(ai_signal.get("score", 0.0)))
    value = (abs(weighted_score) * 0.7) + (ai_abs * 0.3)
    return round(_clamp(value, 0.05, 0.99), 4)


def _resolve_risk_level(sentiment_context: dict, weighted_score: float) -> str:
    volatility = str(sentiment_context.get("volatility_level", "unknown")).lower()
    if volatility == "high" or abs(weighted_score) >= 0.65:
        return "high"
    if volatility == "medium" or abs(weighted_score) >= 0.35:
        return "medium"
    return "low"


def _to_float(raw: object) -> float:
    try:
        return float(raw)
    except Exception:
        return 0.0


def _to_float_or_none(raw: object) -> float | None:
    try:
        return float(raw)
    except Exception:
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def _unique_lines(lines: list[object]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for item in lines:
        line = str(item or "").strip()
        if not line or line in seen:
            continue
        seen.add(line)
        output.append(line)
    return output

