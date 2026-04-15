from fastapi import APIRouter, Query
from typing import Optional

from app.services.basic_data_service import BasicDataService


router = APIRouter(prefix="/basic-data", tags=["basic-data"])


@router.get("/trade-cal", response_model=dict)
async def get_trade_cal(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    exchange: Optional[str] = Query(None, description="交易所筛选"),
    cal_date: Optional[str] = Query(None, description="日期筛选，格式YYYY-MM-DD"),
):
    service = BasicDataService()
    result = service.get_trade_cal(page, page_size, exchange, cal_date)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/trade-cal/exchanges", response_model=dict)
async def get_exchanges():
    service = BasicDataService()
    exchanges = service.get_exchanges()
    return {"success": True, "data": exchanges}


@router.get("/stocks", response_model=dict)
async def get_stock_basic(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    name: Optional[str] = Query(None, description="股票名称搜索"),
    ts_code: Optional[str] = Query(None, description="ts_code搜索"),
    symbol: Optional[str] = Query(None, description="symbol搜索"),
):
    service = BasicDataService()
    result = service.get_stock_basic(page, page_size, name, ts_code, symbol)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/daily", response_model=dict)
async def get_daily_data(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    name: Optional[str] = Query(None, description="股票名称搜索"),
    ts_code: Optional[str] = Query(None, description="ts_code搜索"),
    trade_date: Optional[str] = Query(None, description="交易日期搜索，格式YYYY-MM-DD"),
):
    service = BasicDataService()
    result = service.get_daily_data(page, page_size, name, ts_code, trade_date)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/weekly", response_model=dict)
async def get_weekly_data(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    name: Optional[str] = Query(None, description="股票名称搜索"),
    ts_code: Optional[str] = Query(None, description="ts_code搜索"),
    trade_date: Optional[str] = Query(None, description="交易日期搜索，格式YYYY-MM-DD"),
):
    service = BasicDataService()
    result = service.get_weekly_data(page, page_size, name, ts_code, trade_date)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result
