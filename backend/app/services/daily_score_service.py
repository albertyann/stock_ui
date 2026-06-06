from typing import List, Optional
from datetime import date
from sqlalchemy import select, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.market.context import get_current_market
from app.market.filter import build_orm_filter
from app.models import DailyStockScore


class DailyScoreService:
    async def get_scores_by_date(
        self,
        session: AsyncSession,
        trade_date: date,
        direction: Optional[str] = None,
        limit: int = 100,
    ) -> List[DailyStockScore]:
        query = (
            select(DailyStockScore)
            .where(DailyStockScore.trade_date == trade_date)
            .order_by(desc(DailyStockScore.composite_5d))
            .limit(limit)
        )
        if direction:
            query = query.where(DailyStockScore.direction_5d == direction)

        market = get_current_market()
        market_filters = build_orm_filter(market, DailyStockScore.ts_code)
        query = query.where(or_(*market_filters))

        result = await session.execute(query)
        return result.scalars().all()

    async def get_score_summary(
        self,
        session: AsyncSession,
        trade_date: date,
    ) -> dict:
        market = get_current_market()
        market_filters = build_orm_filter(market, DailyStockScore.ts_code)

        total_query = select(func.count()).where(DailyStockScore.trade_date == trade_date).where(or_(*market_filters))
        total_result = await session.execute(total_query)
        total = total_result.scalar()

        bullish_query = (
            select(func.count())
            .where(DailyStockScore.trade_date == trade_date)
            .where(DailyStockScore.direction_5d == "bullish")
            .where(or_(*market_filters))
        )
        bullish_result = await session.execute(bullish_query)
        bullish = bullish_result.scalar()

        bearish_query = (
            select(func.count())
            .where(DailyStockScore.trade_date == trade_date)
            .where(DailyStockScore.direction_5d == "bearish")
            .where(or_(*market_filters))
        )
        bearish_result = await session.execute(bearish_query)
        bearish = bearish_result.scalar()

        neutral = total - bullish - bearish if total else 0

        avg_query = (
            select(func.avg(DailyStockScore.composite_5d))
            .where(DailyStockScore.trade_date == trade_date)
        )
        avg_result = await session.execute(avg_query)
        avg_score = float(avg_result.scalar() or 0)

        return {
            "total": total,
            "bullish": bullish,
            "bearish": bearish,
            "neutral": neutral,
            "avg_score": round(avg_score, 2),
        }

    async def get_latest_trade_date(self, session: AsyncSession) -> Optional[date]:
        query = select(DailyStockScore.trade_date).order_by(desc(DailyStockScore.trade_date)).limit(1)
        result = await session.execute(query)
        row = result.scalar()
        return row

    async def get_available_dates(
        self,
        session: AsyncSession,
        limit: int = 30,
    ) -> List[date]:
        query = (
            select(DailyStockScore.trade_date)
            .distinct()
            .order_by(desc(DailyStockScore.trade_date))
            .limit(limit)
        )
        result = await session.execute(query)
        return [row[0] for row in result.all()]

    async def get_stock_score_history(
        self,
        session: AsyncSession,
        ts_code: str,
        limit: int = 30,
    ) -> List[DailyStockScore]:
        query = (
            select(DailyStockScore)
            .where(DailyStockScore.ts_code == ts_code)
            .order_by(desc(DailyStockScore.trade_date))
            .limit(limit)
        )
        result = await session.execute(query)
        return result.scalars().all()
