from time import perf_counter

import psycopg
import redis


def _to_ms(start: float) -> int:
    return int((perf_counter() - start) * 1000)


def check_postgres(database_url: str) -> dict:
    started = perf_counter()
    try:
        with psycopg.connect(database_url, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        return {"ok": True, "latency_ms": _to_ms(started)}
    except Exception as exc:
        return {"ok": False, "latency_ms": _to_ms(started), "error": str(exc)}


def check_redis(redis_url: str) -> dict:
    started = perf_counter()
    try:
        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=3,
            socket_timeout=3,
            decode_responses=True,
        )
        client.ping()
        return {"ok": True, "latency_ms": _to_ms(started)}
    except Exception as exc:
        return {"ok": False, "latency_ms": _to_ms(started), "error": str(exc)}

