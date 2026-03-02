from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import time
from functools import lru_cache

import redis


class QuoteRateLimitExceeded(Exception):
    pass


_memory_quote_cache: dict[str, tuple[float, dict]] = {}
_memory_rate_guard: dict[str, tuple[int, float]] = {}


@lru_cache(maxsize=8)
def _get_redis_client(redis_url: str) -> redis.Redis | None:
    if not redis_url.strip():
        return None
    try:
        return redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=1,
            socket_connect_timeout=1,
        )
    except Exception:
        return None


def load_short_quote_cache(redis_url: str, symbol: str) -> dict | None:
    key = _cache_key(symbol)
    client = _get_redis_client(redis_url)
    if client is not None:
        try:
            raw = client.get(key)
            if not raw:
                return None
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    now = time.time()
    entry = _memory_quote_cache.get(key)
    if not entry:
        return None
    expire_ts, payload = entry
    if now >= expire_ts:
        _memory_quote_cache.pop(key, None)
        return None
    return dict(payload)


def save_short_quote_cache(redis_url: str, symbol: str, payload: dict, ttl_seconds: int) -> None:
    ttl = max(int(ttl_seconds), 1)
    key = _cache_key(symbol)
    body = json.dumps(payload, ensure_ascii=False)
    client = _get_redis_client(redis_url)
    if client is not None:
        try:
            client.setex(key, ttl, body)
            return
        except Exception:
            pass

    _memory_quote_cache[key] = (time.time() + ttl, dict(payload))


def enforce_quote_rate_guard(
    redis_url: str,
    symbol: str,
    max_requests: int,
    window_seconds: int,
) -> dict:
    limit = max(int(max_requests), 1)
    window = max(int(window_seconds), 1)
    key = _rate_guard_key(symbol=symbol, window_seconds=window)

    used: int
    client = _get_redis_client(redis_url)
    if client is not None:
        try:
            used = int(client.incr(key))
            if used == 1:
                client.expire(key, window + 1)
        except Exception:
            used = _increment_memory_rate_guard(key=key, window_seconds=window)
    else:
        used = _increment_memory_rate_guard(key=key, window_seconds=window)

    if used > limit:
        raise QuoteRateLimitExceeded(
            f"Quote rate limit exceeded (max {limit}/{window}s). Please retry shortly."
        )

    return {
        "limit": limit,
        "used": used,
        "window_seconds": window,
        "remaining": max(limit - used, 0),
    }


def _increment_memory_rate_guard(key: str, window_seconds: int) -> int:
    now = time.time()
    entry = _memory_rate_guard.get(key)
    if not entry:
        _memory_rate_guard[key] = (1, now + window_seconds + 1)
        return 1

    used, expire_ts = entry
    if now >= expire_ts:
        _memory_rate_guard[key] = (1, now + window_seconds + 1)
        return 1

    used += 1
    _memory_rate_guard[key] = (used, expire_ts)
    return used


def _cache_key(symbol: str) -> str:
    return f"quote:short:{symbol}"


def _rate_guard_key(symbol: str, window_seconds: int) -> str:
    now = datetime.now(timezone.utc)
    bucket = int(now.timestamp()) // window_seconds
    bucket_start = datetime.fromtimestamp(bucket * window_seconds, tz=timezone.utc)
    bucket_tag = bucket_start.strftime("%Y%m%d%H%M%S")
    return f"quote:guard:{symbol}:{window_seconds}:{bucket_tag}"
