from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.services.tag_service import TagService


router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreate(BaseModel):
    name: str
    description: Optional[str] = None


class TagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TagResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("", response_model=dict)
async def get_tags(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="标签名称搜索"),
    db: AsyncSession = Depends(get_db),
):
    service = TagService(db)
    result = await service.get_tags(page, page_size, name)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/all", response_model=dict)
async def get_all_tags(db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    tags = await service.get_all_tags()
    return {"success": True, "data": tags}


@router.get("/{tag_id}", response_model=dict)
async def get_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    tag = await service.get_tag(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {
        "success": True,
        "data": {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
            "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
        },
    }


@router.post("", response_model=dict)
async def create_tag(data: TagCreate, db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    tag = await service.create_tag(name=data.name, description=data.description)
    if not tag:
        raise HTTPException(status_code=400, detail="Tag name already exists")
    return {
        "success": True,
        "data": {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
            "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
        },
    }


@router.put("/{tag_id}", response_model=dict)
async def update_tag(tag_id: int, data: TagUpdate, db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    tag = await service.update_tag(
        tag_id=tag_id,
        name=data.name,
        description=data.description,
    )
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {
        "success": True,
        "data": {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
            "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
        },
    }


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    success = await service.delete_tag(tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"success": True}
