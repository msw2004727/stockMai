from __future__ import annotations

import json


def _strip_markdown_json_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _extract_json_object(raw: str) -> str | None:
    start = raw.find("{")
    if start < 0:
        return None

    depth = 0
    for idx in range(start, len(raw)):
        ch = raw[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return raw[start : idx + 1]
    return None


def _parse_json(raw: str) -> tuple[dict | None, str]:
    candidates = [
        ("plain_json", raw.strip()),
        ("markdown_fence", _strip_markdown_json_fence(raw)),
    ]
    extracted = _extract_json_object(raw)
    if extracted:
        candidates.append(("embedded_json", extracted))

    for strategy, candidate in candidates:
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue
        if isinstance(parsed, dict):
            return parsed, strategy
    return None, "fallback_text"


def _to_signal(raw: object) -> str:
    allowed = {"bullish", "bearish", "neutral"}
    signal = str(raw or "neutral").strip().lower()
    return signal if signal in allowed else "neutral"


def _to_confidence(raw: object) -> float:
    try:
        value = float(raw)
    except Exception:
        return 0.5
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return value


def normalize_ai_response(provider: str, raw_text: str) -> dict:
    parsed, strategy = _parse_json(raw_text)

    if parsed:
        summary = str(parsed.get("summary") or parsed.get("analysis") or "").strip()
        if not summary:
            summary = raw_text.strip()[:240]
        key_points = parsed.get("key_points")
        if not isinstance(key_points, list):
            key_points = []
        return {
            "provider": provider,
            "summary": summary,
            "signal": _to_signal(parsed.get("signal")),
            "confidence": _to_confidence(parsed.get("confidence")),
            "key_points": [str(item) for item in key_points],
            "normalized_by": strategy,
            "raw": raw_text,
        }

    return {
        "provider": provider,
        "summary": raw_text.strip()[:240],
        "signal": "neutral",
        "confidence": 0.5,
        "key_points": [],
        "normalized_by": strategy,
        "raw": raw_text,
    }

