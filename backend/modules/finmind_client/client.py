from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

FINMIND_DATA_URL = "https://api.finmindtrade.com/api/v4/data"


@dataclass(slots=True)
class FinMindClientResult:
    ok: bool
    dataset: str
    rows: list[dict]
    status_code: int
    message: str


class FinMindClient:
    def __init__(self, token: str, timeout_seconds: int = 10):
        self.token = str(token or "").strip()
        self.timeout_seconds = max(int(timeout_seconds), 3)

    def fetch_dataset(
        self,
        *,
        dataset: str,
        symbol: str,
        start_date: str = "",
        end_date: str = "",
    ) -> FinMindClientResult:
        if not self.token:
            return FinMindClientResult(
                ok=False,
                dataset=dataset,
                rows=[],
                status_code=401,
                message="FINMIND_TOKEN not configured.",
            )

        last_error = FinMindClientResult(
            ok=False,
            dataset=dataset,
            rows=[],
            status_code=503,
            message="FinMind request failed.",
        )

        query_candidates = self._query_candidates(
            dataset=dataset,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )

        for query in query_candidates:
            payload, status_code, error_message = self._fetch_payload(query)
            if payload is None:
                last_error = FinMindClientResult(
                    ok=False,
                    dataset=dataset,
                    rows=[],
                    status_code=status_code,
                    message=error_message,
                )
                continue

            status_raw = payload.get("status")
            msg = str(payload.get("msg") or payload.get("message") or "").strip()
            normalized_status = _to_int(status_raw)
            if normalized_status == 200:
                rows = payload.get("data")
                if not isinstance(rows, list):
                    rows = []
                normalized_rows = [row for row in rows if isinstance(row, dict)]
                return FinMindClientResult(
                    ok=True,
                    dataset=dataset,
                    rows=normalized_rows,
                    status_code=200,
                    message=msg,
                )

            current_status = normalized_status or status_code or 500
            current_message = msg or f"FinMind status={status_raw}"
            last_error = FinMindClientResult(
                ok=False,
                dataset=dataset,
                rows=[],
                status_code=current_status,
                message=current_message,
            )

            # If API accepted request shape, no need to retry other query variants.
            if current_status not in {400, 404}:
                break

        return last_error

    def _query_candidates(
        self,
        *,
        dataset: str,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, str]]:
        base = {
            "dataset": dataset,
            "data_id": symbol,
            "token": self.token,
        }
        date_params = {}
        if start_date:
            date_params["start_date"] = start_date
        if end_date:
            date_params["end_date"] = end_date

        out = []
        out.append({**base, **date_params})
        out.append(base)
        # Some datasets in older examples use stock_id instead of data_id.
        out.append({**{k: v for k, v in base.items() if k != "data_id"}, "stock_id": symbol, **date_params})
        out.append({**{k: v for k, v in base.items() if k != "data_id"}, "stock_id": symbol})

        unique: list[dict[str, str]] = []
        seen: set[str] = set()
        for params in out:
            key = json.dumps(params, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            unique.append(params)
        return unique

    def _fetch_payload(self, query: dict[str, str]) -> tuple[dict | None, int, str]:
        try:
            encoded = urlencode(query)
            with urlopen(f"{FINMIND_DATA_URL}?{encoded}", timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                payload = json.loads(raw)
                return payload if isinstance(payload, dict) else {}, int(response.getcode() or 200), ""
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            try:
                payload = json.loads(body)
                if isinstance(payload, dict):
                    return payload, int(exc.code), ""
            except Exception:
                pass
            return None, int(exc.code), body or str(exc)
        except URLError as exc:
            return None, 503, str(exc.reason)
        except Exception as exc:
            return None, 500, str(exc)


def _to_int(raw: object) -> int | None:
    try:
        return int(raw)
    except Exception:
        return None
