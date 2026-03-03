import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

from backend.app.stocks.market_clock import infer_market_state, previous_trading_day


class MarketClockTest(unittest.TestCase):
    def test_returns_trading_during_session_with_realtime_quote(self):
        now = datetime(2026, 3, 2, 10, 30, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        state = infer_market_state(
            market_state="trading",
            as_of_date="2026-03-02",
            quote_time="2026-03-02 10:29:40",
            is_realtime=True,
            holiday_dates=set(),
            now_taipei=now,
        )
        self.assertEqual(state, "trading")

    def test_returns_daily_close_at_night(self):
        now = datetime(2026, 3, 2, 20, 10, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        state = infer_market_state(
            market_state="trading",
            as_of_date="2026-03-02",
            quote_time="2026-03-02 13:25:01",
            is_realtime=True,
            holiday_dates=set(),
            now_taipei=now,
        )
        self.assertEqual(state, "daily_close")

    def test_returns_market_holiday_for_weekend(self):
        now = datetime(2026, 3, 1, 10, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))  # Sunday
        state = infer_market_state(
            market_state="unknown",
            as_of_date="2026-03-01",
            quote_time="2026-03-01 10:00:00",
            is_realtime=False,
            holiday_dates=set(),
            now_taipei=now,
        )
        self.assertEqual(state, "market_holiday")

    def test_returns_market_holiday_for_configured_holiday(self):
        now = datetime(2026, 10, 1, 10, 0, 0, tzinfo=ZoneInfo("Asia/Taipei"))
        state = infer_market_state(
            market_state="unknown",
            as_of_date="2026-10-01",
            quote_time="2026-10-01 10:00:00",
            is_realtime=False,
            holiday_dates={date(2026, 10, 1)},
            now_taipei=now,
        )
        self.assertEqual(state, "market_holiday")

    def test_previous_trading_day_skips_weekend(self):
        # Monday -> previous Friday
        self.assertEqual(
            previous_trading_day(date(2026, 3, 2), holiday_dates=set()),
            date(2026, 2, 27),
        )

    def test_previous_trading_day_skips_holiday(self):
        # Tuesday with Monday holiday -> previous Friday
        self.assertEqual(
            previous_trading_day(date(2026, 3, 3), holiday_dates={date(2026, 3, 2)}),
            date(2026, 2, 27),
        )


if __name__ == "__main__":
    unittest.main()
