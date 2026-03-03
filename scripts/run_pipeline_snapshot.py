from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
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
    request = Request(
        url=url,
        method="GET",
        headers=headers,
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _ensure_token(base_url: str, user_id: str, expires_minutes: int, timeout: int) -> str:
    payload = {
        "user_id": user_id,
        "expires_minutes": expires_minutes,
    }
    data = _post_json(f"{base_url}/auth/token", payload, headers={}, timeout=timeout)
    token = str(data.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("token response missing access_token")
    return token


def main() -> int:
    base_url = _env("BACKEND_BASE_URL")
    user_id = _env("PIPELINE_USER_ID", "pipeline-cron-user")
    expires_minutes = int(_env("PIPELINE_EXPIRES_MINUTES", "30") or "30")
    max_symbols = int(_env("SNAPSHOT_MAX_SYMBOLS", "3000") or "3000")
    timeout = int(_env("PIPELINE_TIMEOUT_SECONDS", "30") or "30")

    if not base_url:
        print("Error: missing BACKEND_BASE_URL")
        return 1

    base_url = base_url.rstrip("/")
    if not base_url.startswith("http"):
        print("Error: BACKEND_BASE_URL must start with http/https")
        return 1

    try:
        token = _ensure_token(
            base_url=base_url,
            user_id=user_id,
            expires_minutes=expires_minutes,
            timeout=timeout,
        )
        headers = {"Authorization": f"Bearer {token}"}

        query = urlencode({"max_symbols": max_symbols})
        snapshot = _post_json(
            f"{base_url}/stocks/pipeline/snapshot?{query}",
            payload={},
            headers=headers,
            timeout=timeout,
        )
        status = _get_json(
            f"{base_url}/stocks/pipeline/status",
            headers=headers,
            timeout=timeout,
        )

        inserted_rows = int(snapshot.get("inserted_rows") or 0)
        latest_trade_date = str(status.get("latest_trade_date") or "")
        coverage_ratio = status.get("coverage_ratio")
        print(
            json.dumps(
                {
                    "snapshot_ok": bool(snapshot.get("ok")),
                    "inserted_rows": inserted_rows,
                    "trade_date": snapshot.get("trade_date"),
                    "pipeline_status": status.get("status"),
                    "latest_trade_date": latest_trade_date,
                    "coverage_ratio": coverage_ratio,
                },
                ensure_ascii=False,
            )
        )

        if inserted_rows <= 0:
            print("Error: snapshot inserted_rows <= 0")
            return 1
        if not latest_trade_date:
            print("Error: pipeline status missing latest_trade_date")
            return 1
        return 0
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
