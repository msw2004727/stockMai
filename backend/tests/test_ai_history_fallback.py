import unittest
from unittest.mock import patch

from backend.app.ai.routes import _load_cached_history


class AIHistoryFallbackTest(unittest.TestCase):
    @patch("backend.app.ai.routes.load_recent_history")
    @patch("backend.app.ai.routes.get_history")
    def test_load_cached_history_prefers_cache(self, mock_get_history, mock_load_recent_history):
        mock_load_recent_history.return_value = {
            "symbol": "2330",
            "days": 60,
            "series": [{"date": "2026-03-02", "close": 1000}],
            "source": "postgres",
        }

        result = _load_cached_history(symbol="2330", database_url="postgresql://x", days=60)

        self.assertEqual(result["source"], "postgres")
        mock_get_history.assert_not_called()

    @patch("backend.app.ai.routes.load_recent_history", return_value=None)
    @patch("backend.app.ai.routes.get_history")
    def test_load_cached_history_falls_back_to_get_history(self, mock_get_history, _mock_load_recent_history):
        mock_get_history.return_value = {
            "symbol": "2330",
            "days": 60,
            "series": [{"date": "2026-03-02", "close": 1000}],
            "source": "twse",
        }

        result = _load_cached_history(symbol="2330", database_url="postgresql://x", days=60)

        self.assertEqual(result["source"], "twse")
        mock_get_history.assert_called_once_with(symbol="2330", days=60)

    @patch("backend.app.ai.routes.load_recent_history", return_value=None)
    @patch("backend.app.ai.routes.get_history", side_effect=RuntimeError("provider failed"))
    def test_load_cached_history_returns_none_when_fallback_fails(self, _mock_get_history, _mock_load_recent_history):
        result = _load_cached_history(symbol="2330", database_url="postgresql://x", days=60)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
