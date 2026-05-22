from typing import List, Optional, Dict, Any, Tuple
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, func, delete as sa_delete
from sqlalchemy.dialects.postgresql import insert
import pandas as pd

from app.models import Signal, StockPriceCache, TechnicalIndicator
from app.events.note_events import NoteCreatedEvent
from app.database import async_session


class SignalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_stock(self, ts_code: str, days: int = 60) -> Dict[str, Any]:
        return {"error": "Signal analysis unavailable: stock_picker dependency removed"}

    def _extract_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        return {}

    async def save_signal(self, signal_data: Dict[str, Any]) -> Signal:
        today = date.today()

        existing = await self.db.execute(
            select(Signal).where(
                and_(
                    Signal.ts_code == signal_data["ts_code"],
                    Signal.signal_date == today,
                    Signal.is_active == True,
                )
            )
        )
        existing_signal = existing.scalar_one_or_none()

        if existing_signal:
            existing_signal.signal_type = signal_data["signal_type"]
            existing_signal.signal_strength = signal_data.get("signal_strength")
            existing_signal.current_price = signal_data.get("current_price")
            existing_signal.indicators = signal_data.get("indicators")
            existing_signal.conditions_met = signal_data.get("conditions_met")
            await self.db.commit()
            await self.db.refresh(existing_signal)
            return existing_signal

        signal = Signal(
            ts_code=signal_data["ts_code"],
            signal_type=signal_data["signal_type"],
            signal_strength=signal_data.get("signal_strength"),
            signal_date=today,
            current_price=signal_data.get("current_price"),
            indicators=signal_data.get("indicators"),
            strategy_name=signal_data.get("strategy_name"),
            conditions_met=signal_data.get("conditions_met"),
            is_active=True,
        )
        self.db.add(signal)
        await self.db.commit()
        await self.db.refresh(signal)
        return signal

    async def get_signals(
        self,
        ts_code: str = None,
        signal_type: str = None,
        active_only: bool = True,
        limit: int = 50,
    ) -> List[Signal]:
        query = select(Signal)

        if ts_code:
            query = query.where(Signal.ts_code == ts_code)
        if signal_type:
            query = query.where(Signal.signal_type == signal_type)
        if active_only:
            query = query.where(Signal.is_active == True)

        query = query.order_by(Signal.id.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_signals_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        ts_code: Optional[str] = None,
        signal_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        signal_date: Optional[date] = None,
        signal_date_start: Optional[date] = None,
        signal_date_end: Optional[date] = None,
        note_content: Optional[str] = None,
        market_type: Optional[str] = None,
    ) -> Tuple[List[Signal], int]:
        filters = []
        if ts_code:
            filters.append(Signal.ts_code == ts_code)
        if signal_type:
            filters.append(Signal.signal_type == signal_type)
        if is_active is not None:
            filters.append(Signal.is_active == is_active)
        if signal_date:
            filters.append(Signal.signal_date == signal_date)
        if signal_date_start:
            filters.append(Signal.signal_date >= signal_date_start)
        if signal_date_end:
            filters.append(Signal.signal_date <= signal_date_end)
        if note_content:
            filters.append(Signal.note_content == note_content)
        if market_type:
            prefix_col = func.substring(Signal.ts_code, 1, 3)
            if market_type == "main":
                filters.append(prefix_col.in_(["600", "601", "603", "605", "000", "001", "002", "003"]))
            elif market_type == "chye":
                filters.append(prefix_col.in_(["300", "301"]))
            elif market_type == "kcb":
                filters.append(prefix_col.in_(["688", "689"]))

        count_query = select(func.count()).select_from(Signal)
        if filters:
            count_query = count_query.where(and_(*filters))
        total = (await self.db.execute(count_query)).scalar()

        offset = (page - 1) * page_size
        data_query = select(Signal)
        if filters:
            data_query = data_query.where(and_(*filters))
        data_query = data_query.order_by(Signal.id.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(data_query)
        signals = result.scalars().all()

        return signals, total

    async def delete_signal(self, signal_id: int) -> bool:
        result = await self.db.execute(
            sa_delete(Signal).where(Signal.id == signal_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_latest_signal(self, ts_code: str) -> Optional[Signal]:
        result = await self.db.execute(
            select(Signal)
            .where(and_(Signal.ts_code == ts_code, Signal.is_active == True))
            .order_by(Signal.signal_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_price_cache(self, ts_code: str, price_data: Dict[str, Any]):
        stmt = (
            insert(StockPriceCache)
            .values(
                ts_code=ts_code,
                trade_date=price_data["trade_date"],
                open_price=price_data.get("open"),
                high_price=price_data.get("high"),
                low_price=price_data.get("low"),
                close_price=price_data["close"],
                volume=price_data.get("volume"),
                amount=price_data.get("amount"),
                change_pct=price_data.get("change_pct"),
                turnover_rate=price_data.get("turnover_rate"),
            )
            .on_conflict_do_update(
                index_elements=["ts_code", "trade_date"], set_=price_data
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_cached_price(self, ts_code: str) -> Optional[StockPriceCache]:
        result = await self.db.execute(
            select(StockPriceCache)
            .where(StockPriceCache.ts_code == ts_code)
            .order_by(StockPriceCache.trade_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_available_dates(
        self, watchlist_id: int
    ) -> List[str]:
        from app.models import WatchlistStock

        result = await self.db.execute(
            select(Signal.signal_date)
            .join(WatchlistStock, Signal.ts_code == WatchlistStock.ts_code)
            .where(WatchlistStock.watchlist_id == watchlist_id)
            .distinct()
            .order_by(Signal.signal_date.desc())
        )
        return [row[0] for row in result.fetchall()]

    @staticmethod
    async def handle_note_created(event: NoteCreatedEvent) -> None:
        from datetime import date
        from sqlalchemy import and_
        from app.models import Signal

        try:
            async with async_session() as session:
                today = date.today()

                result = await session.execute(
                    select(Signal).where(
                        and_(
                            Signal.ts_code == event.ts_code,
                            Signal.signal_type == "NOTE",
                            Signal.signal_date == today,
                        )
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.note_content = event.note_content
                    await session.commit()
                    await session.refresh(existing)
                    return

                signal = Signal(
                    ts_code=event.ts_code,
                    signal_type="NOTE",
                    signal_date=today,
                    note_content=event.note_content,
                    is_active=True,
                )
                session.add(signal)
                await session.commit()
                await session.refresh(signal)
        except Exception:
            logger.exception(
                "Failed to create note signal for %s", event.ts_code
            )
