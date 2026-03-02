import unittest

from backend.modules.ai_gateway.prompt_builder import build_analysis_prompt, build_provider_prompts


class PromptBuilderTest(unittest.TestCase):
    def test_build_analysis_prompt_without_indicator_context(self):
        prompt = build_analysis_prompt("2330", "focus on momentum")
        self.assertIn("Target symbol: 2330", prompt)
        self.assertIn("User focus: focus on momentum", prompt)
        self.assertNotIn("Technical indicators", prompt)

    def test_build_analysis_prompt_with_indicator_context(self):
        indicator_context = {
            "symbol": "2330",
            "days": 60,
            "history_source": "postgres",
            "as_of_date": "2026-03-02",
            "latest": {
                "sma5": 1010.1,
                "sma20": 1002.5,
                "rsi14": 56.2,
                "macd": 1.2,
                "macd_signal": 1.0,
                "macd_hist": 0.2,
            },
        }
        prompt = build_analysis_prompt("2330", "focus on risk", indicator_context=indicator_context)
        self.assertIn("Technical indicators", prompt)
        self.assertIn("source=postgres", prompt)
        self.assertIn("RSI14=56.2", prompt)
        self.assertIn("MACD_HIST=0.2", prompt)
        self.assertIn("User focus: focus on risk", prompt)

    def test_build_analysis_prompt_with_sentiment_context(self):
        sentiment_context = {
            "symbol": "2330",
            "as_of_date": "2026-03-02",
            "window_days": 20,
            "market_sentiment": "bullish",
            "sentiment_score": 0.38,
            "price_change_pct": 2.14,
            "volatility_level": "medium",
            "source": "price_action_heuristic",
            "summary": "Heuristic sentiment is bullish.",
        }
        prompt = build_analysis_prompt(
            "2330",
            "focus on risk",
            sentiment_context=sentiment_context,
        )
        self.assertIn("Sentiment context", prompt)
        self.assertIn("label=bullish", prompt)
        self.assertIn("score=0.38", prompt)
        self.assertIn("price_change_pct=2.14", prompt)
        self.assertIn("volatility_level=medium", prompt)

    def test_build_provider_prompts_are_differentiated(self):
        providers = ["claude", "gpt5", "grok", "deepseek"]
        prompts = build_provider_prompts(
            symbol="2330",
            providers=providers,
            user_prompt="focus on momentum",
            indicator_context=None,
            sentiment_context={
                "market_sentiment": "neutral",
                "sentiment_score": 0.0,
                "price_change_pct": 0.0,
                "volatility_level": "low",
                "source": "price_action_heuristic",
                "window_days": 20,
                "as_of_date": "2026-03-02",
            },
        )

        self.assertEqual(set(prompts.keys()), set(providers))
        self.assertIn("Provider role: Deep semantic analyst", prompts["claude"])
        self.assertIn("Provider role: Technical analyst", prompts["gpt5"])
        self.assertIn("Provider role: Real-time intelligence scout", prompts["grok"])
        self.assertIn("Provider role: Capital-flow and data auditor", prompts["deepseek"])
        self.assertIn("User focus: focus on momentum", prompts["claude"])
        self.assertIn("Target symbol: 2330", prompts["deepseek"])


if __name__ == "__main__":
    unittest.main()

