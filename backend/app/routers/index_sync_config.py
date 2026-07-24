from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import IndexSyncConfig
from app.config import get_settings

router = APIRouter(
    prefix="/index-sync-configs",
    tags=["index-sync-configs"],
    dependencies=[Depends(require_admin)],
)


class IndexSyncConfigCreate(BaseModel):
    ts_code: str = Field(..., min_length=1, max_length=20, description="指数 TS 代码")
    name: Optional[str] = Field(None, max_length=100, description="指数名称")
    market: Optional[str] = Field(None, max_length=20, description="市场")


class IndexSyncConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    market: Optional[str] = Field(None, max_length=20)
    enabled: Optional[bool] = None


def _config_to_dict(c: IndexSyncConfig) -> dict:
    return {
        "ts_code": c.ts_code,
        "name": c.name,
        "market": c.market,
        "enabled": c.enabled,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.get("", response_model=dict)
async def list_configs(
    enabled: Optional[bool] = Query(None, description="筛选启用状态"),
    db: AsyncSession = Depends(get_db),
):
    """List all configured index codes for sync."""
    stmt = select(IndexSyncConfig).order_by(IndexSyncConfig.ts_code)
    if enabled is not None:
        stmt = stmt.where(IndexSyncConfig.enabled == enabled)
    result = await db.execute(stmt)
    configs = result.scalars().all()
    return {"success": True, "data": [_config_to_dict(c) for c in configs]}


@router.post("", response_model=dict)
async def create_config(
    payload: IndexSyncConfigCreate, db: AsyncSession = Depends(get_db)
):
    """Add an index code to the sync config."""
    existing = await db.execute(
        select(IndexSyncConfig).where(IndexSyncConfig.ts_code == payload.ts_code)
    )
    if existing.scalar_one_or_none():
        return {"success": False, "error": f"指数 {payload.ts_code} 已存在"}

    # Try to fill missing info from index_basic if not provided
    name = payload.name
    market = payload.market
    if not name or not market:
        try:
            settings = get_settings()
            sync_url = settings.database_url.replace("+asyncpg", "")
            from sqlalchemy import create_engine

            engine = create_engine(sync_url)
            with engine.connect() as conn:
                row = conn.execute(
                    text(
                        "SELECT name, market FROM index_basic WHERE ts_code = :ts_code"
                    ),
                    {"ts_code": payload.ts_code},
                ).fetchone()
                if row:
                    if not name:
                        name = row.name
                    if not market:
                        market = row.market
            engine.dispose()
        except Exception:
            pass

    config = IndexSyncConfig(
        ts_code=payload.ts_code,
        name=name,
        market=market,
        enabled=True,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    return {"success": True, "data": _config_to_dict(config)}


@router.put("/{ts_code}", response_model=dict)
async def update_config(
    ts_code: str,
    payload: IndexSyncConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an index sync config (name, market, enabled)."""
    config = await db.get(IndexSyncConfig, ts_code)
    if not config:
        return {"success": False, "error": "配置不存在"}

    if payload.name is not None:
        config.name = payload.name
    if payload.market is not None:
        config.market = payload.market
    if payload.enabled is not None:
        config.enabled = payload.enabled

    await db.commit()
    await db.refresh(config)
    return {"success": True, "data": _config_to_dict(config)}


@router.delete("/{ts_code}", response_model=dict)
async def delete_config(ts_code: str, db: AsyncSession = Depends(get_db)):
    """Remove an index code from the sync config."""
    config = await db.get(IndexSyncConfig, ts_code)
    if not config:
        return {"success": False, "error": "配置不存在"}
    await db.delete(config)
    await db.commit()
    return {"success": True}


@router.get("/search", response_model=dict)
async def search_index_basic(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
):
    """Search index_basic table for index codes to add."""
    try:
        settings = get_settings()
        sync_url = settings.database_url.replace("+asyncpg", "")
        from sqlalchemy import create_engine

        engine = create_engine(sync_url)
        results = []
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT ts_code, name, market
                    FROM index_basic
                    WHERE ts_code ILIKE :q OR name ILIKE :q
                    ORDER BY ts_code
                    LIMIT :limit
                """
                ),
                {"q": f"%{q}%", "limit": limit},
            )
            for row in rows:
                results.append(
                    {
                        "ts_code": row.ts_code,
                        "name": row.name,
                        "market": row.market,
                    }
                )
        engine.dispose()
        return {"success": True, "data": results}
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
