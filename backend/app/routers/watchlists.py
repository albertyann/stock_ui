from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import json
import os

from app.database import get_db
from app.services.watchlist_service import WatchlistService


router = APIRouter(prefix="/watchlists", tags=["watchlists"])


class WatchlistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sort_num: Optional[int] = 0


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_num: Optional[int] = None


class WatchlistStockCreate(BaseModel):
    ts_code: str
    notes: Optional[str] = None
    watch_reason: Optional[str] = None
    watch_date: Optional[str] = None


class WatchlistStockBatchCreate(BaseModel):
    ts_codes: List[str]


class WatchlistResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_default: bool
    sort_num: int
    created_at: str

    class Config:
        from_attributes = True


class WatchlistStockResponse(BaseModel):
    id: int
    ts_code: str
    symbol: str
    name: Optional[str]
    added_at: str
    watch_date: Optional[str]
    watch_reason: Optional[str]
    added_price: Optional[float]
    notes: Optional[str]
    alert_enabled: bool
    status: int = 1

    class Config:
        from_attributes = True


def get_watch_reasons():
    """Load watch reasons from config file"""
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "config", "watch_reasons.json"
    )
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"watch_reasons": []}


@router.get("", response_model=dict)
async def get_watchlists(user_id: str = "default", db: AsyncSession = Depends(get_db)):
    service = WatchlistService(db)
    watchlists_with_count = await service.get_watchlists_with_count(user_id)
    return {
        "success": True,
        "data": [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "is_default": w.is_default,
                "sort_num": w.sort_num if w.sort_num is not None else 0,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "stock_count": stock_count,
            }
            for w, stock_count in watchlists_with_count
        ],
    }


