from __future__ import annotations

OVERVIEW_DATASETS = {
    "company_profile": [
        "TaiwanStockInfo",
        "StockInfo",
    ],
    "valuation": [
        "TaiwanStockPER",
        "PER",
    ],
    "institutional_flow": [
        "TaiwanStockInstitutionalInvestorsBuySell",
        "InstitutionalInvestorsBuySell",
    ],
    "margin_short": [
        "TaiwanStockMarginPurchaseShortSale",
    ],
    "foreign_holding": [
        "TaiwanStockShareholding",
        "Shareholding",
    ],
    "monthly_revenue": [
        "TaiwanStockMonthRevenue",
        "MonthRevenue",
    ],
}

DEEP_DATASETS = {
    "price_performance": [
        "TaiwanStockPrice",
    ],
    "shareholding_distribution": [
        "TaiwanStockHoldingSharesPer",
    ],
    "securities_lending": [
        "TaiwanStockSecuritiesLending",
        "SecuritiesLending",
    ],
    "broker_branches": [
        "TaiwanStockTradingDailyReport",
    ],
}

FINANCIAL_DATASETS = {
    "income_statement": [
        "TaiwanStockFinancialStatements",
        "FinancialStatements",
    ],
    "balance_sheet": [
        "TaiwanStockBalanceSheet",
        "BalanceSheet",
    ],
    "cash_flow": [
        "TaiwanStockCashFlowsStatement",
        "CashFlowsStatement",
    ],
}

LOOKBACK_DAYS = {
    "company_profile": 3650,
    "valuation": 420,
    "institutional_flow": 120,
    "margin_short": 120,
    "foreign_holding": 180,
    "monthly_revenue": 450,
    "price_performance": 420,
    "shareholding_distribution": 180,
    "securities_lending": 180,
    "broker_branches": 14,
    "financial": 1200,
}

FRESHNESS_POLICY = {
    "company_profile": {
        "cadence": "irregular",
        "cadence_label": "不定期",
        "expected_interval_days": 120,
        "watch_after_days": 365,
        "stale_after_days": 730,
    },
    "valuation": {
        "cadence": "daily",
        "cadence_label": "日更",
        "expected_interval_days": 2,
        "watch_after_days": 5,
        "stale_after_days": 10,
    },
    "institutional_flow": {
        "cadence": "daily",
        "cadence_label": "日更",
        "expected_interval_days": 2,
        "watch_after_days": 5,
        "stale_after_days": 10,
    },
    "margin_short": {
        "cadence": "daily",
        "cadence_label": "日更",
        "expected_interval_days": 2,
        "watch_after_days": 5,
        "stale_after_days": 10,
    },
    "foreign_holding": {
        "cadence": "daily",
        "cadence_label": "日更",
        "expected_interval_days": 3,
        "watch_after_days": 7,
        "stale_after_days": 14,
    },
    "monthly_revenue": {
        "cadence": "monthly",
        "cadence_label": "月更",
        "expected_interval_days": 45,
        "watch_after_days": 75,
        "stale_after_days": 120,
    },
    "price_performance": {
        "cadence": "daily",
        "cadence_label": "日更",
        "expected_interval_days": 2,
        "watch_after_days": 5,
        "stale_after_days": 10,
    },
    "shareholding_distribution": {
        "cadence": "weekly",
        "cadence_label": "週更",
        "expected_interval_days": 14,
        "watch_after_days": 30,
        "stale_after_days": 60,
    },
    "securities_lending": {
        "cadence": "daily",
        "cadence_label": "日更",
        "expected_interval_days": 3,
        "watch_after_days": 7,
        "stale_after_days": 14,
    },
    "broker_branches": {
        "cadence": "daily",
        "cadence_label": "日更",
        "expected_interval_days": 2,
        "watch_after_days": 5,
        "stale_after_days": 10,
    },
    "financial_statements": {
        "cadence": "quarterly",
        "cadence_label": "季更",
        "expected_interval_days": 120,
        "watch_after_days": 200,
        "stale_after_days": 320,
    },
}
