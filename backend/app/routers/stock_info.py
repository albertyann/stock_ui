from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import StockInfo


router = APIRouter(prefix="/stock-info", tags=["stock-info"])


class StockInfoCreate(BaseModel):
    ts_code: str
    memo: Optional[str] = None


class StockInfoUpdate(BaseModel):
    memo: Optional[str] = None


def serialize_stock_info(info: StockInfo) -> dict:
    return {
        "id": info.id,
        "ts_code": info.ts_code,
        "memo": info.memo,
        "created_at": info.created_at.isoformat() if info.created_at else None,
        "updated_at": info.updated_at.isoformat() if info.updated_at else None,
    }


@router.get("/{ts_code}", response_model=dict)
async def get_stock_infos(
    ts_code: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(StockInfo).where(StockInfo.ts_code == ts_code).order_by(StockInfo.created_at.desc())
    result = await db.execute(stmt)
    infos = result.scalars().all()
    return {"success": True, "data": [serialize_stock_info(info) for info in infos]}


@router.post("/", response_model=dict)
async def create_stock_info(
    data: StockInfoCreate,
    db: AsyncSession = Depends(get_db),
):
    stock_info = StockInfo(ts_code=data.ts_code, memo=data.memo)
    db.add(stock_info)
    await db.commit()
    await db.refresh(stock_info)
    return {"success": True, "data": serialize_stock_info(stock_info)}


@router.put("/{info_id}", response_model=dict)
async def update_stock_info(
    info_id: int,
    data: StockInfoUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(StockInfo).where(StockInfo.id == info_id)
    result = await db.execute(stmt)
    stock_info = result.scalar_one_or_none()

    if not stock_info:
        raise HTTPException(status_code=404, detail="Stock info not found")

    update_data = {}
    if data.memo is not None:
        update_data["memo"] = data.memo

    if update_data:
        update_stmt = (
            update(StockInfo)
            .where(StockInfo.id == info_id)
            .values(**update_data)
        )
        await db.execute(update_stmt)
        await db.commit()
        await db.refresh(stock_info)

    return {"success": True, "data": serialize_stock_info(stock_info)}


@router.delete("/{info_id}", response_model=dict)
async def delete_stock_info(
    info_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(StockInfo).where(StockInfo.id == info_id)
    result = await db.execute(stmt)
    stock_info = result.scalar_one_or_none()

    if not stock_info:
        raise HTTPException(status_code=404, detail="Stock info not found")

    await db.delete(stock_info)
    await db.commit()
    return {"success": True}
