from fastapi import APIRouter, Depends, HTTPException
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


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


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
    watchlists = await service.get_watchlists(user_id)
    return {
        "success": True,
        "data": [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "is_default": w.is_default,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in watchlists
        ],
    }


@router.post("", response_model=dict)
async def create_watchlist(
    data: WatchlistCreate, user_id: str = "default", db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    watchlist = await service.create_watchlist(
        name=data.name, description=data.description, user_id=user_id
    )
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
        },
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
        watchlist_id=watchlist_id, name=data.name, description=data.description
    )

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return {
        "success": True,
        "data": {
            "id": watchlist.id,
            "name": watchlist.name,
            "description": watchlist.description,
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

    stock_data = []
    for s in stocks:
        stock_info = {
            "id": s.id,
            "ts_code": s.ts_code,
            "symbol": s.symbol,
            "name": s.name,
            "added_at": s.added_at.isoformat() if s.added_at else None,
            "watch_date": s.watch_date,
            "watch_reason": s.watch_reason,
            "added_price": float(s.added_price) if s.added_price else None,
            "notes": s.notes,
            "alert_enabled": s.alert_enabled,
            "status": s.status if s.status else 1,
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

    dates = await service.get_available_dates(watchlist_id)

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
