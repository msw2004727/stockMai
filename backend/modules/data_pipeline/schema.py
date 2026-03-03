from __future__ import annotations

STOCK_DAILY_PRICES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_daily_prices (
    symbol VARCHAR(16) NOT NULL,
    trade_date DATE NOT NULL,
    open NUMERIC(14, 4) NOT NULL,
    high NUMERIC(14, 4) NOT NULL,
    low NUMERIC(14, 4) NOT NULL,
    close NUMERIC(14, 4) NOT NULL,
    change NUMERIC(14, 4) NOT NULL DEFAULT 0,
    volume BIGINT NOT NULL DEFAULT 0,
    source VARCHAR(32) NOT NULL DEFAULT 'finmind',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, trade_date)
)
"""

STOCK_DAILY_PRICES_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_stock_daily_prices_trade_date ON stock_daily_prices (trade_date)",
    "CREATE INDEX IF NOT EXISTS idx_stock_daily_prices_symbol_date ON stock_daily_prices (symbol, trade_date DESC)",
)


def ensure_stock_daily_prices_table(cur) -> None:
    cur.execute(STOCK_DAILY_PRICES_TABLE_SQL)
    for statement in STOCK_DAILY_PRICES_INDEX_SQL:
        cur.execute(statement)
