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
