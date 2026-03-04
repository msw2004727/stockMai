from __future__ import annotations

from datetime import date, timedelta

from backend.modules.finmind_client import FinMindClient, FinMindClientResult

from .intel_constants import DEEP_DATASETS, FINANCIAL_DATASETS, LOOKBACK_DAYS, OVERVIEW_DATASETS
from .intel_official_provider import fetch_official_deep_blocks, fetch_official_overview_blocks


def build_finmind_client(token: str) -> FinMindClient:
    return FinMindClient(token=token, timeout_seconds=12)


def fetch_overview_blocks(client: FinMindClient, symbol: str) -> dict[str, dict]:
    official_blocks = fetch_official_overview_blocks(symbol)
    out: dict[str, dict] = {}
    for key, dataset_candidates in OVERVIEW_DATASETS.items():
        official_block = _normalize_block(official_blocks.get(key), key=key, default_source="official_free_api")
        if _is_ok_status(official_block):
            out[key] = _with_source_priority(official_block, "official_primary")
            continue

        finmind_block = _fetch_first_available(
            client=client,
            symbol=symbol,
            dataset_candidates=dataset_candidates,
            lookback_days=LOOKBACK_DAYS.get(key, 180),
            block_key=key,
        )
        out[key] = _merge_preferred_block(official_block, finmind_block)
    return out


def fetch_deep_blocks(client: FinMindClient, symbol: str) -> dict[str, dict]:
    official_blocks = fetch_official_deep_blocks(symbol)
    out: dict[str, dict] = {}
    for key, dataset_candidates in DEEP_DATASETS.items():
        official_block = _normalize_block(official_blocks.get(key), key=key, default_source="official_free_api")
        if _is_ok_status(official_block):
            out[key] = _with_source_priority(official_block, "official_primary")
            continue

        finmind_block = _fetch_first_available(
            client=client,
            symbol=symbol,
            dataset_candidates=dataset_candidates,
            lookback_days=LOOKBACK_DAYS.get(key, 365),
            block_key=key,
        )
        out[key] = _merge_preferred_block(official_block, finmind_block)

    official_financial = _normalize_block(
        official_blocks.get("financial_statements"),
        key="financial_statements",
        default_source="official_free_api",
    )
    if _is_ok_status(official_financial):
        out["financial_statements"] = _with_source_priority(official_financial, "official_primary")
    else:
        finmind_financial = _fetch_financial_sections(client=client, symbol=symbol)
        out["financial_statements"] = _merge_preferred_block(official_financial, finmind_financial)

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
                "source": str(result.get("source") or "finmind"),
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
        "key": "financial_statements",
        "status": status,
        "message": message,
        "status_code": last_code,
        "dataset": last_dataset,
        "source": "finmind",
        "source_priority": "finmind_primary",
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
                    "source": "finmind",
                    "source_priority": "finmind_primary",
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
            "source": "finmind",
            "source_priority": "finmind_primary",
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
            "source": "finmind",
            "source_priority": "finmind_primary",
            "data_as_of": "",
            "rows": [],
        }

    return {
        "key": block_key,
        "status": "error",
        "message": last_error_message or "FinMind dataset unavailable.",
        "status_code": last_error_code or 503,
        "dataset": dataset_candidates[0] if dataset_candidates else "",
        "source": "finmind",
        "source_priority": "finmind_primary",
        "data_as_of": "",
        "rows": [],
    }


def _merge_preferred_block(official_block: dict, finmind_block: dict) -> dict:
    if _is_ok_status(finmind_block):
        return _with_source_priority(finmind_block, "finmind_fallback")

    official_score = _status_score(str(official_block.get("status") or "error"))
    finmind_score = _status_score(str(finmind_block.get("status") or "error"))
    if official_score <= finmind_score:
        return _with_source_priority(official_block, "official_primary")
    return _with_source_priority(finmind_block, "finmind_fallback")


def _normalize_block(block: dict | None, *, key: str, default_source: str) -> dict:
    if isinstance(block, dict):
        out = dict(block)
    else:
        out = {}
    out["key"] = str(out.get("key") or key)
    out["status"] = str(out.get("status") or "error")
    out["message"] = str(out.get("message") or "")
    out["status_code"] = int(out.get("status_code") or 503)
    out["dataset"] = str(out.get("dataset") or "")
    out["source"] = str(out.get("source") or default_source)
    out["data_as_of"] = str(out.get("data_as_of") or "")
    out["rows"] = list(out.get("rows") or [])
    if key == "financial_statements":
        out["sections"] = list(out.get("sections") or [])
    return out


def _with_source_priority(block: dict, source_priority: str) -> dict:
    out = dict(block)
    out["source_priority"] = source_priority
    return out


def _is_ok_status(block: dict) -> bool:
    return str(block.get("status") or "").lower() == "ok"


def _status_score(status: str) -> int:
    normalized = str(status or "").lower()
    if normalized == "ok":
        return 0
    if normalized == "empty":
        return 1
    if normalized == "error":
        return 2
    if normalized == "restricted":
        return 3
    return 4


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
    keywords = ("sponsor", "permission", "vip", "authorize", "forbidden", "restricted")
    return any(keyword in message for keyword in keywords)

