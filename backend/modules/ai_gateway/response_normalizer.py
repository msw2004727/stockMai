from __future__ import annotations

import json
import re


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

    salvaged = _salvage_partial_json(raw)
    if salvaged:
        return salvaged, "partial_json"
    return None, "fallback_text"


def _salvage_partial_json(raw: str) -> dict | None:
    summary = _extract_quoted_value(raw, ("summary", "analysis"))
    signal = _extract_quoted_value(raw, ("signal",))
    confidence = _extract_number_value(raw, "confidence")
    key_points = _extract_key_points(raw)
    bullish_view = _extract_quoted_value(raw, ("bullish_view", "bullish", "bull_case"))
    bearish_view = _extract_quoted_value(raw, ("bearish_view", "bearish", "bear_case"))
    easy_summary = _extract_quoted_value(raw, ("easy_summary", "light_summary", "summary_easy"))

    if not any([summary, signal, confidence is not None, key_points, bullish_view, bearish_view, easy_summary]):
        return None

    result: dict[str, object] = {}
    if summary:
        result["summary"] = summary
    if signal:
        result["signal"] = signal
    if confidence is not None:
        result["confidence"] = confidence
    if key_points:
        result["key_points"] = key_points
    if bullish_view:
        result["bullish_view"] = bullish_view
    if bearish_view:
        result["bearish_view"] = bearish_view
    if easy_summary:
        result["easy_summary"] = easy_summary
    return result


def _extract_quoted_value(raw: str, keys: tuple[str, ...]) -> str:
    key_pattern = "|".join(re.escape(key) for key in keys)
    pattern = rf'"(?:{key_pattern})"\s*:\s*"((?:\\.|[^"\\])*)"'
    match = re.search(pattern, raw, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""

    captured = match.group(1)
    try:
        return str(json.loads(f'"{captured}"')).strip()
    except Exception:
        return captured.replace('\\"', '"').strip()


def _extract_number_value(raw: str, key: str) -> float | None:
    pattern = rf'"{re.escape(key)}"\s*:\s*(-?\d+(?:\.\d+)?)'
    match = re.search(pattern, raw, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1))
    except Exception:
        return None


def _extract_key_points(raw: str) -> list[str]:
    match = re.search(r'"key_points"\s*:\s*\[(.*?)(?:\]|$)', raw, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    segment = match.group(1)
    items = re.findall(r'"((?:\\.|[^"\\])*)"', segment, flags=re.DOTALL)
    parsed_items: list[str] = []
    for item in items:
        try:
            parsed = str(json.loads(f'"{item}"')).strip()
        except Exception:
            parsed = item.replace('\\"', '"').strip()
        if parsed:
            parsed_items.append(parsed)
    return parsed_items


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


def _pick_text(raw: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_ai_response(provider: str, raw_text: str) -> dict:
    parsed, strategy = _parse_json(raw_text)

    if parsed:
        summary = _pick_text(parsed, ("summary", "analysis"))
        if not summary:
            summary = raw_text.strip()[:240]
        key_points = parsed.get("key_points")
        if not isinstance(key_points, list):
            key_points = []
        bullish_view = _pick_text(parsed, ("bullish_view", "bullish", "bull_case"))
        bearish_view = _pick_text(parsed, ("bearish_view", "bearish", "bear_case"))
        easy_summary = _pick_text(parsed, ("easy_summary", "light_summary", "summary_easy"))
        return {
            "provider": provider,
            "summary": summary,
            "signal": _to_signal(parsed.get("signal")),
            "confidence": _to_confidence(parsed.get("confidence")),
            "key_points": [str(item) for item in key_points],
            "bullish_view": bullish_view,
            "bearish_view": bearish_view,
            "easy_summary": easy_summary,
            "normalized_by": strategy,
            "raw": raw_text,
        }

    return {
        "provider": provider,
        "summary": raw_text.strip()[:240],
        "signal": "neutral",
        "confidence": 0.5,
        "key_points": [],
        "bullish_view": "",
        "bearish_view": "",
        "easy_summary": "",
        "normalized_by": strategy,
        "raw": raw_text,
    }

