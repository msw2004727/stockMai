import unittest
from types import SimpleNamespace
from unittest.mock import patch

import redis
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.app.auth import (
    TokenValidationError,
    check_daily_limit,
    create_access_token,
    decode_access_token,
    get_current_user,
)


class _FakeRedis:
    def __init__(self):
        self.store = {}
        self.expire_calls = []

    def incr(self, key: str) -> int:
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key: str, ttl: int) -> bool:
        self.expire_calls.append((key, ttl))
        return True


class _BrokenRedis:
    def incr(self, _key: str) -> int:
        raise redis.RedisError("redis down")

    def expire(self, _key: str, _ttl: int) -> bool:
        return True


def _settings(**overrides):
    base = {
        "jwt_secret": "test-secret",
        "jwt_expire_minutes": 60,
        "api_daily_limit": 2,
        "redis_url": "redis://localhost:6379/0",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class AuthTest(unittest.TestCase):
    @patch("backend.app.auth.get_settings", return_value=_settings())
    def test_create_and_decode_access_token(self, _mock_settings):
        token = create_access_token("user-1", expires_minutes=5)
        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], "user-1")
        self.assertIn("exp", payload)

    @patch("backend.app.auth.get_settings", return_value=_settings())
    def test_decode_access_token_rejects_tampered_signature(self, _mock_settings):
        token = create_access_token("user-1", expires_minutes=5)
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
        with self.assertRaises(TokenValidationError):
            decode_access_token(tampered)

    @patch("backend.app.auth.get_settings", return_value=_settings())
    def test_get_current_user_rejects_missing_credentials(self, _mock_settings):
        with self.assertRaises(HTTPException) as ctx:
            get_current_user(credentials=None)
        self.assertEqual(ctx.exception.status_code, 401)

    @patch("backend.app.auth.get_settings", return_value=_settings())
    def test_get_current_user_accepts_valid_token(self, _mock_settings):
        token = create_access_token("user-1", expires_minutes=5)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        user = get_current_user(credentials=credentials)
        self.assertEqual(user["user_id"], "user-1")

    @patch("backend.app.auth.get_redis_client", return_value=_FakeRedis())
    @patch("backend.app.auth.get_settings", return_value=_settings(api_daily_limit=2))
    def test_check_daily_limit_blocks_when_over_limit(self, _mock_settings, _mock_redis):
        check_daily_limit("user-1", "stocks_quote")
        check_daily_limit("user-1", "stocks_quote")
        with self.assertRaises(HTTPException) as ctx:
            check_daily_limit("user-1", "stocks_quote")
        self.assertEqual(ctx.exception.status_code, 429)

    @patch("backend.app.auth.get_redis_client", return_value=_BrokenRedis())
    @patch("backend.app.auth.get_settings", return_value=_settings())
    def test_check_daily_limit_returns_503_when_redis_down(self, _mock_settings, _mock_redis):
        with self.assertRaises(HTTPException) as ctx:
            check_daily_limit("user-1", "stocks_quote")
        self.assertEqual(ctx.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
