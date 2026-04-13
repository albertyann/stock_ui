#!/usr/bin/env python3
"""
生成测试数据到 stock_watchlist 数据库
"""

import asyncio
import sys
import random
from datetime import datetime, timedelta, date
from decimal import Decimal

sys.path.insert(0, "/Users/yann/workspace/trading/stock_watchlist/backend")

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session, engine, Base
from app.models import (
    Watchlist,
    WatchlistStock,
    Signal,
    StockPriceCache,
    TechnicalIndicator,
)

# 测试股票数据
TEST_STOCKS = [
    {"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行"},
    {"ts_code": "000002.SZ", "symbol": "000002", "name": "万科A"},
    {"ts_code": "000858.SZ", "symbol": "000858", "name": "五粮液"},
    {"ts_code": "002415.SZ", "symbol": "002415", "name": "海康威视"},
    {"ts_code": "002594.SZ", "symbol": "002594", "name": "比亚迪"},
    {"ts_code": "300750.SZ", "symbol": "300750", "name": "宁德时代"},
    {"ts_code": "600000.SH", "symbol": "600000", "name": "浦发银行"},
    {"ts_code": "600519.SH", "symbol": "600519", "name": "贵州茅台"},
    {"ts_code": "601318.SH", "symbol": "601318", "name": "中国平安"},
    {"ts_code": "601012.SH", "symbol": "601012", "name": "隆基绿能"},
]


async def create_watchlists(session: AsyncSession):
    """创建自选股列表"""
    print("📋 创建自选股列表...")

    watchlists_data = [
        {"name": "核心资产", "description": "长期持有的优质股票", "is_default": True},
        {"name": "成长股", "description": "高增长潜力股票池", "is_default": False},
        {"name": "观察池", "description": "待观察的股票列表", "is_default": False},
    ]

    watchlists = []
    for data in watchlists_data:
        watchlist = Watchlist(**data)
        session.add(watchlist)
        watchlists.append(watchlist)

    await session.flush()
    print(f"   ✓ 创建了 {len(watchlists)} 个自选股列表")
    return watchlists


async def create_watchlist_stocks(session: AsyncSession, watchlists):
    """创建自选股列表中的股票"""
    print("📈 添加自选股...")

    stocks = []

    # 为核心资产列表添加股票
    for stock_data in TEST_STOCKS[:5]:
        stock = WatchlistStock(
            watchlist_id=watchlists[0].id,
            ts_code=stock_data["ts_code"],
            symbol=stock_data["symbol"],
            name=stock_data["name"],
            added_price=Decimal(str(random.uniform(10.0, 200.0))),
            notes=f"测试备注 - {stock_data['name']}",
            alert_enabled=True,
        )
        session.add(stock)
        stocks.append(stock)

    # 为成长股列表添加股票
    for stock_data in TEST_STOCKS[3:8]:
        stock = WatchlistStock(
            watchlist_id=watchlists[1].id,
            ts_code=stock_data["ts_code"],
            symbol=stock_data["symbol"],
            name=stock_data["name"],
            added_price=Decimal(str(random.uniform(20.0, 300.0))),
            notes=f"成长股 - {stock_data['name']}",
            alert_enabled=True,
        )
        session.add(stock)
        stocks.append(stock)

    # 为观察池添加股票
    for stock_data in TEST_STOCKS[5:]:
        stock = WatchlistStock(
            watchlist_id=watchlists[2].id,
            ts_code=stock_data["ts_code"],
            symbol=stock_data["symbol"],
            name=stock_data["name"],
            added_price=Decimal(str(random.uniform(15.0, 250.0))),
            notes=f"观察中 - {stock_data['name']}",
            alert_enabled=False,
        )
        session.add(stock)
        stocks.append(stock)

    await session.flush()
    print(f"   ✓ 添加了 {len(stocks)} 只自选股")
    return stocks


async def create_signals(session: AsyncSession):
    """创建交易信号"""
    print("📊 创建交易信号...")

    signals = []
    signal_types = ["BUY", "SELL", "HOLD"]
    strategies = ["MultiFactorStrategy", "MomentumStrategy", "MeanReversionStrategy"]

    today = date.today()

    for i, stock in enumerate(TEST_STOCKS):
        # 生成多个信号
        for j in range(random.randint(1, 3)):
            signal_date = today - timedelta(days=j * 2)
            signal_type = random.choice(signal_types)

            indicators = {
                "ma5": round(random.uniform(10.0, 200.0), 2),
                "ma10": round(random.uniform(10.0, 200.0), 2),
                "volume_ratio": round(random.uniform(0.5, 3.0), 2),
                "rsi": round(random.uniform(20.0, 80.0), 2),
                "macd_signal": random.choice(
                    ["golden_cross", "death_cross", "neutral"]
                ),
            }

            signal = Signal(
                ts_code=stock["ts_code"],
                signal_type=signal_type,
                signal_strength=random.randint(60, 95),
                signal_date=signal_date,
                current_price=Decimal(str(random.uniform(10.0, 300.0))),
                target_price=Decimal(str(random.uniform(15.0, 350.0)))
                if signal_type == "BUY"
                else None,
                stop_loss_price=Decimal(str(random.uniform(8.0, 250.0)))
                if signal_type == "BUY"
                else None,
                indicators=indicators,
                strategy_name=random.choice(strategies),
                conditions_met=random.randint(4, 8),
                is_active=j == 0,  # 只有最新的信号是活跃的
                executed_at=datetime.now() - timedelta(days=j)
                if random.random() > 0.5
                else None,
                execution_result=random.choice(["成功", "等待中", "已取消"])
                if random.random() > 0.5
                else None,
            )
            session.add(signal)
            signals.append(signal)

    await session.flush()
    print(f"   ✓ 创建了 {len(signals)} 个交易信号")
    return signals


