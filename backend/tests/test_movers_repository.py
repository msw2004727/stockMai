from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.app.stocks.movers_repository import _normalize_rows


class MoversRepositoryTest(unittest.TestCase):
    @patch("backend.app.stocks.movers_repository.resolve_stock_name", return_value="TSMC")
    def test_normalize_rows_converts_shares_to_integer_lots(self, _mock_name):
        rows = [
            {
                "symbol": "2330",
                "close": 1935.0,
                "change": -40.0,
                "change_pct": -2.02,
                "volume": 224651381,
            }
        ]

        payload = _normalize_rows(rows)

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["name"], "TSMC")
        self.assertEqual(payload[0]["volume_shares"], 224651381)
        self.assertEqual(payload[0]["volume"], 224651)


if __name__ == "__main__":
    unittest.main()
