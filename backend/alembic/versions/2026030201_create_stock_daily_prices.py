"""create stock_daily_prices

Revision ID: 2026030201
Revises:
Create Date: 2026-03-02 14:58:00
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026030201"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
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
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_stock_daily_prices_trade_date ON stock_daily_prices (trade_date)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_stock_daily_prices_symbol_date ON stock_daily_prices (symbol, trade_date DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS stock_daily_prices")
