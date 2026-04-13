from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete, distinct
from sqlalchemy.orm import selectinload
from app.models import Watchlist, WatchlistStock, Signal


class WatchlistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_watchlists(self, user_id: str = "default") -> List[Watchlist]:
        result = await self.db.execute(
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .order_by(Watchlist.created_at.desc())
        )
        return result.scalars().all()

    async def get_watchlist(self, watchlist_id: int) -> Optional[Watchlist]:
        result = await self.db.execute(
            select(Watchlist)
            .where(Watchlist.id == watchlist_id)
            .options(selectinload(Watchlist.stocks))
        )
        return result.scalar_one_or_none()

    async def create_watchlist(
        self,
        name: str,
        description: str = None,
        user_id: str = "default",
        is_default: bool = False,
    ) -> Watchlist:
        watchlist = Watchlist(
            name=name, description=description, user_id=user_id, is_default=is_default
        )
        self.db.add(watchlist)
        await self.db.commit()
        await self.db.refresh(watchlist)
        return watchlist

    async def update_watchlist(
        self, watchlist_id: int, name: str = None, description: str = None
    ) -> Optional[Watchlist]:
        watchlist = await self.get_watchlist(watchlist_id)
        if not watchlist:
            return None

        if name:
            watchlist.name = name
        if description is not None:
            watchlist.description = description

        await self.db.commit()
        await self.db.refresh(watchlist)
        return watchlist

    async def delete_watchlist(self, watchlist_id: int) -> bool:
        watchlist = await self.get_watchlist(watchlist_id)
        if not watchlist:
            return False

        await self.db.delete(watchlist)
        await self.db.commit()
        return True

    async def add_stock(
        self,
        watchlist_id: int,
        ts_code: str,
        symbol: str,
        name: str = None,
        added_price: float = None,
        notes: str = None,
        watch_reason: str = None,
        watch_date: str = None,
    ) -> Optional[WatchlistStock]:
        existing = await self.db.execute(
            select(WatchlistStock).where(
                and_(
                    WatchlistStock.watchlist_id == watchlist_id,
                    WatchlistStock.ts_code == ts_code,
                )
            )
        )
        if existing.scalar_one_or_none():
            return None

        from datetime import date

        stock = WatchlistStock(
            watchlist_id=watchlist_id,
            ts_code=ts_code,
            symbol=symbol,
            name=name,
            watch_date=watch_date or date.today().strftime("%Y-%m-%d"),
            watch_reason=watch_reason,
            added_price=added_price,
            notes=notes,
            status=1,
        )
        self.db.add(stock)
        await self.db.commit()
        await self.db.refresh(stock)
        return stock

    async def remove_stock(self, watchlist_id: int, stock_id: int) -> bool:
        result = await self.db.execute(
            delete(WatchlistStock).where(
                and_(
                    WatchlistStock.id == stock_id,
                    WatchlistStock.watchlist_id == watchlist_id,
                )
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_stocks(
        self,
        watchlist_id: int,
        signal_date: Optional[str] = None,
        watch_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[WatchlistStock]:
        query = select(WatchlistStock).where(
            WatchlistStock.watchlist_id == watchlist_id
        )

        if watch_date:
            query = query.where(WatchlistStock.watch_date == watch_date)

        query = query.order_by(WatchlistStock.added_at.desc())

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_last_trading_day(self, exchange: str = "SSE") -> Optional[str]:
        """获取指定交易所的最后一个交易日

        Args:
            exchange: 交易所代码，默认为 "SSE"（上交所）

        Returns:
            最后一个交易日期， 格式为 "YYYY-MM-DD"， 如果没有则返回 None
        """
        from sqlalchemy import select, and_
        from datetime import date
        from app.models import TradeCal

        # 查询最近的交易日
        result = await self.db.execute(
            select(TradeCal.cal_date)
            .where(
                and_(
                    TradeCal.exchange == exchange,
                    TradeCal.is_open == 1,
                    TradeCal.cal_date <= date.today(),
                )
            )
            .order_by(TradeCal.cal_date.desc())
            .limit(1)
        )

        row = result.scalar_one_or_none()
        return row.cal_date.strftime("%Y-%m-%d") if row else None

    async def get_available_dates(self, watchlist_id: int) -> List[str]:
        """获取有信号数据的日期列表"""
        result = await self.db.execute(
            select(Signal.signal_date)
            .join(WatchlistStock, Signal.ts_code == WatchlistStock.ts_code)
            .where(WatchlistStock.watchlist_id == watchlist_id)
            .distinct()
            .order_by(Signal.signal_date.desc())
        )
        return [row[0] for row in result.fetchall()]

    async def get_watch_dates(self, watchlist_id: int) -> List[str]:
        """获取关注日期列表用于筛选"""
        result = await self.db.execute(
            select(distinct(WatchlistStock.watch_date))
            .where(WatchlistStock.watchlist_id == watchlist_id)
            .where(WatchlistStock.watch_date.isnot(None))
            .order_by(WatchlistStock.watch_date.desc())
        )
        return [row[0] for row in result.fetchall() if row[0]]

    async def update_stock_status(
        self, watchlist_id: int, stock_id: int, status: int
    ) -> Optional[WatchlistStock]:
        result = await self.db.execute(
            select(WatchlistStock).where(
                and_(
                    WatchlistStock.id == stock_id,
                    WatchlistStock.watchlist_id == watchlist_id,
                )
            )
        )
        stock = result.scalar_one_or_none()
        if not stock:
            return None

        stock.status = status
        await self.db.commit()
        await self.db.refresh(stock)
        return stock
