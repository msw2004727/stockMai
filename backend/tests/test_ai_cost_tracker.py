import unittest

from backend.modules.ai_gateway.cost_tracker import CostTracker
from backend.modules.ai_gateway.provider_client import ProviderCallError


class AICostTrackerTest(unittest.TestCase):
    def test_estimate_request_cost_usd_uses_provider_pricing(self):
        tracker = CostTracker(redis_url="")
        cost = tracker.estimate_request_cost_usd(provider="claude", input_tokens=1_000_000, output_tokens=0)
        self.assertAlmostEqual(cost, 5.0, places=6)

    def test_record_usage_updates_daily_total_with_memory_fallback(self):
        tracker = CostTracker(redis_url="")
        usage = tracker.record_usage(
            user_id="user-1",
            provider="gpt5",
            input_tokens=1000,
            output_tokens=1000,
            daily_budget_usd=1.0,
        )
        self.assertGreater(usage["request_cost_usd"], 0)
        self.assertGreater(usage["daily_total_usd"], 0)
        self.assertFalse(usage["budget_exceeded"])

    def test_check_budget_before_request_raises_when_exceeded(self):
        tracker = CostTracker(redis_url="")
        tracker.record_usage(
            user_id="budget-user",
            provider="claude",
            input_tokens=1_000_000,
            output_tokens=0,
            daily_budget_usd=10.0,
        )
        with self.assertRaises(ProviderCallError):
            tracker.check_budget_before_request(user_id="budget-user", daily_budget_usd=1.0)

    def test_zero_budget_means_no_enforcement(self):
        tracker = CostTracker(redis_url="")
        tracker.check_budget_before_request(user_id="user-free", daily_budget_usd=0.0)
        usage = tracker.record_usage(
            user_id="user-free",
            provider="deepseek",
            input_tokens=1000,
            output_tokens=1000,
            daily_budget_usd=0.0,
        )
        self.assertFalse(usage["budget_exceeded"])


if __name__ == "__main__":
    unittest.main()

