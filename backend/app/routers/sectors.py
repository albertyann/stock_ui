from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.services.sector_service import SectorService


router = APIRouter(prefix="/sectors", tags=["sectors"])


@router.get("", response_model=dict)
async def get_all_sectors():
    """
    获取所有板块列表（行业和概念）

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
):
    """
    获取板块内的股票列表

    Args:
        sector_code: 板块代码
        sector_type: 板块类型
        page: 页码
        page_size: 每页数量
        search: 搜索关键词

    Returns:
        股票列表及分页信息
    """
    service = SectorService()

    # 获取板块详情
    sector = service.get_sector_detail(sector_code, sector_type)
    if not sector:
        raise HTTPException(status_code=404, detail="Sector not found")

    # 获取所有股票
    all_stocks = service.get_sector_stocks(sector_code, sector_type)

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
