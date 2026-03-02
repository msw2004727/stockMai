from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_STATUS_ERROR_CODES = {
    401: "unauthorized",
    404: "not_found",
    422: "validation_error",
    429: "rate_limited",
    503: "service_unavailable",
}

_DETAIL_ERROR_CODES = {
    "Missing bearer token": "auth_missing_bearer_token",
    "Token missing subject": "auth_token_missing_subject",
    "Daily quota exceeded": "daily_quota_exceeded",
    "Rate limiter unavailable": "rate_limiter_unavailable",
}


def _default_message(status_code: int) -> str:
    status = HTTPStatus(status_code) if status_code in HTTPStatus._value2member_map_ else None
    return status.phrase if status else "Request failed"


def _resolve_error_code(status_code: int, detail: Any) -> str:
    if isinstance(detail, str):
        mapped = _DETAIL_ERROR_CODES.get(detail)
        if mapped:
            return mapped
    return _STATUS_ERROR_CODES.get(status_code, "http_error")


def _resolve_message(status_code: int, detail: Any) -> str:
    if isinstance(detail, str) and detail.strip():
        return detail
    return _default_message(status_code)


def _build_error_payload(status_code: int, detail: Any, path: str) -> dict:
    message = _resolve_message(status_code, detail)
    return {
        "error_code": _resolve_error_code(status_code, detail),
        "message": message,
        "detail": detail if detail is not None else message,
        "status_code": status_code,
        "path": path,
    }


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    payload = _build_error_payload(
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
    )
    return JSONResponse(status_code=exc.status_code, content=payload, headers=exc.headers)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    payload = _build_error_payload(
        status_code=422,
        detail=exc.errors(),
        path=request.url.path,
    )
    payload["error_code"] = "validation_error"
    payload["message"] = "Invalid request parameters"
    return JSONResponse(status_code=422, content=payload)
