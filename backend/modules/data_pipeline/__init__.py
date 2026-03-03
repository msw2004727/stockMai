__all__ = [
    "fetch_finmind_history",
    "fetch_finmind_quote",
    "load_latest_quote",
    "load_recent_history",
    "upsert_price_snapshots",
    "upsert_price_series",
]


def __getattr__(name: str):
    if name in {"fetch_finmind_history", "fetch_finmind_quote"}:
        from .repository import fetch_finmind_history, fetch_finmind_quote

        mapping = {
            "fetch_finmind_history": fetch_finmind_history,
            "fetch_finmind_quote": fetch_finmind_quote,
        }
        return mapping[name]

    if name in {"load_latest_quote", "load_recent_history", "upsert_price_series"}:
        from .storage import load_latest_quote, load_recent_history, upsert_price_series

        mapping = {
            "load_latest_quote": load_latest_quote,
            "load_recent_history": load_recent_history,
            "upsert_price_series": upsert_price_series,
        }
        return mapping[name]

    if name == "upsert_price_snapshots":
        from .snapshot_storage import upsert_price_snapshots

        return upsert_price_snapshots

    raise AttributeError(name)
