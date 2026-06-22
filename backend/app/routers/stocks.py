from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.services.stock_service import StockService


router = APIRouter(prefix="/stocks", tags=["stocks"])


class KlineParams(BaseModel):
    period: str = "daily"
    limit: int = 60


@router.get("/search", response_model=dict)
async def search_stocks(
    q: str = Query(..., description="Search keyword"),
    limit: int = Query(20, ge=1, le=100),
):
    service = StockService()
    results = service.search_stocks(q, limit)
    return {"success": True, "data": results}


@router.get("/{ts_code}", response_model=dict)
async def get_stock_detail(ts_code: str):
    service = StockService()
    stock = service.get_stock_detail(ts_code)

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    return {"success": True, "data": stock}


@router.get("/{ts_code}/kline", response_model=dict)
async def get_kline_data(
    ts_code: str,
    period: str = Query("daily", description="daily, weekly, monthly"),
    limit: int = Query(60, ge=1, le=365),
):
    service = StockService()
    kline = service.get_kline_data(ts_code, period, limit)

    return {
        "success": True,
        "data": {"ts_code": ts_code, "period": period, "data": kline},
    }


@router.get("/{ts_code}/weekly-kline", response_model=dict)
async def get_weekly_kline_data(
    ts_code: str,
    limit: int = Query(60, ge=1, le=200, description="返回周线条数"),
):
    service = StockService()
    kline = service.get_weekly_kline_data(ts_code, limit)
    return {"success": True, "data": kline}


@router.get("/{ts_code}/buy-signals", response_model=dict)
async def get_buy_signals(
    ts_code: str,
    check_days: int = Query(3, ge=1, le=30, description="检查最近 N 个交易日"),
):
    service = StockService()
    result = service.get_buy_signals(ts_code, check_days)
    return result


@router.post("/{ts_code}/sync-kline", response_model=dict)
async def sync_kline_data(ts_code: str):
    service = StockService()
    result = service.sync_kline_data(ts_code)
    return result
