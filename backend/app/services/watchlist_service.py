from typing import List, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete, distinct, func
from sqlalchemy.orm import selectinload
import json
from app.events import event_bus, NoteCreatedEvent
from app.models import (
    Watchlist,
    WatchlistStock,
    WatchlistSnapshot,
    WatchlistSnapshotItem,
    StockTag,
    Tag,
)


class WatchlistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_watchlists(self, user_id: str = "default") -> List[Watchlist]:
        result = await self.db.execute(
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .order_by(
                Watchlist.sort_num.asc().nullsfirst(), Watchlist.created_at.desc()
            )
        )
        return result.scalars().all()

    async def get_watchlists_with_count(
        self, user_id: str = "default"
    ) -> List[Tuple[Watchlist, int]]:
        result = await self.db.execute(
            select(Watchlist, func.count(WatchlistStock.id).label("stock_count"))
            .outerjoin(WatchlistStock, Watchlist.id == WatchlistStock.watchlist_id)
            .where(Watchlist.user_id == user_id)
            .group_by(Watchlist.id)
            .order_by(
                Watchlist.sort_num.asc().nullsfirst(), Watchlist.created_at.desc()
            )
        )
        return [(row.Watchlist, row.stock_count) for row in result.all()]

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
        sort_num: int = 0,
    ) -> Watchlist:
        watchlist = Watchlist(
            name=name,
            description=description,
            user_id=user_id,
            is_default=is_default,
            sort_num=sort_num,
        )
        self.db.add(watchlist)
        await self.db.commit()
        await self.db.refresh(watchlist)
        return watchlist

    async def update_watchlist(
        self,
        watchlist_id: int,
        name: str = None,
        description: str = None,
        sort_num: int = None,
    ) -> Optional[Watchlist]:
        watchlist = await self.get_watchlist(watchlist_id)
        if not watchlist:
            return None

        if name:
            watchlist.name = name
        if description is not None:
            watchlist.description = description
        if sort_num is not None:
            watchlist.sort_num = sort_num

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
                WatchlistStock.ts_code == ts_code,
            )
        )
        if existing.scalar_one_or_none():
            return None

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

        if notes:
            await event_bus.publish(
                "note_created",
                NoteCreatedEvent(ts_code=ts_code, note_content=notes),
            )

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

    def get_stock_industries(self, ts_codes: List[str]) -> dict:
        if not ts_codes:
            return {}
        from sqlalchemy import create_engine, text
        from app.config import get_settings

        settings = get_settings()
        sync_url = settings.database_url.replace("+asyncpg", "")
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT ts_code, industry FROM stock_basic WHERE ts_code = ANY(:ts_codes)"
                ),
                {"ts_codes": ts_codes},
            )
            return {row.ts_code: row.industry or "" for row in result}

    def get_stock_tags(self, ts_codes: List[str]) -> dict:
        if not ts_codes:
            return {}
        from sqlalchemy import create_engine, text
        from app.config import get_settings

        settings = get_settings()
        sync_url = settings.database_url.replace("+asyncpg", "")
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT ts_code, tags FROM stock_tags WHERE ts_code = ANY(:ts_codes)"
                ),
                {"ts_codes": ts_codes},
            )
            return {row.ts_code: row.tags if row.tags is not None else [] for row in result}

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

    async def update_stock_notes(
        self, watchlist_id: int, stock_id: int, notes: str
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

        from datetime import datetime as dt
        stock.notes = notes
        stock.updated_at = dt.now()
        await self.db.commit()
        await self.db.refresh(stock)

        if notes:
            await event_bus.publish(
                "note_created",
                NoteCreatedEvent(ts_code=stock.ts_code, note_content=notes),
            )

        return stock

    async def update_stock_notes_by_id(
        self, stock_id: int, notes: str
    ) -> Optional[WatchlistStock]:
        from datetime import datetime as dt
        result = await self.db.execute(
            select(WatchlistStock).where(WatchlistStock.id == stock_id)
        )
        stock = result.scalar_one_or_none()
        if not stock:
            return None

        stock.notes = notes
        stock.updated_at = dt.now()
        await self.db.commit()
        await self.db.refresh(stock)

        if notes:
            await event_bus.publish(
                "note_created",
                NoteCreatedEvent(ts_code=stock.ts_code, note_content=notes),
            )

        return stock

    async def move_stock_to_watchlist(
        self, stock_id: int, target_watchlist_id: int
    ) -> Optional[WatchlistStock]:
        result = await self.db.execute(
            select(WatchlistStock).where(WatchlistStock.id == stock_id)
        )
        stock = result.scalar_one_or_none()
        if not stock:
            return None

        existing = await self.db.execute(
            select(WatchlistStock).where(
                and_(
                    WatchlistStock.watchlist_id == target_watchlist_id,
                    WatchlistStock.ts_code == stock.ts_code,
                )
            )
        )
        if existing.scalar_one_or_none():
            return None

        stock.watchlist_id = target_watchlist_id
        await self.db.commit()
        await self.db.refresh(stock)
        return stock

    async def create_snapshot(
        self, watchlist_id: int, stocks: List[dict]
    ) -> WatchlistSnapshot:
        from datetime import datetime

        now = datetime.now()
        snapshot = WatchlistSnapshot(
            watchlist_id=watchlist_id,
            snapshot_date=now.strftime("%Y-%m-%d"),
            snapshot_time=now.strftime("%H:%M:%S"),
        )
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)

        for stock in stocks:
            item = WatchlistSnapshotItem(
                snapshot_id=snapshot.id,
                ts_code=stock["ts_code"],
                name=stock.get("name"),
                industry=stock.get("industry"),
                notes=stock.get("notes"),
            )
            self.db.add(item)

        await self.db.commit()
        return snapshot

    async def get_snapshots(self, watchlist_id: int) -> List[WatchlistSnapshot]:
        result = await self.db.execute(
            select(WatchlistSnapshot)
            .where(WatchlistSnapshot.watchlist_id == watchlist_id)
            .options(selectinload(WatchlistSnapshot.items))
            .order_by(WatchlistSnapshot.created_at.desc())
        )
        return result.scalars().all()

    async def delete_snapshot(self, snapshot_id: int) -> bool:
        result = await self.db.execute(
            select(WatchlistSnapshot).where(WatchlistSnapshot.id == snapshot_id)
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            return False

        await self.db.delete(snapshot)
        await self.db.commit()
        return True

    async def get_all_tags(self) -> List[str]:
        result = await self.db.execute(
            select(Tag.name).order_by(Tag.name)
        )
        return [row[0] for row in result.fetchall() if row[0]]

    async def update_stock_tags(self, ts_code: str, tags: List[str]) -> Optional[StockTag]:
        from sqlalchemy import text

        cleaned_tags = sorted(list(set(tag.strip() for tag in tags if tag and tag.strip())))

        if cleaned_tags:
            existing_tags_result = await self.db.execute(
                select(Tag.name).where(Tag.name.in_(cleaned_tags))
            )
            existing_tags = {row[0] for row in existing_tags_result.fetchall()}
            missing_tags = [tag for tag in cleaned_tags if tag not in existing_tags]

            # 自动创建不存在的标签
            for tag_name in missing_tags:
                new_tag = Tag(name=tag_name)
                self.db.add(new_tag)

            if missing_tags:
                await self.db.flush()  # Flush to make new tags available for the upsert

        result = await self.db.execute(
            text("""
                INSERT INTO stock_tags (ts_code, tags, updated_at)
                VALUES (:ts_code, :tags, NOW())
                ON CONFLICT (ts_code)
                DO UPDATE SET
                    tags = EXCLUDED.tags,
                    updated_at = NOW()
                RETURNING ts_code, tags, updated_at
            """),
            {"ts_code": ts_code, "tags": json.dumps(cleaned_tags)}
        )
        await self.db.commit()

        row = result.fetchone()
        if row:
            return StockTag(ts_code=row.ts_code, tags=row.tags, updated_at=row.updated_at)
        return None

    def get_all_watchlist_stocks(
        self,
        page: int = 1,
        page_size: int = 30,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        watchlist_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        sort_by_change_pct: Optional[str] = None,
    ) -> dict:
        from sqlalchemy import create_engine, text
        from app.config import get_settings

        settings = get_settings()
        sync_url = settings.database_url.replace("+asyncpg", "")
        engine = create_engine(sync_url)

        try:
            with engine.connect() as conn:
                where_clauses = []
                params = {}

                if search:
                    where_clauses.append(
                        "(ws.ts_code ILIKE :search OR ws.name ILIKE :search)"
                    )
                    params["search"] = f"%{search}%"

                if industry:
                    where_clauses.append("sb.industry = :industry")
                    params["industry"] = industry

                if watchlist_id:
                    where_clauses.append("ws.watchlist_id = :watchlist_id")
                    params["watchlist_id"] = watchlist_id

                if tags:
                    where_clauses.append("st.tags ?| :tags_list")
                    params["tags_list"] = tags

                where_sql = ""
                if where_clauses:
                    where_sql = "WHERE " + " AND ".join(where_clauses)

                order_sql = "ws.added_at DESC"
                if sort_by_change_pct == "asc":
                    order_sql = "dd.pct_chg ASC NULLS LAST"
                elif sort_by_change_pct == "desc":
                    order_sql = "dd.pct_chg DESC NULLS LAST"

                count_query = f"""
                    SELECT COUNT(*)
                    FROM watchlist_stocks ws
                    LEFT JOIN stock_basic sb ON ws.ts_code = sb.ts_code
                    LEFT JOIN stock_tags st ON ws.ts_code = st.ts_code
                    {where_sql}
                """
                total_result = conn.execute(text(count_query), params)
                total = total_result.scalar()

                stats_query = f"""
                    SELECT
                        COALESCE(SUM(CASE WHEN dd.pct_chg > 0 THEN 1 ELSE 0 END), 0) as up_count,
                        COALESCE(SUM(CASE WHEN dd.pct_chg < 0 THEN 1 ELSE 0 END), 0) as down_count
                    FROM watchlist_stocks ws
                    LEFT JOIN stock_basic sb ON ws.ts_code = sb.ts_code
                    LEFT JOIN stock_tags st ON ws.ts_code = st.ts_code
                    LEFT JOIN LATERAL (
                        SELECT pct_chg
                        FROM daily_data
                        WHERE ts_code = ws.ts_code
                        ORDER BY trade_date DESC
                        LIMIT 1
                    ) dd ON TRUE
                    {where_sql}
                """
                stats_result = conn.execute(text(stats_query), params)
                stats_row = stats_result.fetchone()
                stats = {
                    "up": int(stats_row.up_count) if stats_row else 0,
                    "down": int(stats_row.down_count) if stats_row else 0,
                }

                query = f"""
                    SELECT
                        ws.id,
                        ws.watchlist_id,
                        ws.ts_code,
                        ws.symbol,
                        ws.name as stock_name,
                        w.name as watchlist_name,
                        sb.industry,
                        dd.close as close_price,
                        dd.pct_chg as change_pct,
                        di.total_mv * 10000 as total_mv,
                        ws.notes,
                        ws.added_at,
                        ws.updated_at,
                        st.tags as tags
                    FROM watchlist_stocks ws
                    JOIN watchlists w ON ws.watchlist_id = w.id
                    LEFT JOIN stock_basic sb ON ws.ts_code = sb.ts_code
                    LEFT JOIN stock_tags st ON ws.ts_code = st.ts_code
                    LEFT JOIN LATERAL (
                        SELECT close, pct_chg
                        FROM daily_data
                        WHERE ts_code = ws.ts_code
                        ORDER BY trade_date DESC
                        LIMIT 1
                    ) dd ON TRUE
                    LEFT JOIN LATERAL (
                        SELECT total_mv
                        FROM daily_basic
                        WHERE ts_code = ws.ts_code
                        ORDER BY trade_date DESC
                        LIMIT 1
                    ) di ON TRUE
                    {where_sql}
                    ORDER BY {order_sql}
                    LIMIT :page_size OFFSET :offset
                """
                query_params = {
                    **params,
                    "page_size": page_size,
                    "offset": (page - 1) * page_size,
                }
                result = conn.execute(text(query), query_params)

                stocks = []
                for row in result:
                    stocks.append(
                        {
                            "id": row.id,
                            "watchlist_id": row.watchlist_id,
                            "ts_code": row.ts_code,
                            "symbol": row.symbol,
                            "name": row.stock_name or row.ts_code,
                            "watchlist_name": row.watchlist_name,
                            "industry": row.industry or "",
                            "tags": row.tags if row.tags is not None else [],
                            "close_price": float(row.close_price)
                            if row.close_price
                            else None,
                            "change_pct": float(row.change_pct)
                            if row.change_pct
                            else None,
                            "total_mv": float(row.total_mv) if row.total_mv else None,
                            "notes": row.notes,
                            "added_at": row.added_at.isoformat()
                            if row.added_at
                            else None,
                            "updated_at": row.updated_at.isoformat()
                            if row.updated_at
                            else None,
                        }
                    )

                return {
                    "stocks": stocks,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "total_pages": (total + page_size - 1) // page_size,
                    },
                    "stats": stats,
                }
        except Exception as e:
            import traceback

            traceback.print_exc()
            return {
                "stocks": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": 0,
                    "total_pages": 0,
                },
                "error": str(e),
            }
