from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    import httpx
except Exception:  # pragma: no cover - fallback path for restricted local env
    httpx = None

from .provider_client import ProviderCallError


class AsyncJsonHttpClient:
    async def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        timeout_seconds: int,
    ) -> tuple[int, dict[str, Any], str]:
        if httpx is not None:
            try:
                return await self._post_with_httpx(
                    url=url,
                    payload=payload,
                    headers=headers,
                    timeout_seconds=timeout_seconds,
                )
            except ProviderCallError as exc:
                # Some providers intermittently fail on httpx transport in cloud envs.
                # Retry once with urllib to improve compatibility without changing call sites.
                if _should_fallback_to_urllib(exc):
                    return await self._post_with_urllib(
                        url=url,
                        payload=payload,
                        headers=headers,
                        timeout_seconds=timeout_seconds,
                    )
                raise
        return await self._post_with_urllib(
            url=url,
            payload=payload,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

    async def _post_with_httpx(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        timeout_seconds: int,
    ) -> tuple[int, dict[str, Any], str]:
        timeout = httpx.Timeout(float(timeout_seconds))
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
        except Exception as exc:
            retryable = _is_timeout_error(exc) or True
            raise ProviderCallError(
                f"HTTP request failed: {_format_exception_detail(exc)}",
                retryable=retryable,
            ) from exc

        raw_text = response.text or ""
        try:
            data = response.json()
        except ValueError:
            data = {}
        return response.status_code, data, raw_text

    async def _post_with_urllib(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        timeout_seconds: int,
    ) -> tuple[int, dict[str, Any], str]:
        raw_body = json.dumps(payload).encode("utf-8")

        def _request_once():
            req = Request(url, data=raw_body, headers=headers, method="POST")
            with urlopen(req, timeout=timeout_seconds) as response:
                status = response.getcode() or 0
                body = response.read().decode("utf-8")
                return status, body

        try:
            status_code, raw_text = await asyncio.to_thread(_request_once)
        except HTTPError as exc:
            raw_text = exc.read().decode("utf-8", errors="ignore")
            status_code = int(exc.code)
        except Exception as exc:
            raise ProviderCallError(
                f"HTTP request failed: {_format_exception_detail(exc)}",
                retryable=True,
            ) from exc

        try:
            data = json.loads(raw_text) if raw_text else {}
        except ValueError:
            data = {}
        return status_code, data, raw_text


def _is_timeout_error(exc: Exception) -> bool:
    return "timeout" in exc.__class__.__name__.lower()


def _format_exception_detail(exc: Exception) -> str:
    name = exc.__class__.__name__
    message = str(exc or "").strip()
    if message:
        return f"{name}: {message}"
    return name


def _should_fallback_to_urllib(exc: ProviderCallError) -> bool:
    text = str(exc or "").lower()
    if "http request failed" not in text:
        return False
    keywords = (
        "connect",
        "connection",
        "timeout",
        "network",
        "ssl",
        "tls",
        "handshake",
        "name or service",
        "temporary failure",
        "remoteprotocolerror",
        "readerror",
        "writeerror",
    )
    return any(keyword in text for keyword in keywords)

