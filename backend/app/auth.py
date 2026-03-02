from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, time, timedelta, timezone
from functools import lru_cache

import redis
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .config import get_settings


class TokenValidationError(Exception):
    pass


class TokenRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    expires_minutes: int = Field(60, ge=1, le=1440)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_minutes: int


router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(f"{raw}{padding}".encode("ascii"))


def _sign(signing_input: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    ttl = expires_minutes if expires_minutes is not None else settings.jwt_expire_minutes
    now = _utc_now()
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl)).timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = _sign(signing_input, settings.jwt_secret)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    parts = token.split(".")
    if len(parts) != 3:
        raise TokenValidationError("Invalid token format")

    encoded_header, encoded_payload, signature = parts
    signing_input = f"{encoded_header}.{encoded_payload}"
    expected_signature = _sign(signing_input, settings.jwt_secret)
    if not hmac.compare_digest(signature, expected_signature):
        raise TokenValidationError("Invalid token signature")

    try:
        header = json.loads(_b64url_decode(encoded_header))
        payload = json.loads(_b64url_decode(encoded_payload))
    except Exception as exc:
        raise TokenValidationError("Invalid token payload") from exc

    if header.get("alg") != "HS256":
        raise TokenValidationError("Unsupported token algorithm")

    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise TokenValidationError("Token missing exp")
    if exp <= int(_utc_now().timestamp()):
        raise TokenValidationError("Token expired")

    return payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenValidationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject")

    return {"user_id": user_id, "exp": payload["exp"]}


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_timeout=2,
        socket_connect_timeout=2,
    )


def _seconds_until_next_utc_day() -> int:
    now = _utc_now()
    tomorrow = now.date() + timedelta(days=1)
    next_midnight = datetime.combine(tomorrow, time.min, tzinfo=timezone.utc)
    return max(int((next_midnight - now).total_seconds()), 1)


def check_daily_limit(user_id: str, scope: str) -> dict:
    settings = get_settings()
    limit = settings.api_daily_limit
    day_key = _utc_now().date().isoformat()
    redis_key = f"rate:{scope}:{day_key}:{user_id}"

    try:
        client = get_redis_client()
        used = int(client.incr(redis_key))
        if used == 1:
            client.expire(redis_key, _seconds_until_next_utc_day())
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail="Rate limiter unavailable") from exc

    if used > limit:
        raise HTTPException(status_code=429, detail="Daily quota exceeded")

    return {"limit": limit, "used": used, "remaining": max(limit - used, 0)}


def enforce_rate_limit(scope: str):
    def _dependency(user: dict = Depends(get_current_user)) -> dict:
        return check_daily_limit(user_id=user["user_id"], scope=scope)

    return _dependency


@router.post("/token", response_model=TokenResponse)
def issue_token(body: TokenRequest) -> TokenResponse:
    token = create_access_token(body.user_id, expires_minutes=body.expires_minutes)
    return TokenResponse(access_token=token, expires_minutes=body.expires_minutes)

