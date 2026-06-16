from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.sync_task_service import SyncTaskService


router = APIRouter(prefix="/sync-tasks", tags=["sync-tasks"])


class SyncTaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    command: str = Field(default="stock-sync", max_length=50)
    sub_command: str = Field(default="run", max_length=50)
    task_type: str = Field(..., min_length=1, max_length=50)
    params: dict = Field(default_factory=dict)
    description: Optional[str] = None
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class SyncTaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    command: Optional[str] = Field(None, max_length=50)
    sub_command: Optional[str] = Field(None, max_length=50)
    task_type: Optional[str] = Field(None, min_length=1, max_length=50)
    params: Optional[dict] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ExecutePayload(BaseModel):
    params: Optional[dict] = Field(default_factory=dict)


@router.get("", response_model=dict)
async def list_tasks(db: AsyncSession = Depends(get_db)):
    service = SyncTaskService(db)
    tasks = await service.get_all_tasks()
    return {"success": True, "data": tasks}


@router.get("/logs", response_model=dict)
async def get_logs(
    task_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = SyncTaskService(db)
    result = await service.get_logs(task_name=task_name, page=page, page_size=page_size)
    return {"success": True, "data": result}


@router.post("", response_model=dict)
async def create_task(payload: SyncTaskCreate, db: AsyncSession = Depends(get_db)):
    service = SyncTaskService(db)
    task = await service.create_task(payload.model_dump())
    return {"success": True, "data": task}


@router.get("/available-types", response_model=dict)
async def get_available_types():
    """List all available sync task types from 'stock-sync ls'."""
    result = await SyncTaskService.get_available_task_types()
    return result


@router.get("/{task_id}", response_model=dict)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    service = SyncTaskService(db)
    task = await service.get_task(task_id)
    if not task:
        return {"success": False, "error": "Task not found", "data": None}
    return {"success": True, "data": task}


@router.put("/{task_id}", response_model=dict)
async def update_task(
    task_id: int, payload: SyncTaskUpdate, db: AsyncSession = Depends(get_db)
):
    service = SyncTaskService(db)
    data = {
        k: v
        for k, v in payload.model_dump().items()
        if v is not None or k in ["params", "is_active", "sort_order"]
    }
    if payload.params is not None:
        data["params"] = payload.params
    if payload.is_active is not None:
        data["is_active"] = payload.is_active
    if payload.sort_order is not None:
        data["sort_order"] = payload.sort_order
    task = await service.update_task(task_id, data)
    if not task:
        return {"success": False, "error": "Task not found", "data": None}
    return {"success": True, "data": task}


@router.delete("/{task_id}", response_model=dict)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    service = SyncTaskService(db)
    deleted = await service.delete_task(task_id)
    if not deleted:
        return {"success": False, "error": "Task not found"}
    return {"success": True}


@router.post("/{task_id}/execute", response_model=dict)
async def execute_task(
    task_id: int, payload: ExecutePayload, db: AsyncSession = Depends(get_db)
):
    service = SyncTaskService(db)
    result = await service.execute_task(task_id, payload.params)
    return result
