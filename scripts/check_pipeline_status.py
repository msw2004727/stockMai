from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default)).strip()


def _post_json(url: str, payload: dict, headers: dict[str, str], timeout: int) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url=url,
        method="POST",
        data=body,
        headers={"Content-Type": "application/json", **headers},
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_json(url: str, headers: dict[str, str], timeout: int) -> dict:
    request = Request(url=url, method="GET", headers=headers)
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _ensure_token(base_url: str, user_id: str, expires_minutes: int, timeout: int) -> str:
    data = _post_json(
        f"{base_url}/auth/token",
        payload={"user_id": user_id, "expires_minutes": expires_minutes},
        headers={},
        timeout=timeout,
    )
    token = str(data.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("token response missing access_token")
    return token


def main() -> int:
    base_url = _env("BACKEND_BASE_URL")
    user_id = _env("PIPELINE_MONITOR_USER_ID", "pipeline-monitor-user")
    expires_minutes = int(_env("PIPELINE_EXPIRES_MINUTES", "30") or "30")
    timeout = int(_env("PIPELINE_TIMEOUT_SECONDS", "30") or "30")
    allow_warn = _env("ALLOW_WARN_STATUS", "false").lower() == "true"

    if not base_url:
        print("Error: missing BACKEND_BASE_URL")
        return 1

    base_url = base_url.rstrip("/")
    if not base_url.startswith("http"):
        print("Error: BACKEND_BASE_URL must start with http/https")
        return 1

    try:
        token = _ensure_token(base_url, user_id=user_id, expires_minutes=expires_minutes, timeout=timeout)
        headers = {"Authorization": f"Bearer {token}"}

        pipeline = _get_json(f"{base_url}/stocks/pipeline/status", headers=headers, timeout=timeout)
        movers = _get_json(f"{base_url}/stocks/movers?limit=6", headers=headers, timeout=timeout)

        summary = {
            "pipeline_status": pipeline.get("status"),
            "pipeline_is_healthy": pipeline.get("is_healthy"),
            "pipeline_latest_trade_date": pipeline.get("latest_trade_date"),
            "pipeline_coverage_ratio": pipeline.get("coverage_ratio"),
            "movers_as_of_date": movers.get("as_of_date"),
            "movers_coverage_ratio": movers.get("coverage_ratio"),
        }
        print(json.dumps(summary, ensure_ascii=False))

        status = str(pipeline.get("status") or "").lower()
        is_healthy = bool(pipeline.get("is_healthy"))
        if is_healthy:
            return 0
        if allow_warn and status == "warn":
            return 0

        print(f"Error: unhealthy pipeline status ({status})")
        return 1
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        print(f"HTTPError: {exc.code} {body}")
        return 1
    except URLError as exc:
        print(f"URLError: {exc}")
        return 1
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
