from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.daily_score_service import DailyScoreService


router = APIRouter(prefix="/daily-scores", tags=["daily-scores"])
service = DailyScoreService()


class ScoreSummaryResponse(BaseModel):
    success: bool
    data: dict


class ScoreListResponse(BaseModel):
    success: bool
    data: list


class DateListResponse(BaseModel):
    success: bool
    data: list


@router.get("/dates", response_model=DateListResponse)
async def get_available_dates(
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    dates = await service.get_available_dates(db, limit=limit)
    return {"success": True, "data": [str(d) for d in dates]}


@router.get("/latest-date", response_model=dict)
async def get_latest_date(db: AsyncSession = Depends(get_db)):
    latest = await service.get_latest_trade_date(db)
    if not latest:
        return {"success": False, "error": "暂无评分数据"}
    return {"success": True, "data": str(latest)}


@router.get("/summary", response_model=ScoreSummaryResponse)
async def get_score_summary(
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD，默认最新"),
    db: AsyncSession = Depends(get_db),
):
    if trade_date:
        target_date = date.fromisoformat(trade_date)
    else:
        target_date = await service.get_latest_trade_date(db)
        if not target_date:
            return {"success": False, "data": {}}

    summary = await service.get_score_summary(db, target_date)
    summary["trade_date"] = str(target_date)
    return {"success": True, "data": summary}


@router.get("/scores", response_model=ScoreListResponse)
async def get_scores(
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD，默认最新"),
    direction: Optional[str] = Query(None, description="方向过滤: bullish/bearish/neutral"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    if trade_date:
        target_date = date.fromisoformat(trade_date)
    else:
        target_date = await service.get_latest_trade_date(db)
        if not target_date:
            return {"success": False, "data": []}

    scores = await service.get_scores_by_date(db, target_date, direction=direction, limit=limit)
    data = [
        {
            "ts_code": s.ts_code,
            "name": s.name,
            "industry": s.industry,
            "trade_date": str(s.trade_date),
            "trend_score": float(s.trend_score) if s.trend_score else None,
            "momentum_score": float(s.momentum_score) if s.momentum_score else None,
            "volume_price_score": float(s.volume_price_score) if s.volume_price_score else None,
            "composite_1d": float(s.composite_1d) if s.composite_1d else None,
            "composite_3d": float(s.composite_3d) if s.composite_3d else None,
            "composite_5d": float(s.composite_5d) if s.composite_5d else None,
            "composite_10d": float(s.composite_10d) if s.composite_10d else None,
            "direction_1d": s.direction_1d,
            "direction_3d": s.direction_3d,
            "direction_5d": s.direction_5d,
            "direction_10d": s.direction_10d,
            "rank_in_watchlist": s.rank_in_watchlist,
            "score_change_5d": float(s.score_change_5d) if s.score_change_5d else None,
        }
        for s in scores
    ]
    return {"success": True, "data": data}


@router.get("/{ts_code}/history", response_model=ScoreListResponse)
async def get_stock_history(
    ts_code: str,
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    scores = await service.get_stock_score_history(db, ts_code, limit=limit)
    data = [
        {
            "ts_code": s.ts_code,
            "name": s.name,
            "trade_date": str(s.trade_date),
            "composite_5d": float(s.composite_5d) if s.composite_5d else None,
            "direction_5d": s.direction_5d,
            "score_change_5d": float(s.score_change_5d) if s.score_change_5d else None,
        }
        for s in scores
    ]
    return {"success": True, "data": data}
