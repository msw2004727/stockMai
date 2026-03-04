from __future__ import annotations

from datetime import date, timedelta

from backend.modules.finmind_client import FinMindClient, FinMindClientResult

from .intel_constants import DEEP_DATASETS, FINANCIAL_DATASETS, LOOKBACK_DAYS, OVERVIEW_DATASETS


def build_finmind_client(token: str) -> FinMindClient:
    return FinMindClient(token=token, timeout_seconds=12)


def fetch_overview_blocks(client: FinMindClient, symbol: str) -> dict[str, dict]:
    return {
        key: _fetch_first_available(
            client=client,
            symbol=symbol,
            dataset_candidates=dataset_candidates,
            lookback_days=LOOKBACK_DAYS.get(key, 180),
            block_key=key,
        )
        for key, dataset_candidates in OVERVIEW_DATASETS.items()
    }


def fetch_deep_blocks(client: FinMindClient, symbol: str) -> dict[str, dict]:
    out = {
        key: _fetch_first_available(
            client=client,
            symbol=symbol,
            dataset_candidates=dataset_candidates,
            lookback_days=LOOKBACK_DAYS.get(key, 365),
            block_key=key,
        )
        for key, dataset_candidates in DEEP_DATASETS.items()
    }
    out["financial_statements"] = _fetch_financial_sections(client=client, symbol=symbol)
    return out


def _fetch_financial_sections(client: FinMindClient, symbol: str) -> dict:
    sections: list[dict] = []
    status = "empty"
    message = ""
    last_code = 200
    last_dataset = ""
    best_data_as_of = ""

    for section_key, dataset_candidates in FINANCIAL_DATASETS.items():
        result = _fetch_first_available(
            client=client,
            symbol=symbol,
            dataset_candidates=dataset_candidates,
            lookback_days=LOOKBACK_DAYS["financial"],
            block_key=section_key,
        )
        section_rows = list(result.get("rows") or [])
        sections.append(
            {
                "kind": section_key,
                "dataset": str(result.get("dataset") or ""),
                "availability": {
                    "status": str(result.get("status") or "empty"),
                    "message": str(result.get("message") or ""),
                },
                "data_as_of": str(result.get("data_as_of") or ""),
                "rows": section_rows,
            }
        )

        current_status = str(result.get("status") or "empty")
        if current_status == "ok":
            status = "ok"
        elif status != "ok" and current_status == "restricted":
            status = "restricted"
        elif status not in {"ok", "restricted"} and current_status == "error":
            status = "error"

        if not message and result.get("message"):
            message = str(result.get("message"))
        last_code = int(result.get("status_code") or last_code)
        last_dataset = str(result.get("dataset") or last_dataset)
        data_as_of = str(result.get("data_as_of") or "")
        if data_as_of and data_as_of > best_data_as_of:
            best_data_as_of = data_as_of

    return {
        "status": status,
        "message": message,
        "status_code": last_code,
        "dataset": last_dataset,
        "data_as_of": best_data_as_of,
        "rows": [],
        "sections": sections,
    }


def _fetch_first_available(
    *,
    client: FinMindClient,
    symbol: str,
    dataset_candidates: list[str],
    lookback_days: int,
    block_key: str,
) -> dict:
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=max(int(lookback_days), 30))).isoformat()

    had_success = False
    had_restricted = False
    had_error = False
    best_empty_dataset = ""
    last_error_message = ""
    last_error_code = 500

    for dataset in dataset_candidates:
        result = client.fetch_dataset(
            dataset=dataset,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )

        if result.ok:
            had_success = True
            if result.rows:
                return {
                    "key": block_key,
                    "status": "ok",
                    "message": "",
                    "status_code": 200,
                    "dataset": result.dataset,
                    "data_as_of": _infer_data_as_of(result.rows),
                    "rows": result.rows,
                }
            if not best_empty_dataset:
                best_empty_dataset = result.dataset
            continue

        if _is_restricted(result):
            had_restricted = True
        else:
            had_error = True
        last_error_message = result.message
        last_error_code = result.status_code

    if had_success:
        return {
            "key": block_key,
            "status": "empty",
            "message": "Dataset returned no rows.",
            "status_code": 200,
            "dataset": best_empty_dataset or (dataset_candidates[0] if dataset_candidates else ""),
            "data_as_of": "",
            "rows": [],
        }

    if had_restricted and not had_error:
        return {
            "key": block_key,
            "status": "restricted",
            "message": last_error_message or "Dataset requires additional FinMind permission.",
            "status_code": last_error_code or 403,
            "dataset": dataset_candidates[0] if dataset_candidates else "",
            "data_as_of": "",
            "rows": [],
        }

    return {
        "key": block_key,
        "status": "error",
        "message": last_error_message or "FinMind dataset unavailable.",
        "status_code": last_error_code or 503,
        "dataset": dataset_candidates[0] if dataset_candidates else "",
        "data_as_of": "",
        "rows": [],
    }


def _infer_data_as_of(rows: list[dict]) -> str:
    latest = ""
    for row in rows:
        if not isinstance(row, dict):
            continue
        current = _pick_date_text(row)
        if current and current > latest:
            latest = current
    return latest


def _pick_date_text(row: dict) -> str:
    for key in (
        "date",
        "Date",
        "trade_date",
        "data_date",
        "stat_date",
        "month",
        "ym",
        "year_month",
    ):
        raw = str(row.get(key) or "").strip()
        if raw:
            return raw

    year = str(row.get("year") or "").strip()
    month = str(row.get("month") or "").strip()
    if year and month and year.isdigit() and month.isdigit():
        return f"{int(year):04d}-{int(month):02d}"
    return ""


def _is_restricted(result: FinMindClientResult) -> bool:
    if int(result.status_code or 0) in {401, 402, 403}:
        return True
    message = str(result.message or "").lower()
    keywords = ("sponsor", "permission", "vip", "authorize", "forbidden", "權限")
    return any(keyword in message for keyword in keywords)
