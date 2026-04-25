from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from app.database import get_db
from app.services.signal_service import SignalService


router = APIRouter(prefix="/signals", tags=["signals"])


class SignalAnalyzeRequest(BaseModel):
    ts_codes: List[str]


class SignalExecuteRequest(BaseModel):
    execution_result: str


class SignalNoteRequest(BaseModel):
    ts_code: str
    note_content: str


class SignalTagRequest(BaseModel):
    ts_code: str
    tags: List[str]


@router.get("", response_model=dict)
async def get_signals(
    ts_code: Optional[str] = None,
    signal_type: Optional[str] = None,
    active_only: bool = True,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    service = SignalService(db)
    signals = await service.get_signals(
        ts_code=ts_code, signal_type=signal_type, active_only=active_only, limit=limit
    )

    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "ts_code": s.ts_code,
                "signal_type": s.signal_type,
                "signal_strength": s.signal_strength,
                "signal_date": s.signal_date.isoformat() if s.signal_date else None,
                "current_price": float(s.current_price) if s.current_price else None,
                "target_price": float(s.target_price) if s.target_price else None,
                "stop_loss_price": float(s.stop_loss_price)
                if s.stop_loss_price
                else None,
                "indicators": s.indicators,
                "strategy_name": s.strategy_name,
                "conditions_met": s.conditions_met,
                "is_active": s.is_active,
                "note_content": s.note_content,
                "execution_result": s.execution_result,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in signals
        ],
    }


