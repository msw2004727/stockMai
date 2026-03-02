from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

import redis

from .provider_client import ProviderCallError

PRICING_PER_M_TOKENS = {
    "claude": {"input": 5.0, "output": 25.0},
    "gpt5": {"input": 1.75, "output": 14.0},
    "grok": {"input": 0.2, "output": 0.5},
    "gemini": {"input": 2.0, "output": 12.0},
}


class CostTracker:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url.strip()
        self._redis_client: redis.Redis | None = None
        self._memory_totals: dict[str, float] = {}

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 1
        return max(len(text) // 4, 1)

    def estimate_request_cost_usd(self, provider: str, input_tokens: int, output_tokens: int) -> float:
        pricing = PRICING_PER_M_TOKENS.get(provider, {"input": 2.0, "output": 12.0})
        input_cost = (max(input_tokens, 0) / 1_000_000.0) * pricing["input"]
        output_cost = (max(output_tokens, 0) / 1_000_000.0) * pricing["output"]
        return input_cost + output_cost

    def get_daily_total_usd(self, user_id: str) -> float:
        key = self._daily_key(user_id)
        client = self._get_redis_client()
        if client is not None:
            try:
                raw = client.get(key)
                return float(raw or 0.0)
            except redis.RedisError:
                pass
        return float(self._memory_totals.get(key, 0.0))

    def check_budget_before_request(self, user_id: str, daily_budget_usd: float) -> None:
        if daily_budget_usd <= 0:
            return
        total = self.get_daily_total_usd(user_id)
        if total >= daily_budget_usd:
            raise ProviderCallError("AI daily budget exceeded.", retryable=False)

    def record_usage(
        self,
        user_id: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        daily_budget_usd: float,
    ) -> dict:
        key = self._daily_key(user_id)
        request_cost = self.estimate_request_cost_usd(provider, input_tokens, output_tokens)
        daily_total = self._increment_daily_total(key=key, delta=request_cost)
        budget_exceeded = daily_total > daily_budget_usd if daily_budget_usd > 0 else False
        return {
            "provider": provider,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "request_cost_usd": round(request_cost, 8),
            "daily_total_usd": round(daily_total, 8),
            "daily_budget_usd": round(daily_budget_usd, 8),
            "budget_exceeded": budget_exceeded,
        }

    def _increment_daily_total(self, key: str, delta: float) -> float:
        client = self._get_redis_client()
        if client is not None:
            try:
                total = float(client.incrbyfloat(key, delta))
                client.expire(key, self._seconds_until_next_utc_day())
                return total
            except redis.RedisError:
                pass

        current = float(self._memory_totals.get(key, 0.0))
        updated = current + delta
        self._memory_totals[key] = updated
        return updated

    def _get_redis_client(self) -> redis.Redis | None:
        if not self.redis_url:
            return None
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2,
                )
            except Exception:
                return None
        return self._redis_client

    def _daily_key(self, user_id: str) -> str:
        return f"ai_cost:{self._utc_day()}:{user_id}"

    @staticmethod
    def _utc_day() -> str:
        return datetime.now(timezone.utc).date().isoformat()

    @staticmethod
    def _seconds_until_next_utc_day() -> int:
        now = datetime.now(timezone.utc)
        tomorrow = now.date() + timedelta(days=1)
        next_midnight = datetime.combine(tomorrow, time.min, tzinfo=timezone.utc)
        return max(int((next_midnight - now).total_seconds()), 1)
