#!/usr/bin/env python3
"""
Initialize PostgreSQL database for stock watchlist system
"""

import asyncio
import asyncpg
import sys

DATABASE_URL = "postgres://postgres:postgrespwd@localhost:5432/stock_data"


async def init_database():
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Create tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlists (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                user_id VARCHAR(50) DEFAULT 'default',
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, name)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_stocks (
                id SERIAL PRIMARY KEY,
                watchlist_id INTEGER REFERENCES watchlists(id) ON DELETE CASCADE,
                ts_code VARCHAR(20) NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                name VARCHAR(100),
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                watch_date VARCHAR(10),
                watch_reason VARCHAR(50),
                added_price NUMERIC(10, 2),
                notes TEXT,
                alert_enabled BOOLEAN DEFAULT TRUE,
                UNIQUE(watchlist_id, ts_code)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_tags (
                ts_code VARCHAR(20) PRIMARY KEY,
                tags JSONB DEFAULT '[]'::jsonb NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m_signals (
                id SERIAL PRIMARY KEY,
                ts_code VARCHAR(20) NOT NULL,
                signal_type VARCHAR(20) NOT NULL,
                signal_strength INTEGER CHECK (signal_strength BETWEEN 1 AND 5),
                signal_date DATE NOT NULL,
                current_price NUMERIC(10, 2),
                target_price NUMERIC(10, 2),
                stop_loss_price NUMERIC(10, 2),
                indicators JSONB,
                strategy_name VARCHAR(50),
                conditions_met INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                executed_at TIMESTAMP,
                execution_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_prices_cache (
                id SERIAL PRIMARY KEY,
                ts_code VARCHAR(20) NOT NULL,
                trade_date DATE NOT NULL,
                open_price NUMERIC(10, 2),
                high_price NUMERIC(10, 2),
                low_price NUMERIC(10, 2),
                close_price NUMERIC(10, 2) NOT NULL,
                volume INTEGER,
                amount NUMERIC(15, 2),
                change_pct NUMERIC(6, 2),
                turnover_rate NUMERIC(6, 2),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ts_code, trade_date)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS technical_indicators_cache (
                id SERIAL PRIMARY KEY,
                ts_code VARCHAR(20) NOT NULL,
                trade_date DATE NOT NULL,
                ma5 NUMERIC(10, 4),
                ma10 NUMERIC(10, 4),
                ma20 NUMERIC(10, 4),
                ma60 NUMERIC(10, 4),
                macd_dif NUMERIC(10, 4),
                macd_dea NUMERIC(10, 4),
                macd_bar NUMERIC(10, 4),
                kdj_k NUMERIC(6, 2),
                kdj_d NUMERIC(6, 2),
                kdj_j NUMERIC(6, 2),
                rsi6 NUMERIC(6, 2),
                rsi12 NUMERIC(6, 2),
                rsi24 NUMERIC(6, 2),
                boll_upper NUMERIC(10, 4),
                boll_middle NUMERIC(10, 4),
                boll_lower NUMERIC(10, 4),
                volume_ratio NUMERIC(6, 2),
                amplitude NUMERIC(6, 2),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ts_code, trade_date)
            )
        """)

        # Create indexes
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_signals_ts_code ON m_signals(ts_code)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_signals_type ON m_signals(signal_type)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_signals_active ON m_signals(is_active) WHERE is_active = TRUE"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_prices_code_date ON stock_prices_cache(ts_code, trade_date DESC)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_indicators_code_date ON technical_indicators_cache(ts_code, trade_date DESC)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_watchlist_stocks_watch_date ON watchlist_stocks(watch_date)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stock_tags_tags ON stock_tags USING GIN (tags)"
        )

        # Insert default watchlist
        await conn.execute("""
            INSERT INTO watchlists (name, description, user_id, is_default)
            VALUES ('我的自选', '默认自选股分组', 'default', TRUE)
            ON CONFLICT (user_id, name) DO NOTHING
        """)

        print("✅ Database initialized successfully!")
        print("✅ Tables created:")
        print("  - watchlists")
        print("  - watchlist_stocks")
        print("  - stock_tags")
        print("  - m_signals")
        print("  - stock_prices_cache")
        print("  - technical_indicators_cache")
        print("✅ Default watchlist created")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init_database())
