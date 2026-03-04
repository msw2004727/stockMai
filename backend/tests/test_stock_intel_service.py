import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.stocks.intel_service import (
    get_stock_intel_deep,
    get_stock_intel_overview,
    get_stock_intel_status,
)


class StockIntelServiceTest(unittest.TestCase):
    @patch("backend.app.stocks.intel_service.fetch_overview_blocks")
    @patch("backend.app.stocks.intel_service.build_finmind_client")
    @patch("backend.app.stocks.intel_service.get_settings")
    def test_overview_without_token_returns_restricted_payload(
        self,
        mock_get_settings,
        _mock_build_client,
        mock_fetch_overview,
    ):
        mock_get_settings.return_value = SimpleNamespace(finmind_token="")
        mock_fetch_overview.return_value = {
            "company_profile": {"status": "restricted", "dataset": "TaiwanStockInfo", "data_as_of": "", "rows": [], "message": "token missing", "status_code": 401},
            "valuation": {"status": "restricted", "dataset": "TaiwanStockPER", "data_as_of": "", "rows": [], "message": "token missing", "status_code": 401},
            "institutional_flow": {"status": "restricted", "dataset": "TaiwanStockInstitutionalInvestorsBuySell", "data_as_of": "", "rows": [], "message": "token missing", "status_code": 401},
            "margin_short": {"status": "restricted", "dataset": "TaiwanStockMarginPurchaseShortSale", "data_as_of": "", "rows": [], "message": "token missing", "status_code": 401},
            "foreign_holding": {"status": "restricted", "dataset": "TaiwanStockShareholding", "data_as_of": "", "rows": [], "message": "token missing", "status_code": 401},
            "monthly_revenue": {"status": "restricted", "dataset": "TaiwanStockMonthRevenue", "data_as_of": "", "rows": [], "message": "token missing", "status_code": 401},
        }
        result = get_stock_intel_overview("2330")
        self.assertEqual(result["symbol"], "2330")
        self.assertFalse(result["token_configured"])
        self.assertEqual(result["institutional_flow"]["availability"]["status"], "restricted")

    @patch("backend.app.stocks.intel_service.get_quote")
    @patch("backend.app.stocks.intel_service.fetch_overview_blocks")
    @patch("backend.app.stocks.intel_service.build_finmind_client")
    @patch("backend.app.stocks.intel_service.get_settings")
    def test_get_stock_intel_overview_success(
        self,
        mock_get_settings,
        _mock_build_client,
        mock_fetch_overview,
        mock_get_quote,
    ):
        mock_get_settings.return_value = SimpleNamespace(finmind_token="token")
        mock_get_quote.return_value = {"symbol": "2330", "source": "twse_realtime", "close": 1000.0}
        mock_fetch_overview.return_value = {
            "company_profile": {
                "status": "ok",
                "dataset": "TaiwanStockInfo",
                "data_as_of": "",
                "rows": [{"stock_id": "2330", "stock_name": "台積電", "industry_category": "半導體"}],
                "message": "",
                "status_code": 200,
            },
            "valuation": {
                "status": "ok",
                "dataset": "TaiwanStockPER",
                "data_as_of": "2026-03-03",
                "rows": [{"date": "2026-03-03", "PER": 21.5, "PBR": 5.8, "dividend_yield": 1.8}],
                "message": "",
                "status_code": 200,
            },
            "institutional_flow": {
                "status": "ok",
                "dataset": "TaiwanStockInstitutionalInvestorsBuySell",
                "data_as_of": "2026-03-03",
                "rows": [{"date": "2026-03-03", "name": "Foreign", "buy": 1000, "sell": 500, "difference": 500}],
                "message": "",
                "status_code": 200,
            },
            "margin_short": {
                "status": "ok",
                "dataset": "TaiwanStockMarginPurchaseShortSale",
                "data_as_of": "2026-03-03",
                "rows": [{"date": "2026-03-03", "MarginPurchaseBalance": 10000, "ShortSaleBalance": 5000}],
                "message": "",
                "status_code": 200,
            },
            "foreign_holding": {
                "status": "ok",
                "dataset": "TaiwanStockShareholding",
                "data_as_of": "2026-03-03",
                "rows": [{"date": "2026-03-03", "Foreign_Investor_Shares_Holding_Ratio": 72.5}],
                "message": "",
                "status_code": 200,
            },
            "monthly_revenue": {
                "status": "ok",
                "dataset": "TaiwanStockMonthRevenue",
                "data_as_of": "2026-02",
                "rows": [{"date": "2026-02-01", "revenue": 1000000, "revenue_year_growth_rate": 12.3}],
                "message": "",
                "status_code": 200,
            },
        }

        result = get_stock_intel_overview("2330")
        self.assertEqual(result["symbol"], "2330")
        self.assertEqual(result["source"], "official_twse_tpex_tdcc_first_then_finmind")
        self.assertTrue(result["token_configured"])
        self.assertEqual(result["quote_summary"]["availability"]["status"], "ok")
        self.assertEqual(result["company_profile"]["availability"]["status"], "ok")
        self.assertEqual(result["valuation"]["summary"]["latest_per"], 21.5)
        self.assertEqual(result["valuation"]["freshness"]["cadence_label"], "日更")
        self.assertEqual(result["institutional_flow"]["availability"]["status"], "ok")
        self.assertIn("datasets", result)
        self.assertIn("institutional_flow", result["datasets"])

    @patch("backend.app.stocks.intel_service.get_quote", side_effect=RuntimeError("quote down"))
    @patch("backend.app.stocks.intel_service.fetch_overview_blocks")
    @patch("backend.app.stocks.intel_service.build_finmind_client")
    @patch("backend.app.stocks.intel_service.get_settings")
    def test_overview_handles_quote_failure(
        self,
        mock_get_settings,
        _mock_build_client,
        mock_fetch_overview,
        _mock_get_quote,
    ):
        mock_get_settings.return_value = SimpleNamespace(finmind_token="token")
        mock_fetch_overview.return_value = {
            "company_profile": {"status": "empty", "dataset": "", "data_as_of": "", "rows": [], "message": "", "status_code": 200},
            "valuation": {"status": "empty", "dataset": "", "data_as_of": "", "rows": [], "message": "", "status_code": 200},
            "institutional_flow": {"status": "empty", "dataset": "", "data_as_of": "", "rows": [], "message": "", "status_code": 200},
            "margin_short": {"status": "empty", "dataset": "", "data_as_of": "", "rows": [], "message": "", "status_code": 200},
            "foreign_holding": {"status": "empty", "dataset": "", "data_as_of": "", "rows": [], "message": "", "status_code": 200},
            "monthly_revenue": {"status": "empty", "dataset": "", "data_as_of": "", "rows": [], "message": "", "status_code": 200},
        }
        result = get_stock_intel_overview("2330")
        self.assertEqual(result["quote_summary"]["availability"]["status"], "error")

    @patch("backend.app.stocks.intel_service.fetch_deep_blocks")
    @patch("backend.app.stocks.intel_service.build_finmind_client")
    @patch("backend.app.stocks.intel_service.get_settings")
    def test_get_stock_intel_deep_success(self, mock_get_settings, _mock_build_client, mock_fetch_deep):
        mock_get_settings.return_value = SimpleNamespace(finmind_token="token")
        mock_fetch_deep.return_value = {
            "price_performance": {
                "status": "ok",
                "dataset": "TaiwanStockPrice",
                "data_as_of": "2026-03-03",
                "rows": [
                    {"date": "2025-03-03", "close": 900},
                    {"date": "2025-12-01", "close": 950},
                    {"date": "2026-02-01", "close": 980},
                    {"date": "2026-03-03", "close": 1000},
                ],
                "message": "",
                "status_code": 200,
            },
            "shareholding_distribution": {
                "status": "ok",
                "dataset": "TaiwanStockHoldingSharesPer",
                "data_as_of": "2026-03-03",
                "rows": [{"date": "2026-03-03", "HoldingSharesLevel": "1-5", "percent": 12.0}],
                "message": "",
                "status_code": 200,
            },
            "securities_lending": {
                "status": "ok",
                "dataset": "TaiwanStockSecuritiesLending",
                "data_as_of": "2026-03-03",
                "rows": [{"date": "2026-03-03", "lending_balance": 1234}],
                "message": "",
                "status_code": 200,
            },
            "broker_branches": {
                "status": "restricted",
                "dataset": "TaiwanStockTradingDailyReport",
                "data_as_of": "",
                "rows": [],
                "message": "permission denied",
                "status_code": 403,
            },
            "financial_statements": {
                "status": "ok",
                "dataset": "TaiwanStockFinancialStatements",
                "data_as_of": "2025-12-31",
                "rows": [],
                "message": "",
                "status_code": 200,
                "sections": [
                    {
                        "kind": "income_statement",
                        "dataset": "TaiwanStockFinancialStatements",
                        "availability": {"status": "ok", "message": ""},
                        "data_as_of": "2025-12-31",
                        "rows": [{"date": "2025-12-31", "type": "Revenue", "value": 1000000}],
                    }
                ],
            },
        }
        result = get_stock_intel_deep("2330")
        self.assertEqual(result["symbol"], "2330")
        self.assertTrue(result["token_configured"])
        self.assertEqual(result["price_performance"]["availability"]["status"], "ok")
        self.assertIn("freshness", result["price_performance"])
        self.assertEqual(result["broker_branches"]["availability"]["status"], "restricted")
        self.assertEqual(result["financial_statements"]["availability"]["status"], "ok")
        self.assertEqual(len(result["financial_statements"]["sections"]), 1)

    @patch("backend.app.stocks.intel_service.fetch_deep_blocks")
    @patch("backend.app.stocks.intel_service.fetch_overview_blocks")
    @patch("backend.app.stocks.intel_service.build_finmind_client")
    @patch("backend.app.stocks.intel_service.get_settings")
    def test_get_stock_intel_status_success(
        self,
        mock_get_settings,
        _mock_build_client,
        mock_fetch_overview,
        mock_fetch_deep,
    ):
        mock_get_settings.return_value = SimpleNamespace(finmind_token="token")
        mock_fetch_overview.return_value = {
            "company_profile": {"status": "ok", "dataset": "AA", "data_as_of": "", "rows": [], "message": "", "status_code": 200},
            "valuation": {"status": "ok", "dataset": "AB", "data_as_of": "2026-03-03", "rows": [], "message": "", "status_code": 200},
            "institutional_flow": {"status": "ok", "dataset": "A", "data_as_of": "2026-03-03", "rows": [], "message": "", "status_code": 200},
            "margin_short": {"status": "empty", "dataset": "B", "data_as_of": "", "rows": [], "message": "", "status_code": 200},
            "foreign_holding": {"status": "ok", "dataset": "C", "data_as_of": "2026-03-03", "rows": [], "message": "", "status_code": 200},
            "monthly_revenue": {"status": "error", "dataset": "D", "data_as_of": "", "rows": [], "message": "down", "status_code": 503},
        }
        mock_fetch_deep.return_value = {
            "price_performance": {"status": "ok", "dataset": "EA", "data_as_of": "2026-03-03", "rows": [], "message": "", "status_code": 200},
            "shareholding_distribution": {"status": "ok", "dataset": "E", "data_as_of": "2026-03-03", "rows": [], "message": "", "status_code": 200},
            "securities_lending": {"status": "ok", "dataset": "F", "data_as_of": "2026-03-03", "rows": [], "message": "", "status_code": 200},
            "broker_branches": {"status": "restricted", "dataset": "G", "data_as_of": "", "rows": [], "message": "no perm", "status_code": 403},
            "financial_statements": {
                "status": "ok",
                "dataset": "H",
                "data_as_of": "2025-12-31",
                "rows": [],
                "message": "",
                "status_code": 200,
                "sections": [],
            },
        }
        result = get_stock_intel_status("2330")
        self.assertEqual(result["symbol"], "2330")
        self.assertTrue(result["token_configured"])
        self.assertIn("datasets", result)
        self.assertIn("freshness", result["datasets"]["valuation"])
        self.assertEqual(result["datasets"]["broker_branches"]["status"], "restricted")


if __name__ == "__main__":
    unittest.main()
