import unittest

from backend.app.stocks.intel_mapper import build_status_view


class StockIntelMapperDiagnosisTest(unittest.TestCase):
    def test_build_status_view_marks_permission_required(self):
        payload = {
            "valuation": {
                "status": "restricted",
                "message": "token required",
                "status_code": 401,
                "dataset": "TaiwanStockPER",
                "source": "finmind",
                "data_as_of": "",
                "rows": [],
                "attempts": [
                    {
                        "source": "twse_rwd",
                        "source_priority": "official_primary",
                        "dataset": "TWSE_BWIBBU_d",
                        "status": "error",
                        "status_code": 503,
                        "message": "official endpoint down",
                    },
                    {
                        "source": "finmind",
                        "source_priority": "finmind_fallback",
                        "dataset": "TaiwanStockPER",
                        "status": "restricted",
                        "status_code": 401,
                        "message": "token required",
                    },
                ],
            }
        }

        result = build_status_view(payload, fetched_at="2026-03-04T00:00:00+00:00")
        valuation = result["valuation"]
        self.assertEqual(valuation["diagnosis"]["code"], "permission_required")
        self.assertEqual(valuation["diagnosis"]["label"], "權限限制")
        self.assertEqual(len(valuation["attempts"]), 2)

    def test_build_status_view_marks_no_data(self):
        payload = {
            "monthly_revenue": {
                "status": "empty",
                "message": "Dataset returned no rows.",
                "status_code": 200,
                "dataset": "official_monthly_revenue",
                "source": "official_free_api",
                "data_as_of": "",
                "rows": [],
                "attempts": [],
            }
        }
        result = build_status_view(payload, fetched_at="2026-03-04T00:00:00+00:00")
        revenue = result["monthly_revenue"]
        self.assertEqual(revenue["diagnosis"]["code"], "no_data")
        self.assertEqual(revenue["diagnosis"]["label"], "無資料")


if __name__ == "__main__":
    unittest.main()
