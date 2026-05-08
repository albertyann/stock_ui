from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.services.sector_service import SectorService


router = APIRouter(prefix="/sectors", tags=["sectors"])


@router.get("", response_model=dict)
async def get_all_sectors():
    """
    获取所有板块列表（行业）

    Returns:
        板块列表
    """
    service = SectorService()
    sectors = service.get_all_sectors()

    return {
        "success": True,
        "data": sectors,
        "count": len(sectors),
    }


@router.get("/concepts", response_model=dict)
async def get_concept_sectors(
    trade_date: Optional[str] = Query(None, description="交易日期，格式YYYY-MM-DD，默认为最新日期"),
    sector_type: Optional[str] = Query(None, description="板块类型: concept(概念板块), industry(行业板块), region(地域板块)，默认返回所有类型"),
):
    """
    获取板块列表（从 dc_index 表）

    Args:
        trade_date: 交易日期，不传则返回最新日期数据
        sector_type: 板块类型，不传则返回所有类型

    Returns:
        板块列表
    """
    service = SectorService()
    sectors = service.get_concept_sectors(trade_date=trade_date, sector_type=sector_type)

    return {
        "success": True,
        "data": sectors,
        "count": len(sectors),
    }


@router.get("/concepts/{ts_code}", response_model=dict)
async def get_concept_sector_detail(ts_code: str):
    """
    获取概念板块详情

    Args:
        ts_code: 板块代码

    Returns:
        板块详情
    """
    service = SectorService()
    sector = service.get_concept_sector_detail(ts_code)

    if not sector:
        raise HTTPException(status_code=404, detail="Concept sector not found")

    return {
        "success": True,
        "data": sector,
    }


@router.get("/concepts/{ts_code}/stocks", response_model=dict)
async def get_concept_sector_stocks(
    ts_code: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（股票名称或代码）"),
    sort: Optional[str] = Query("default", description="排序方式: default, asc(涨幅升序), desc(涨幅降序), volume_asc(成交量升序), volume_desc(成交量降序)"),
    trend: Optional[str] = Query(None, description="趋势过滤: up(上升), down(下降)"),
):
    """
    获取概念板块内的股票列表

    Args:
        ts_code: 板块代码
        page: 页码
        page_size: 每页数量
        search: 搜索关键词
        sort: 排序方式
        trend: 趋势过滤

    Returns:
        股票列表及分页信息
    """
    service = SectorService()

    sector = service.get_concept_sector_detail(ts_code)
    if not sector:
        raise HTTPException(status_code=404, detail="Concept sector not found")

    all_stocks = service.get_concept_sector_stocks(ts_code, sort=sort, trend=trend)

    if search:
        search_lower = search.lower()
        filtered_stocks = [
            s
            for s in all_stocks
            if search_lower in s.get("name", "").lower()
            or search_lower in s.get("symbol", "").lower()
            or search_lower in s.get("ts_code", "").lower()
        ]
    else:
        filtered_stocks = all_stocks

    total = len(filtered_stocks)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_stocks = filtered_stocks[start_idx:end_idx]

    return {
        "success": True,
        "data": {
            "sector": sector,
            "stocks": paginated_stocks,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        },
    }


@router.get("/large-orders", response_model=dict)
async def get_sector_large_orders(
    trade_date: str = Query(..., description="交易日期，格式YYYY-MM-DD"),
):
    """
    获取板块大单交易统计（按行业汇总）

    Args:
        trade_date: 交易日期

    Returns:
        板块大单统计数据
    """
    service = SectorService()
    data = service.get_sector_large_orders(trade_date)

    return {
        "success": True,
        "data": data,
        "count": len(data),
    }


@router.get("/{sector_code}", response_model=dict)
async def get_sector_detail(
    sector_code: str,
    sector_type: str = Query("industry", description="板块类型: industry, concept"),
):
    """
    获取板块详情

    Args:
        sector_code: 板块代码
        sector_type: 板块类型 (industry/concept)

    Returns:
        板块详情
    """
    service = SectorService()
    sector = service.get_sector_detail(sector_code, sector_type)

    if not sector:
        raise HTTPException(status_code=404, detail="Sector not found")

    return {
        "success": True,
        "data": sector,
    }


@router.get("/{sector_code}/stocks", response_model=dict)
async def get_sector_stocks(
    sector_code: str,
    sector_type: str = Query("industry", description="板块类型: industry, concept"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（股票名称或代码）"),
    sort: Optional[str] = Query("default", description="排序方式: default, asc(涨幅升序), desc(涨幅降序), volume_asc(成交量升序), volume_desc(成交量降序)"),
    trend: Optional[str] = Query(None, description="趋势过滤: up(上升), down(下降)"),
):
    """
    获取板块内的股票列表

    Args:
        sector_code: 板块代码
        sector_type: 板块类型
        page: 页码
        page_size: 每页数量
        search: 搜索关键词
        sort: 排序方式

    Returns:
        股票列表及分页信息
    """
    service = SectorService()

    if sector_type == "concept":
        sector = service.get_concept_sector_detail(sector_code)
    else:
        sector = service.get_sector_detail(sector_code, sector_type)

    if not sector:
        raise HTTPException(status_code=404, detail="Sector not found")

    if sector_type == "concept":
        all_stocks = service.get_concept_sector_stocks(sector_code, sort=sort, trend=trend)
    else:
        all_stocks = service.get_sector_stocks(sector_code, sector_type, sort=sort, trend=trend)

    # 搜索过滤
    if search:
        search_lower = search.lower()
        filtered_stocks = [
            s
            for s in all_stocks
            if search_lower in s.get("name", "").lower()
            or search_lower in s.get("symbol", "").lower()
            or search_lower in s.get("ts_code", "").lower()
        ]
    else:
        filtered_stocks = all_stocks

    # 分页
    total = len(filtered_stocks)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_stocks = filtered_stocks[start_idx:end_idx]

    return {
        "success": True,
        "data": {
            "sector": sector,
            "stocks": paginated_stocks,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        },
    }
