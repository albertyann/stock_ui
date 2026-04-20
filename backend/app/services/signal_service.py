from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.dialects.postgresql import insert
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from stock_picker.strategy.momentum_strategy import MomentumStrategy
from stock_picker.analysis.technical_indicators import TechnicalIndicators
from stock_picker.data.fetcher import DataFetcher
from app.models import Signal, StockPriceCache, TechnicalIndicator
from app.events.note_events import NoteCreatedEvent
from app.database import async_session


class SignalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.momentum_strategy = MomentumStrategy()
        self.indicators = TechnicalIndicators()
        self.fetcher = DataFetcher()

    async def analyze_stock(self, ts_code: str, days: int = 60) -> Dict[str, Any]:
        try:
            df = self.fetcher.get_daily_data(ts_code, period=days)
            if df.empty or len(df) < 30:
                return {"error": "Insufficient data"}

            should_buy = self.momentum_strategy.should_buy(ts_code, df)

            if should_buy:
                signal_type = "BUY"
                strength = 4
            else:
                should_sell = self.momentum_strategy.should_sell(ts_code, df, {})
                signal_type = "SELL" if should_sell else "WATCH"
                strength = 3 if should_sell else 0

            latest = df.iloc[-1]
            indicators = self._extract_indicators(df)

            return {
                "ts_code": ts_code,
                "signal_type": signal_type,
                "signal_strength": strength,
                "current_price": float(latest["收盘"]),
                "indicators": indicators,
                "strategy_name": "momentum",
                "conditions_met": 6 if should_buy else (4 if should_sell else 2),
            }
        except Exception as e:
            return {"error": str(e)}

    def _extract_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        df = self.indicators.calculate_ma(df, [5, 10, 20, 60])
        df = self.indicators.calculate_macd(df)
        df = self.indicators.calculate_kdj(df)
        df = self.indicators.calculate_rsi(df, 14)

        latest = df.iloc[-1]
        return {
            "ma5": float(latest.get("MA5", 0)),
            "ma10": float(latest.get("MA10", 0)),
            "ma20": float(latest.get("MA20", 0)),
            "macd": float(latest.get("MACD", 0)),
            "kdj_j": float(latest.get("J", 0)),
            "rsi14": float(latest.get("RSI14", 0)),
        }

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
