import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.strategy.service import (
    StrategyDataUnavailableError,
    StrategySymbolNotFoundError,
    build_strategy_decision,
)


def _sample_history(days: int = 60) -> dict:
    series = []
    for idx in range(days):
        base = 100.0 + idx
        series.append(
            {
                "date": f"2026-02-{(idx % 28) + 1:02d}",
                "open": base,
                "high": base + 2.0,
                "low": base - 2.0,
                "close": base + 1.0,
                "change": 1.0,
                "volume": 100000 + (idx * 100),
            }
        )
    return {
        "symbol": "2330",
        "days": len(series),
        "series": series,
        "source": "integration",
        "as_of_date": series[-1]["date"],
    }


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        ai_default_providers="claude,gpt5,grok,deepseek",
        ai_provider_weights="claude=1.0,gpt5=1.0,grok=1.0,deepseek=1.0",
        ai_timeout_seconds=15,
        ai_retry_count=1,
        ai_retry_backoff_seconds=0.1,
        ai_daily_budget_usd=5.0,
        redis_url="redis://localhost:6379/0",
        anthropic_api_key="",
        claude_model="claude-opus-4-6",
        openai_api_key="",
        gpt_model="gpt-5.2",
        grok_api_key="",
        grok_model="grok-4.1-fast",
        deepseek_api_key="",
        deepseek_model="deepseek-chat",
    )


class StrategyServiceTest(unittest.TestCase):
    @patch("backend.app.strategy.service.run_ai_consensus")
    @patch("backend.app.strategy.service.get_history")
    @patch("backend.app.strategy.service.get_settings")
    def test_build_strategy_decision_success(self, mock_get_settings, mock_get_history, mock_run_ai):
        mock_get_settings.return_value = _settings()
        mock_get_history.return_value = _sample_history()
        mock_run_ai.return_value = {
            "consensus": {
                "signal": "bullish",
                "confidence": 0.72,
                "summary": "Trend and momentum are aligned.",
                "source_provider": "claude",
                "signal_scores": {"bullish": 1.0, "bearish": 0.0, "neutral": 0.0},
            },
            "results": [{"provider": "claude", "ok": True, "data": {"signal": "bullish", "confidence": 0.72}}],
            "fallback_used": False,
            "cost": {"enabled": True, "total_request_cost_usd": 0.0001},
        }

        result = asyncio.run(
            build_strategy_decision(
                symbol="2330",
                user_id="strategy-user",
                user_prompt="focus on 2-week trend",
                providers=["claude"],
                lookback_days=60,
                sentiment_window_days=20,
            )
        )

        self.assertEqual(result["symbol"], "2330")
        self.assertIn(result["action"], {"buy", "hold", "sell"})
        self.assertIn("confidence", result)
        self.assertIn("risk_level", result)
        self.assertIn("reasons", result)
        self.assertIn("components", result)
        self.assertIn("indicator_context", result)
        self.assertIn("sentiment_context", result)
        self.assertIn("ai_consensus", result)

    @patch("backend.app.strategy.service.get_settings")
    def test_build_strategy_decision_raises_data_unavailable(self, mock_get_settings):
        from backend.app.stocks.service import DataUnavailableError

        mock_get_settings.return_value = _settings()
        with patch("backend.app.strategy.service.get_history", side_effect=DataUnavailableError("market down")):
            with self.assertRaises(StrategyDataUnavailableError):
                asyncio.run(build_strategy_decision(symbol="2330", user_id="u1"))

    @patch("backend.app.strategy.service.get_settings")
    def test_build_strategy_decision_raises_symbol_not_found(self, mock_get_settings):
        from backend.app.stocks.service import SymbolNotFoundError

        mock_get_settings.return_value = _settings()
        with patch("backend.app.strategy.service.get_history", side_effect=SymbolNotFoundError("missing")):
            with self.assertRaises(StrategySymbolNotFoundError):
                asyncio.run(build_strategy_decision(symbol="9999", user_id="u1"))


if __name__ == "__main__":
    unittest.main()

