from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

TAIPEI_TZ = ZoneInfo("Asia/Taipei")
TRADING_OPEN = time(9, 0, 0)
TRADING_CLOSE = time(13, 30, 0)


def parse_holiday_dates(raw: str) -> set[date]:
    values = [item.strip() for item in str(raw or "").split(",") if item.strip()]
    parsed: set[date] = set()
    for value in values:
        try:
            parsed.add(date.fromisoformat(value))
        except Exception:
            continue
    return parsed


def current_taipei_now() -> datetime:
    return datetime.now(TAIPEI_TZ)


def infer_market_state(
    *,
    market_state: str,
    as_of_date: str,
    quote_time: str,
    is_realtime: bool,
    holiday_dates: set[date],
    now_taipei: datetime | None = None,
) -> str:
    now = now_taipei or current_taipei_now()
    today = now.date()
    parsed_as_of = _parse_iso_date(as_of_date)
    base_state = str(market_state or "").strip().lower()

    if not is_trading_day(today, holiday_dates):
        return "market_holiday"

    if now.time() < TRADING_OPEN:
        return "pre_open"
    if now.time() > TRADING_CLOSE:
        return "daily_close"

    # During session: stale day quote must not show as trading.
    if parsed_as_of and parsed_as_of != today:
        return "daily_close"

    if is_realtime and _is_quote_time_in_session(quote_time, today):
        return "trading"
    if base_state == "trading":
        return "trading"

    # Non-realtime source in session is usually delayed/day-level data.
    return "daily_close"


def is_trading_day(target: date, holiday_dates: set[date]) -> bool:
    if target.weekday() >= 5:
        return False
    return target not in holiday_dates


def previous_trading_day(reference_date: date, holiday_dates: set[date]) -> date:
    cursor = reference_date
    while True:
        cursor = cursor.fromordinal(cursor.toordinal() - 1)
        if is_trading_day(cursor, holiday_dates):
            return cursor


def _parse_iso_date(raw: str) -> date | None:
    try:
        return date.fromisoformat(str(raw or "").strip())
    except Exception:
        return None


def _is_quote_time_in_session(raw: str, today: date) -> bool:
    text = str(raw or "").strip()
    if not text:
        return False

    # Expected format: YYYY-MM-DD HH:MM:SS
    parts = text.split(" ")
    if len(parts) != 2:
        return False
    parsed_date = _parse_iso_date(parts[0])
    if parsed_date != today:
        return False

    time_part = parts[1]
    try:
        parsed_time = datetime.strptime(time_part, "%H:%M:%S").time()
    except Exception:
        return False
    return TRADING_OPEN <= parsed_time <= TRADING_CLOSE