def _serialize_signal(s) -> dict:
    return {
        "id": s.id,
        "ts_code": s.ts_code,
        "signal_type": s.signal_type,
        "signal_strength": s.signal_strength,
        "signal_date": s.signal_date.isoformat() if s.signal_date else None,
        "current_price": float(s.current_price) if s.current_price else None,
        "target_price": float(s.target_price) if s.target_price else None,
        "stop_loss_price": float(s.stop_loss_price) if s.stop_loss_price else None,
        "indicators": s.indicators,
        "strategy_name": s.strategy_name,
        "conditions_met": s.conditions_met,
        "is_active": s.is_active,
        "execution_result": s.execution_result,
        "note_content": s.note_content,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


@router.get("/manage", response_model=dict)
async def get_signals_manage(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ts_code: Optional[str] = None,
    signal_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    signal_date: Optional[date] = None,
    signal_date_start: Optional[date] = None,
    signal_date_end: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    service = SignalService(db)
    signals, total = await service.get_signals_paginated(
        page=page,
        page_size=page_size,
        ts_code=ts_code,
        signal_type=signal_type,
        is_active=is_active,
        signal_date=signal_date,
        signal_date_start=signal_date_start,
        signal_date_end=signal_date_end,
    )

    return {
        "success": True,
        "data": [_serialize_signal(s) for s in signals],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@router.delete("/{signal_id}", response_model=dict)
async def delete_signal(signal_id: int, db: AsyncSession = Depends(get_db)):
    service = SignalService(db)
    deleted = await service.delete_signal(signal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"success": True, "data": {"message": "Signal deleted"}}


@router.get("/latest/{ts_code}", response_model=dict)
async def get_latest_signal(ts_code: str, db: AsyncSession = Depends(get_db)):
    service = SignalService(db)
    signal = await service.get_latest_signal(ts_code)

    if not signal:
        return {"success": True, "data": None}

    return {
        "success": True,
        "data": {
            "id": signal.id,
            "ts_code": signal.ts_code,
            "signal_type": signal.signal_type,
            "signal_strength": signal.signal_strength,
            "signal_date": signal.signal_date.isoformat()
            if signal.signal_date
            else None,
            "indicators": signal.indicators,
            "note_content": signal.note_content,
        },
    }


@router.post("/analyze", response_model=dict)
async def analyze_stocks(
    data: SignalAnalyzeRequest, db: AsyncSession = Depends(get_db)
):
    service = SignalService(db)
    results = []

    for ts_code in data.ts_codes:
        try:
            analysis = await service.analyze_stock(ts_code)
            if "error" not in analysis:
                signal = await service.save_signal(analysis)
                results.append(
                    {
                        "ts_code": ts_code,
                        "signal_type": analysis["signal_type"],
                        "signal_strength": analysis["signal_strength"],
                    }
                )
            else:
                results.append({"ts_code": ts_code, "error": analysis["error"]})
        except Exception as e:
            results.append({"ts_code": ts_code, "error": str(e)})

    return {"success": True, "data": results}


@router.post("/analyze-all", response_model=dict)
async def analyze_all_watchlist_stocks(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models import WatchlistStock

    result = await db.execute(select(WatchlistStock.ts_code).distinct())
    ts_codes = [r[0] for r in result.all()]

    if not ts_codes:
        return {
            "success": True,
            "data": {"message": "No stocks in watchlists", "analyzed": 0},
        }

    service = SignalService(db)
    analyzed = 0
    errors = []

    for ts_code in ts_codes:
        try:
            analysis = await service.analyze_stock(ts_code)
            if "error" not in analysis:
                await service.save_signal(analysis)
                analyzed += 1
        except Exception as e:
            errors.append({"ts_code": ts_code, "error": str(e)})

    return {
        "success": True,
        "data": {"analyzed": analyzed, "total": len(ts_codes), "errors": errors},
    }


@router.put("/{signal_id}/execute", response_model=dict)
async def mark_signal_executed(
    signal_id: int, data: SignalExecuteRequest, db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from app.models import Signal
    from datetime import datetime

    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()

    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    signal.is_active = False
    signal.executed_at = datetime.now()
    signal.execution_result = data.execution_result

    await db.commit()

    return {"success": True, "data": {"message": "Signal marked as executed"}}


@router.post("/note", response_model=dict)
async def add_signal_note(data: SignalNoteRequest, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models import Signal, WatchlistStock
    from datetime import datetime, date

    from app.services.signal_service import SignalService

    service = SignalService(db)
    cached_price = await service.get_cached_price(data.ts_code)
    current_price = float(cached_price.close_price) if cached_price else None

    signal = Signal(
        ts_code=data.ts_code,
        signal_type="NOTE",
        signal_strength=0,
        signal_date=date.today(),
        current_price=current_price,
        note_content=data.note_content,
        is_active=True,
    )
    db.add(signal)

    ws_result = await db.execute(
        select(WatchlistStock).where(WatchlistStock.ts_code == data.ts_code)
    )
    watchlist_stock = ws_result.scalar_one_or_none()
    if watchlist_stock:
        watchlist_stock.notes = data.note_content

    await db.commit()
    await db.refresh(signal)

    try:
        from app.websockets.manager import broadcast_notes_updated
        await broadcast_notes_updated(data.ts_code, data.note_content)
    except Exception:
        pass

    return {
        "success": True,
        "data": {
            "id": signal.id,
            "ts_code": signal.ts_code,
            "signal_type": signal.signal_type,
            "note_content": signal.note_content,
            "signal_date": signal.signal_date.isoformat(),
            "created_at": signal.created_at.isoformat() if signal.created_at else None,
        },
    }


@router.post("/tag", response_model=dict)
async def add_signal_tag(data: SignalTagRequest, db: AsyncSession = Depends(get_db)):
    """添加标签信号"""
    from sqlalchemy import select
    from app.models import Signal
    from datetime import date

    from app.services.signal_service import SignalService

    service = SignalService(db)
    cached_price = await service.get_cached_price(data.ts_code)
    current_price = float(cached_price.close_price) if cached_price else None

    # 将标签列表转换为逗号分隔的字符串存储在 note_content
    tags_content = ", ".join(data.tags)

    signal = Signal(
        ts_code=data.ts_code,
        signal_type="ADD_TAG",
        signal_strength=0,
        signal_date=date.today(),
        current_price=current_price,
        note_content=tags_content,
        is_active=True,
    )
    db.add(signal)

    await db.commit()
    await db.refresh(signal)

    return {
        "success": True,
        "data": {
            "id": signal.id,
            "ts_code": signal.ts_code,
            "signal_type": signal.signal_type,
            "note_content": signal.note_content,
            "signal_date": signal.signal_date.isoformat(),
            "created_at": signal.created_at.isoformat() if signal.created_at else None,
        },
    }