async def create_stock_prices(session: AsyncSession):
    """创建股票价格缓存"""
    print("💰 创建股票价格数据...")

    prices = []
    today = date.today()

    for stock in TEST_STOCKS:
        base_price = random.uniform(10.0, 300.0)

        # 为每只股票生成最近30天的价格数据
        for i in range(30):
            trade_date = today - timedelta(days=i)

            # 模拟价格波动
            change_pct = random.uniform(-5.0, 5.0)
            close_price = base_price * (1 + change_pct / 100)

            price = StockPriceCache(
                ts_code=stock["ts_code"],
                trade_date=trade_date,
                open_price=Decimal(str(close_price * random.uniform(0.98, 1.02))),
                high_price=Decimal(str(close_price * random.uniform(1.0, 1.05))),
                low_price=Decimal(str(close_price * random.uniform(0.95, 1.0))),
                close_price=Decimal(str(close_price)),
                volume=random.randint(1000000, 100000000),
                amount=Decimal(str(random.uniform(1000000.0, 1000000000.0))),
                change_pct=Decimal(str(change_pct)),
                turnover_rate=Decimal(str(random.uniform(0.5, 15.0))),
            )
            session.add(price)
            prices.append(price)

            base_price = close_price

    await session.flush()
    print(f"   ✓ 创建了 {len(prices)} 条价格记录")
    return prices


async def create_technical_indicators(session: AsyncSession):
    """创建技术指标缓存"""
    print("📉 创建技术指标数据...")

    indicators = []
    today = date.today()

    for stock in TEST_STOCKS:
        # 为每只股票生成最近20天的技术指标
        for i in range(20):
            trade_date = today - timedelta(days=i)

            indicator = TechnicalIndicator(
                ts_code=stock["ts_code"],
                trade_date=trade_date,
                ma5=Decimal(str(random.uniform(10.0, 200.0))),
                ma10=Decimal(str(random.uniform(10.0, 200.0))),
                ma20=Decimal(str(random.uniform(10.0, 200.0))),
                ma60=Decimal(str(random.uniform(10.0, 200.0))),
                macd_dif=Decimal(str(random.uniform(-2.0, 2.0))),
                macd_dea=Decimal(str(random.uniform(-2.0, 2.0))),
                macd_bar=Decimal(str(random.uniform(-1.0, 1.0))),
                kdj_k=Decimal(str(random.uniform(0.0, 100.0))),
                kdj_d=Decimal(str(random.uniform(0.0, 100.0))),
                kdj_j=Decimal(str(random.uniform(0.0, 100.0))),
                rsi6=Decimal(str(random.uniform(10.0, 90.0))),
                rsi12=Decimal(str(random.uniform(10.0, 90.0))),
                rsi24=Decimal(str(random.uniform(10.0, 90.0))),
                boll_upper=Decimal(str(random.uniform(50.0, 300.0))),
                boll_middle=Decimal(str(random.uniform(45.0, 280.0))),
                boll_lower=Decimal(str(random.uniform(40.0, 260.0))),
                volume_ratio=Decimal(str(random.uniform(0.5, 3.0))),
                amplitude=Decimal(str(random.uniform(1.0, 10.0))),
            )
            session.add(indicator)
            indicators.append(indicator)

    await session.flush()
    print(f"   ✓ 创建了 {len(indicators)} 条技术指标记录")
    return indicators


async def init_database():
    """初始化数据库表"""
    print("🔄 初始化数据库...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   ✓ 数据库表已创建")


async def main():
    print("=" * 60)
    print("🚀 开始生成测试数据到 stock_watchlist")
    print("=" * 60)
    print()

    # 初始化数据库
    await init_database()
    print()

    async with async_session() as session:
        try:
            # 1. 创建自选股列表
            watchlists = await create_watchlists(session)
            print()

            # 2. 添加自选股
            await create_watchlist_stocks(session, watchlists)
            print()

            # 3. 创建交易信号
            await create_signals(session)
            print()

            # 4. 创建股票价格缓存
            await create_stock_prices(session)
            print()

            # 5. 创建技术指标
            await create_technical_indicators(session)
            print()

            # 提交所有更改
            await session.commit()
            print("=" * 60)
            print("✅ 测试数据生成完成！")
            print("=" * 60)
            print()
            print("📊 数据统计：")
            print(f"   • 自选股列表: {len(watchlists)} 个")
            print(f"   • 股票数量: {len(TEST_STOCKS)} 只")
            print(f"   • 交易信号: 约 {len(TEST_STOCKS) * 2} 个")
            print(f"   • 价格记录: {len(TEST_STOCKS) * 30} 条")
            print(f"   • 技术指标: {len(TEST_STOCKS) * 20} 条")
            print()

        except Exception as e:
            await session.rollback()
            print(f"\n❌ 错误: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