@router.get("/stocks/all", response_model=dict)
async def get_all_watchlist_stocks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(30, ge=1, le=1000, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（ts_code或股票名称）"),
    industry: Optional[str] = Query(None, description="板块筛选"),
    watchlist_id: Optional[int] = Query(None, description="分组筛选"),
    tags: Optional[str] = Query(None, description="标签筛选（逗号分隔）"),
    sort_by_change_pct: Optional[str] = Query(
        None, description="按涨幅排序: asc, desc"
    ),
    market_type: Optional[str] = Query(
        None, description="市场类型: main=主板, chye=创业板, kcb=科创板"
    ),
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    result = service.get_all_watchlist_stocks(
        page=page,
        page_size=page_size,
        search=search,
        industry=industry,
        watchlist_id=watchlist_id,
        tags=tags_list,
        sort_by_change_pct=sort_by_change_pct,
        market_type=market_type,
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "success": True,
        "data": result["stocks"],
        "pagination": result["pagination"],
        "stats": result.get("stats", {"up": 0, "down": 0}),
    }


@router.get("/stats/overview", response_model=dict)
async def get_watchlist_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics for watchlist stocks"""
    from sqlalchemy import func, case, select
    from app.models import WatchlistStock

    result = await db.execute(
        select(
            func.count(WatchlistStock.id).label("total"),
            func.sum(case((WatchlistStock.status == 1, 1), else_=0)).label("hot"),
            func.sum(case((WatchlistStock.status == 2, 1), else_=0)).label("silent"),
        )
    )
    row = result.one()

    return {
        "success": True,
        "data": {
            "total_stocks": row.total,
            "hot_stocks": row.hot,
            "silent_stocks": row.silent,
        },
    }


class CheckStocksRequest(BaseModel):
    ts_codes: List[str]


@router.post("/check-stocks", response_model=dict)
async def check_stocks_in_watchlists(
    data: CheckStocksRequest, db: AsyncSession = Depends(get_db)
):
    """Check if stocks are already in any watchlist"""
    from sqlalchemy import select, distinct
    from app.models import WatchlistStock

    if not data.ts_codes:
        return {"success": True, "data": {"watched_codes": []}}

    result = await db.execute(
        select(distinct(WatchlistStock.ts_code)).where(
            WatchlistStock.ts_code.in_(data.ts_codes)
        )
    )
    watched_codes = [row[0] for row in result.all()]

    return {"success": True, "data": {"watched_codes": watched_codes}}


@router.get("/stocks/by-ts-code/{ts_code}", response_model=dict)
async def get_watchlist_stock_by_ts_code(
    ts_code: str, db: AsyncSession = Depends(get_db)
):
    """Get watchlist_stock record for a given ts_code, including watchlist name"""
    from sqlalchemy import select
    from app.models import WatchlistStock, Watchlist

    result = await db.execute(
        select(WatchlistStock, Watchlist.name.label("watchlist_name"))
        .join(Watchlist, WatchlistStock.watchlist_id == Watchlist.id)
        .where(WatchlistStock.ts_code == ts_code)
    )
    row = result.first()

    if not row:
        return {"success": True, "data": None}

    ws, watchlist_name = row
    return {
        "success": True,
        "data": {
            "id": ws.id,
            "watchlist_id": ws.watchlist_id,
            "watchlist_name": watchlist_name,
            "ts_code": ws.ts_code,
            "name": ws.name,
            "notes": ws.notes,
            "added_at": ws.added_at.isoformat() if ws.added_at else None,
            "watch_date": ws.watch_date,
            "watch_reason": ws.watch_reason,
            "status": ws.status,
        },
    }


@router.post("", response_model=dict)
async def create_watchlist(
    data: WatchlistCreate, user_id: str = "default", db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    watchlist = await service.create_watchlist(
        name=data.name,
        description=data.description,
        user_id=user_id,
        sort_num=data.sort_num,
    )
    return {
        "success": True,
        "data": {
            "id": watchlist.id,
            "name": watchlist.name,
            "description": watchlist.description,
            "is_default": watchlist.is_default,
            "sort_num": watchlist.sort_num if watchlist.sort_num is not None else 0,
            "created_at": watchlist.created_at.isoformat()
            if watchlist.created_at
            else None,
        },
    }


@router.get("/tags", response_model=dict)
async def get_all_tags(db: AsyncSession = Depends(get_db)):
    """Get all unique tags from stock_tags table"""
    service = WatchlistService(db)
    tags = await service.get_all_tags()
    return {
        "success": True,
        "data": {"tags": tags},
    }


@router.get("/{watchlist_id}", response_model=dict)
async def get_watchlist(watchlist_id: int, db: AsyncSession = Depends(get_db)):
    service = WatchlistService(db)
    watchlist = await service.get_watchlist(watchlist_id)

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return {
        "success": True,
        "data": {
            "id": watchlist.id,
            "name": watchlist.name,
            "description": watchlist.description,
            "is_default": watchlist.is_default,
            "created_at": watchlist.created_at.isoformat()
            if watchlist.created_at
            else None,
            "stocks": [
                {
                    "id": s.id,
                    "ts_code": s.ts_code,
                    "symbol": s.symbol,
                    "name": s.name,
                    "added_at": s.added_at.isoformat() if s.added_at else None,
                    "watch_date": s.watch_date,
                    "watch_reason": s.watch_reason,
                    "notes": s.notes,
                }
                for s in watchlist.stocks
            ],
        },
    }


@router.put("/{watchlist_id}", response_model=dict)
async def update_watchlist(
    watchlist_id: int, data: WatchlistUpdate, db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    watchlist = await service.update_watchlist(
        watchlist_id=watchlist_id,
        name=data.name,
        description=data.description,
        sort_num=data.sort_num,
    )

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return {
        "success": True,
        "data": {
            "id": watchlist.id,
            "name": watchlist.name,
            "description": watchlist.description,
            "sort_num": watchlist.sort_num if watchlist.sort_num is not None else 0,
        },
    }


@router.delete("/{watchlist_id}")
async def delete_watchlist(watchlist_id: int, db: AsyncSession = Depends(get_db)):
    service = WatchlistService(db)
    success = await service.delete_watchlist(watchlist_id)

    if not success:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return {"success": True}


@router.get("/{watchlist_id}/stocks", response_model=dict)
async def get_watchlist_stocks(
    watchlist_id: int,
    signal_date: Optional[str] = None,
    watch_date: Optional[str] = None,
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    watchlist = await service.get_watchlist(watchlist_id)

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    stocks = await service.get_stocks(
        watchlist_id, signal_date=signal_date, watch_date=watch_date, limit=limit
    )

    ts_codes = [s.ts_code for s in stocks]
    industries = service.get_stock_industries(ts_codes)
    tags = service.get_stock_tags(ts_codes)

    stock_data = []
    for s in stocks:
        stock_info = {
            "id": s.id,
            "ts_code": s.ts_code,
            "symbol": s.symbol,
            "name": s.name,
            "industry": industries.get(s.ts_code, ""),
            "added_at": s.added_at.isoformat() if s.added_at else None,
            "watch_date": s.watch_date,
            "watch_reason": s.watch_reason,
            "added_price": float(s.added_price) if s.added_price else None,
            "notes": s.notes,
            "alert_enabled": s.alert_enabled,
            "status": s.status if s.status else 1,
            "tags": tags.get(s.ts_code, []),
        }

        if signal_date and hasattr(s, "signal"):
            signal = s.signal
            stock_info["signal"] = {
                "signal_type": signal.signal_type if signal else None,
                "signal_strength": signal.signal_strength if signal else None,
                "current_price": float(signal.current_price)
                if signal and signal.current_price
                else None,
            }

        stock_data.append(stock_info)

    return {
        "success": True,
        "data": {
            "watchlist_id": watchlist.id,
            "watchlist_name": watchlist.name,
            "signal_date": signal_date,
            "watch_date": watch_date,
            "stocks": stock_data,
        },
    }


@router.post("/{watchlist_id}/stocks", response_model=dict)
async def add_stock_to_watchlist(
    watchlist_id: int, data: WatchlistStockCreate, db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)

    from app.services.stock_service import StockService

    stock_service = StockService()
    stock_detail = stock_service.get_stock_detail(data.ts_code)

    if not stock_detail:
        raise HTTPException(status_code=404, detail="Stock not found")

    stock = await service.add_stock(
        watchlist_id=watchlist_id,
        ts_code=data.ts_code,
        symbol=stock_detail["symbol"],
        name=stock_detail["name"],
        added_price=stock_detail.get("current_price"),
        notes=data.notes,
        watch_reason=data.watch_reason,
        watch_date=data.watch_date,
    )

    if not stock:
        raise HTTPException(status_code=400, detail="Stock already in watchlist")

    return {
        "success": True,
        "data": {
            "id": stock.id,
            "ts_code": stock.ts_code,
            "symbol": stock.symbol,
            "name": stock.name,
        },
    }


@router.post("/{watchlist_id}/stocks/batch", response_model=dict)
async def batch_add_stocks(
    watchlist_id: int,
    data: WatchlistStockBatchCreate,
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    stock_service = StockService()

    added = []
    failed = []

    for ts_code in data.ts_codes:
        try:
            stock_detail = stock_service.get_stock_detail(ts_code)
            if stock_detail:
                stock = await service.add_stock(
                    watchlist_id=watchlist_id,
                    ts_code=ts_code,
                    symbol=stock_detail["symbol"],
                    name=stock_detail["name"],
                )
                if stock:
                    added.append(ts_code)
                else:
                    failed.append({"ts_code": ts_code, "reason": "Already exists"})
            else:
                failed.append({"ts_code": ts_code, "reason": "Not found"})
        except Exception as e:
            failed.append({"ts_code": ts_code, "reason": str(e)})

    return {"success": True, "data": {"added": added, "failed": failed}}


@router.delete("/{watchlist_id}/stocks/{stock_id}")
async def remove_stock_from_watchlist(
    watchlist_id: int, stock_id: int, db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    success = await service.remove_stock(watchlist_id, stock_id)

    if not success:
        raise HTTPException(status_code=404, detail="Stock not found in watchlist")

    return {"success": True}


@router.get("/{watchlist_id}/dates", response_model=dict)
async def get_watchlist_available_dates(
    watchlist_id: int, db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    watchlist = await service.get_watchlist(watchlist_id)

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    from app.services.signal_service import SignalService

    signal_service = SignalService(db)
    dates = await signal_service.get_available_dates(watchlist_id)

    return {
        "success": True,
        "data": {
            "watchlist_id": watchlist.id,
            "watchlist_name": watchlist.name,
            "dates": dates,
        },
    }


@router.get("/{watchlist_id}/watch-reasons", response_model=dict)
async def get_watch_reasons_endpoint():
    """Get available watch reasons from config"""
    return {"success": True, "data": get_watch_reasons()}


@router.get("/{watchlist_id}/watch-dates", response_model=dict)
async def get_watch_dates(watchlist_id: int, db: AsyncSession = Depends(get_db)):
    """Get available watch dates for filtering"""
    service = WatchlistService(db)
    watchlist = await service.get_watchlist(watchlist_id)

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    dates = await service.get_watch_dates(watchlist_id)

    return {
        "success": True,
        "data": {
            "watchlist_id": watchlist.id,
            "watchlist_name": watchlist.name,
            "dates": dates,
        },
    }


@router.get("/{watchlist_id}/last-trading-day")
async def get_last_trading_day(
    watchlist_id: int, exchange: str = "SSE", db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    last_trading_day = await service.get_last_trading_day(exchange)

    return {
        "success": True,
        "data": {"last_trading_day": last_trading_day, "exchange": exchange},
    }


@router.put("/{watchlist_id}/stocks/{stock_id}/status", response_model=dict)
async def update_stock_status(
    watchlist_id: int, stock_id: int, status: int, db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    stock = await service.update_stock_status(watchlist_id, stock_id, status)

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found in watchlist")

    return {
        "success": True,
        "data": {
            "id": stock.id,
            "ts_code": stock.ts_code,
            "symbol": stock.symbol,
            "name": stock.name,
            "status": stock.status,
        },
    }


class WatchlistStockNotesUpdate(BaseModel):
    notes: Optional[str] = None


class StockTagsUpdate(BaseModel):
    tags: List[str]


class MoveStockRequest(BaseModel):
    target_watchlist_id: int
    reason: Optional[str] = None


class CreateSnapshotRequest(BaseModel):
    stocks: List[dict]


@router.put("/stocks/{stock_id}/notes", response_model=dict)
async def update_stock_notes(
    stock_id: int,
    data: WatchlistStockNotesUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新股票备注"""
    service = WatchlistService(db)
    stock = await service.update_stock_notes_by_id(stock_id, data.notes)

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found in watchlist")

    return {
        "success": True,
        "data": {
            "id": stock.id,
            "ts_code": stock.ts_code,
            "symbol": stock.symbol,
            "name": stock.name,
            "notes": stock.notes,
        },
    }


@router.put("/stocks/{stock_id}/move", response_model=dict)
async def move_stock_to_watchlist(
    stock_id: int, data: MoveStockRequest, db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)

    target_watchlist = await service.get_watchlist(data.target_watchlist_id)
    if not target_watchlist:
        raise HTTPException(status_code=404, detail="Target watchlist not found")

    stock = await service.move_stock_to_watchlist(stock_id, data.target_watchlist_id)

    if not stock:
        raise HTTPException(
            status_code=400,
            detail="Stock not found or already exists in target watchlist",
        )

    return {
        "success": True,
        "data": {
            "id": stock.id,
            "ts_code": stock.ts_code,
            "symbol": stock.symbol,
            "name": stock.name,
            "watchlist_id": stock.watchlist_id,
            "moved_to": target_watchlist.name,
        },
    }


@router.post("/{watchlist_id}/snapshots", response_model=dict)
async def create_watchlist_snapshot(
    watchlist_id: int, data: CreateSnapshotRequest, db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    watchlist = await service.get_watchlist(watchlist_id)

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    snapshot = await service.create_snapshot(watchlist_id, data.stocks)

    return {
        "success": True,
        "data": {
            "id": snapshot.id,
            "watchlist_id": snapshot.watchlist_id,
            "snapshot_date": snapshot.snapshot_date,
            "snapshot_time": snapshot.snapshot_time,
            "created_at": snapshot.created_at.isoformat()
            if snapshot.created_at
            else None,
        },
    }


@router.get("/{watchlist_id}/snapshots", response_model=dict)
async def get_watchlist_snapshots(
    watchlist_id: int, db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    watchlist = await service.get_watchlist(watchlist_id)

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    snapshots = await service.get_snapshots(watchlist_id)

    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "watchlist_id": s.watchlist_id,
                "snapshot_date": s.snapshot_date,
                "snapshot_time": s.snapshot_time,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "items": [
                    {
                        "id": item.id,
                        "ts_code": item.ts_code,
                        "name": item.name,
                        "industry": item.industry,
                        "notes": item.notes,
                    }
                    for item in s.items
                ],
            }
            for s in snapshots
        ],
    }


@router.delete("/{watchlist_id}/snapshots/{snapshot_id}")
async def delete_watchlist_snapshot(
    watchlist_id: int, snapshot_id: int, db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    watchlist = await service.get_watchlist(watchlist_id)

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    success = await service.delete_snapshot(snapshot_id)

    if not success:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return {"success": True}


@router.get("/stocks/{ts_code}/tags", response_model=dict)
async def get_stock_tags(
    ts_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Get tags for a specific stock"""
    service = WatchlistService(db)
    tags_map = service.get_stock_tags([ts_code])
    tags = tags_map.get(ts_code, [])
    return {
        "success": True,
        "data": {
            "ts_code": ts_code,
            "tags": tags,
        },
    }


@router.put("/stocks/{ts_code}/tags", response_model=dict)
async def update_stock_tags(
    ts_code: str,
    data: StockTagsUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    try:
        stock_tag = await service.update_stock_tags(ts_code, data.tags)
        return {
            "success": True,
            "data": {
                "ts_code": stock_tag.ts_code,
                "tags": stock_tag.tags,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

