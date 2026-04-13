#!/usr/bin/env python3
"""
生成股票基础数据到数据库，用于测试
"""

import asyncio
import sys
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, "/Users/yann/workspace/trading/stock_watchlist/backend")

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session

# 测试股票基础数据
TEST_STOCKS_DATA = [
    {
        "ts_code": "000001.SZ",
        "symbol": "000001",
        "name": "平安银行",
        "industry": "银行",
        "current_price": 12.58,
        "change_pct": 1.25,
        "volume": 125800000,
        "amount": 1580000000.0,
        "turnover_rate": 0.65,
        "pe": 6.5,
        "pb": 0.85,
        "market_cap": 250000000000.0,
    },
    {
        "ts_code": "000002.SZ",
        "symbol": "000002",
        "name": "万科A",
        "industry": "房地产",
        "current_price": 8.32,
        "change_pct": -0.85,
        "volume": 85000000,
        "amount": 708000000.0,
        "turnover_rate": 0.89,
        "pe": 12.3,
        "pb": 0.65,
        "market_cap": 98000000000.0,
    },
    {
        "ts_code": "000858.SZ",
        "symbol": "000858",
        "name": "五粮液",
        "industry": "白酒",
        "current_price": 145.20,
        "change_pct": 2.15,
        "volume": 6500000,
        "amount": 945000000.0,
        "turnover_rate": 0.17,
        "pe": 18.5,
        "pb": 4.2,
        "market_cap": 565000000000.0,
    },
    {
        "ts_code": "002415.SZ",
        "symbol": "002415",
        "name": "海康威视",
        "industry": "电子",
        "current_price": 32.68,
        "change_pct": -1.23,
        "volume": 25600000,
        "amount": 836000000.0,
        "turnover_rate": 0.28,
        "pe": 22.3,
        "pb": 3.85,
        "market_cap": 305000000000.0,
    },
    {
        "ts_code": "002594.SZ",
        "symbol": "002594",
        "name": "比亚迪",
        "industry": "汽车",
        "current_price": 268.50,
        "change_pct": 3.45,
        "volume": 12800000,
        "amount": 3430000000.0,
        "turnover_rate": 1.12,
        "pe": 28.6,
        "pb": 5.2,
        "market_cap": 785000000000.0,
    },
    {
        "ts_code": "300750.SZ",
        "symbol": "300750",
        "name": "宁德时代",
        "industry": "电池",
        "current_price": 198.30,
        "change_pct": 1.89,
        "volume": 8900000,
        "amount": 1764000000.0,
        "turnover_rate": 0.45,
        "pe": 25.8,
        "pb": 4.85,
        "market_cap": 872000000000.0,
    },
    {
        "ts_code": "600000.SH",
        "symbol": "600000",
        "name": "浦发银行",
        "industry": "银行",
        "current_price": 7.45,
        "change_pct": 0.25,
        "volume": 45000000,
        "amount": 335000000.0,
        "turnover_rate": 0.15,
        "pe": 4.8,
        "pb": 0.42,
        "market_cap": 218000000000.0,
    },
    {
        "ts_code": "600519.SH",
        "symbol": "600519",
        "name": "贵州茅台",
        "industry": "白酒",
        "current_price": 1588.00,
        "change_pct": 0.95,
        "volume": 1200000,
        "amount": 1905600000.0,
        "turnover_rate": 0.095,
        "pe": 28.5,
        "pb": 8.5,
        "market_cap": 1998000000000.0,
    },
    {
        "ts_code": "601318.SH",
        "symbol": "601318",
        "name": "中国平安",
        "industry": "保险",
        "current_price": 48.65,
        "change_pct": -0.45,
        "volume": 35000000,
        "amount": 1702000000.0,
        "turnover_rate": 0.32,
        "pe": 9.2,
        "pb": 0.95,
        "market_cap": 885000000000.0,
    },
    {
        "ts_code": "601012.SH",
        "symbol": "601012",
        "name": "隆基绿能",
        "industry": "光伏",
        "current_price": 18.92,
        "change_pct": -2.15,
        "volume": 42000000,
        "amount": 794000000.0,
        "turnover_rate": 0.55,
        "pe": 15.8,
        "pb": 1.95,
        "market_cap": 143000000000.0,
    },
]


