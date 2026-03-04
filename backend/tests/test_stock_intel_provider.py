import unittest
from unittest.mock import MagicMock, patch

from backend.app.stocks.intel_provider import fetch_deep_blocks, fetch_overview_blocks


def _ok_block(key: str, source: str = "official_source") -> dict:
    return {
        "key": key,
        "status": "ok",
        "message": "",
        "status_code": 200,
        "dataset": f"{key}_dataset",
        "source": source,
        "data_as_of": "2026-03-04",
        "rows": [{"date": "2026-03-04"}],
    }


def _empty_block(key: str, source: str = "official_source") -> dict:
    return {
        "key": key,
        "status": "empty",
        "message": "",
        "status_code": 200,
        "dataset": f"{key}_dataset",
        "source": source,
        "data_as_of": "",
        "rows": [],
    }


def _error_block(key: str, source: str = "official_source") -> dict:
    return {
        "key": key,
        "status": "error",
        "message": "official endpoint down",
        "status_code": 503,
        "dataset": f"{key}_dataset",
        "source": source,
        "data_as_of": "",
        "rows": [],
    }


def _restricted_finmind_block(key: str) -> dict:
    return {
        "key": key,
        "status": "restricted",
        "message": "token required",
        "status_code": 401,
        "dataset": f"{key}_finmind",
        "source": "finmind",
        "data_as_of": "",
        "rows": [],
    }


class StockIntelProviderTest(unittest.TestCase):
    @patch("backend.app.stocks.intel_provider._fetch_first_available")
    @patch("backend.app.stocks.intel_provider.fetch_official_overview_blocks")
    def test_overview_prefers_official_when_available(self, mock_official, mock_finmind_fetch):
        mock_official.return_value = {
            "company_profile": _ok_block("company_profile"),
            "valuation": _ok_block("valuation"),
            "institutional_flow": _ok_block("institutional_flow"),
            "margin_short": _ok_block("margin_short"),
            "foreign_holding": _ok_block("foreign_holding"),
            "monthly_revenue": _ok_block("monthly_revenue"),
        }

        result = fetch_overview_blocks(client=MagicMock(), symbol="2330")
        self.assertEqual(result["company_profile"]["source_priority"], "official_primary")
        self.assertEqual(result["valuation"]["source_priority"], "official_primary")
        mock_finmind_fetch.assert_not_called()

    @patch("backend.app.stocks.intel_provider._fetch_first_available")
    @patch("backend.app.stocks.intel_provider.fetch_official_overview_blocks")
    def test_overview_uses_finmind_fallback_when_official_empty(self, mock_official, mock_finmind_fetch):
        mock_official.return_value = {
            "company_profile": _empty_block("company_profile"),
            "valuation": _empty_block("valuation"),
            "institutional_flow": _empty_block("institutional_flow"),
            "margin_short": _empty_block("margin_short"),
            "foreign_holding": _empty_block("foreign_holding"),
            "monthly_revenue": _empty_block("monthly_revenue"),
        }

        def finmind_side_effect(*, block_key: str, **_kwargs):
            return _ok_block(block_key, source="finmind")

        mock_finmind_fetch.side_effect = finmind_side_effect

        result = fetch_overview_blocks(client=MagicMock(), symbol="2330")
        self.assertEqual(result["company_profile"]["source"], "finmind")
        self.assertEqual(result["company_profile"]["source_priority"], "finmind_fallback")
        self.assertEqual(result["monthly_revenue"]["source_priority"], "finmind_fallback")

    @patch("backend.app.stocks.intel_provider._fetch_first_available")
    @patch("backend.app.stocks.intel_provider.fetch_official_overview_blocks")
    def test_overview_prefers_official_over_finmind_restricted(self, mock_official, mock_finmind_fetch):
        mock_official.return_value = {
            "company_profile": _error_block("company_profile"),
            "valuation": _error_block("valuation"),
            "institutional_flow": _error_block("institutional_flow"),
            "margin_short": _error_block("margin_short"),
            "foreign_holding": _error_block("foreign_holding"),
            "monthly_revenue": _error_block("monthly_revenue"),
        }
        mock_finmind_fetch.side_effect = lambda *, block_key, **_kwargs: _restricted_finmind_block(block_key)

        result = fetch_overview_blocks(client=MagicMock(), symbol="2330")
        self.assertEqual(result["valuation"]["status"], "error")
        self.assertEqual(result["valuation"]["source"], "official_source")
        self.assertEqual(result["valuation"]["source_priority"], "official_primary")

    @patch("backend.app.stocks.intel_provider._fetch_financial_sections")
    @patch("backend.app.stocks.intel_provider._fetch_first_available")
    @patch("backend.app.stocks.intel_provider.fetch_official_deep_blocks")
    def test_deep_financial_prefers_official_over_finmind_restricted(
        self,
        mock_official,
        mock_finmind_fetch,
        mock_financial_sections,
    ):
        mock_official.return_value = {
            "price_performance": _ok_block("price_performance"),
            "shareholding_distribution": _ok_block("shareholding_distribution"),
            "securities_lending": _ok_block("securities_lending"),
            "broker_branches": _ok_block("broker_branches"),
            "financial_statements": {
                "key": "financial_statements",
                "status": "error",
                "message": "official not available",
                "status_code": 501,
                "dataset": "official_financial_statements",
                "source": "official_free_api",
                "data_as_of": "",
                "rows": [],
                "sections": [],
            },
        }
        mock_finmind_fetch.side_effect = lambda *, block_key, **_kwargs: _ok_block(block_key, source="finmind")
        mock_financial_sections.return_value = {
            "key": "financial_statements",
            "status": "restricted",
            "message": "token required",
            "status_code": 401,
            "dataset": "TaiwanStockFinancialStatements",
            "source": "finmind",
            "data_as_of": "",
            "rows": [],
            "sections": [],
        }

        result = fetch_deep_blocks(client=MagicMock(), symbol="2330")
        self.assertEqual(result["financial_statements"]["status"], "error")
        self.assertEqual(result["financial_statements"]["source"], "official_free_api")
        self.assertEqual(result["financial_statements"]["source_priority"], "official_primary")


if __name__ == "__main__":
    unittest.main()
