from __future__ import annotations


def parse_provider_weights(raw: str) -> dict[str, float]:
    weights: dict[str, float] = {}
    for part in raw.split(","):
        token = part.strip()
        if not token or "=" not in token:
            continue
        provider, value = token.split("=", 1)
        provider = provider.strip().lower()
        if not provider:
            continue
        try:
            parsed = float(value.strip())
        except ValueError:
            continue
        if parsed > 0:
            weights[provider] = parsed
    return weights


def build_weighted_consensus(successful: list[dict], provider_weights: dict[str, float]) -> dict:
    if not successful:
        return {
            "signal": "neutral",
            "confidence": 0.0,
            "summary": "No provider produced usable output.",
            "source_provider": "",
            "signal_scores": {"bullish": 0.0, "bearish": 0.0, "neutral": 0.0},
        }

    signal_scores = {"bullish": 0.0, "bearish": 0.0, "neutral": 0.0}
    weighted_items: list[tuple[float, dict]] = []

    for item in successful:
        provider = str(item.get("provider", ""))
        signal = str(item.get("signal", "neutral")).lower()
        if signal not in signal_scores:
            signal = "neutral"

        confidence = _clamp_confidence(item.get("confidence", 0.5))
        provider_weight = provider_weights.get(provider, 1.0)
        weighted_score = confidence * max(provider_weight, 0.0)

        signal_scores[signal] += weighted_score
        weighted_items.append((weighted_score, item))

    total_score = sum(signal_scores.values())
    selected_signal = max(signal_scores.items(), key=lambda kv: kv[1])[0]

    chosen_candidates = [
        pair for pair in weighted_items if str(pair[1].get("signal", "neutral")).lower() == selected_signal
    ]
    if not chosen_candidates:
        chosen_candidates = weighted_items

    top_weight, top_item = max(chosen_candidates, key=lambda pair: pair[0])
    confidence = (signal_scores[selected_signal] / total_score) if total_score > 0 else 0.0
    confidence = round(confidence, 4)

    return {
        "signal": selected_signal,
        "confidence": confidence,
        "summary": str(top_item.get("summary", "")),
        "source_provider": str(top_item.get("provider", "")),
        "winning_weighted_score": round(top_weight, 6),
        "signal_scores": {k: round(v, 6) for k, v in signal_scores.items()},
    }


def _clamp_confidence(raw: object) -> float:
    try:
        value = float(raw)
    except Exception:
        return 0.5
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return value