def insert_stock_prices_sync():
    """同步插入股票价格数据"""
    import sys

    sys.path.insert(0, "/Users/yann/workspace/trading/stock_watchlist/backend")

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.config import get_settings

    settings = get_settings()
    # 使用同步引擎
    sync_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        # 检查表是否存在
        result = session.execute(
            text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'stock_prices_cache'
            )
        """)
        )
        table_exists = result.scalar()

        if not table_exists:
            print("❌ stock_prices_cache 表不存在，请先创建数据库表")
            return

        print("📊 插入股票价格测试数据...")

        from datetime import date

        today = date.today()

        inserted = 0
        for stock in TEST_STOCKS_DATA:
            try:
                # 检查是否已存在
                result = session.execute(
                    text("""
                    SELECT id FROM stock_prices_cache 
                    WHERE ts_code = :ts_code AND trade_date = :trade_date
                """),
                    {"ts_code": stock["ts_code"], "trade_date": today},
                )

                if result.fetchone():
                    # 更新现有记录
                    session.execute(
                        text("""
                        UPDATE stock_prices_cache SET
                            close_price = :close_price,
                            open_price = :open_price,
                            high_price = :high_price,
                            low_price = :low_price,
                            volume = :volume,
                            amount = :amount,
                            change_pct = :change_pct,
                            turnover_rate = :turnover_rate,
                            updated_at = NOW()
                        WHERE ts_code = :ts_code AND trade_date = :trade_date
                    """),
                        {
                            "ts_code": stock["ts_code"],
                            "trade_date": today,
                            "close_price": stock["current_price"],
                            "open_price": stock["current_price"] * 0.99,
                            "high_price": stock["current_price"] * 1.02,
                            "low_price": stock["current_price"] * 0.98,
                            "volume": stock["volume"],
                            "amount": stock["amount"],
                            "change_pct": stock["change_pct"],
                            "turnover_rate": stock["turnover_rate"],
                        },
                    )
                else:
                    # 插入新记录
                    session.execute(
                        text("""
                        INSERT INTO stock_prices_cache 
                        (ts_code, trade_date, close_price, open_price, high_price, low_price, 
                         volume, amount, change_pct, turnover_rate, updated_at)
                        VALUES 
                        (:ts_code, :trade_date, :close_price, :open_price, :high_price, :low_price,
                         :volume, :amount, :change_pct, :turnover_rate, NOW())
                    """),
                        {
                            "ts_code": stock["ts_code"],
                            "trade_date": today,
                            "close_price": stock["current_price"],
                            "open_price": stock["current_price"] * 0.99,
                            "high_price": stock["current_price"] * 1.02,
                            "low_price": stock["current_price"] * 0.98,
                            "volume": stock["volume"],
                            "amount": stock["amount"],
                            "change_pct": stock["change_pct"],
                            "turnover_rate": stock["turnover_rate"],
                        },
                    )
                inserted += 1
            except Exception as e:
                print(f"   ✗ {stock['ts_code']}: {e}")

        session.commit()
        print(f"   ✓ 已插入/更新 {inserted} 条价格记录")


async def main():
    print("=" * 60)
    print("🚀 开始生成股票基础数据")
    print("=" * 60)
    print()

    # 使用同步方式插入数据
    insert_stock_prices_sync()

    print()
    print("=" * 60)
    print("✅ 股票基础数据生成完成！")
    print("=" * 60)
    print()
    print("📊 数据预览：")
    for stock in TEST_STOCKS_DATA[:3]:
        print(
            f"   • {stock['ts_code']} {stock['name']}: ¥{stock['current_price']} ({stock['change_pct']:+.2f}%)"
        )
    print(f"   ... 共 {len(TEST_STOCKS_DATA)} 只股票")


if __name__ == "__main__":
    asyncio.run(main())
