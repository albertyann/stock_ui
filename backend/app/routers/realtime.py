from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.services.realtime_service import RealtimePriceService


router = APIRouter(prefix="/realtime", tags=["realtime"])


class StockCodesRequest(BaseModel):
    ts_codes: str


class RefreshRequest(BaseModel):
    ts_codes: List[str]


class KlineRequest(BaseModel):
    ts_code: str
    period: str = "daily"
    limit: int = 60


@router.post("/prices", response_model=dict)
async def get_realtime_prices(request: StockCodesRequest):
    """
    获取股票最新价格数据（基于本地数据库）

    支持逗号或换行分隔的股票代码
    示例: "600000.SH,000001.SZ" 或 "600000\n000001"
    """
    service = RealtimePriceService()

    # 解析输入的股票代码
    ts_codes = service.parse_ts_codes_input(request.ts_codes)

    if not ts_codes:
        raise HTTPException(status_code=400, detail="No valid stock codes provided")

    if len(ts_codes) > 100:
        raise HTTPException(status_code=400, detail="Too many stock codes (max 100)")

    # 从本地数据库获取数据
    result = await service.get_realtime_prices(ts_codes)

    if not result.get("success"):
        raise HTTPException(
            status_code=500, detail=result.get("error", "Failed to fetch data")
        )

    return result


@router.post("/refresh", response_model=dict)
async def refresh_prices(request: RefreshRequest):
    """
    刷新指定股票的价格数据（从本地数据库重新查询）
    """
    service = RealtimePriceService()

    if not request.ts_codes:
        raise HTTPException(status_code=400, detail="No stock codes provided")

    if len(request.ts_codes) > 100:
        raise HTTPException(status_code=400, detail="Too many stock codes (max 100)")

    result = await service.get_realtime_prices(request.ts_codes)

    if not result.get("success"):
        raise HTTPException(
            status_code=500, detail=result.get("error", "Failed to fetch data")
        )

    return result


@router.get("/watchlist/{watchlist_id}", response_model=dict)
async def get_watchlist_prices(
    watchlist_id: int, include_kline: bool = Query(False, description="是否包含K线数据")
):
    """
    获取指定股票池中所有股票的最新价格

    Args:
        watchlist_id: 股票池ID
        include_kline: 是否同时返回K线数据
    """
    service = RealtimePriceService()

    # 获取股票池中的股票列表
    watchlist_stocks = service.get_watchlist_stocks(watchlist_id)

    if not watchlist_stocks:
        return {
            "success": True,
            "data": {
                "watchlist_id": watchlist_id,
                "stocks": [],
                "message": "No stocks found in this watchlist",
            },
        }

    # 提取股票代码
    ts_codes = [stock["ts_code"] for stock in watchlist_stocks]

    # 获取价格数据
    result = await service.get_realtime_prices(ts_codes)

    if not result.get("success"):
        raise HTTPException(
            status_code=500, detail=result.get("error", "Failed to fetch data")
        )

    response_data = {
        "watchlist_id": watchlist_id,
        "stock_count": len(watchlist_stocks),
        "stocks": result.get("data", []),
        "data_source": "local_db",
    }

    # 如果需要，添加K线数据
    if include_kline:
        kline_data = {}
        for ts_code in ts_codes:
            kline = service.get_kline_data(ts_code, period="daily", limit=30)
            kline_data[ts_code] = kline
        response_data["kline_data"] = kline_data

    return {"success": True, "data": response_data}


@router.get("/watchlists", response_model=dict)
async def get_all_watchlists_prices(
    include_kline: bool = Query(False, description="是否包含K线数据"),
):
    """
    获取所有股票池中股票的最新价格（去重）

    Args:
        include_kline: 是否同时返回K线数据
    """
    service = RealtimePriceService()

    # 获取所有股票池的股票列表
    watchlist_stocks = service.get_watchlist_stocks()

    if not watchlist_stocks:
        return {
            "success": True,
            "data": {"stocks": [], "message": "No stocks found in any watchlist"},
        }

    # 提取股票代码（去重）
    ts_codes = list(set([stock["ts_code"] for stock in watchlist_stocks]))

    # 获取价格数据
    result = await service.get_realtime_prices(ts_codes)

    if not result.get("success"):
        raise HTTPException(
            status_code=500, detail=result.get("error", "Failed to fetch data")
        )

    response_data = {
        "total_stocks": len(ts_codes),
        "watchlist_sources": list(set([s["watchlist_name"] for s in watchlist_stocks])),
        "stocks": result.get("data", []),
        "data_source": "local_db",
    }

    # 如果需要，添加K线数据
    if include_kline:
        kline_data = {}
        for ts_code in ts_codes[:20]:  # 限制K线查询数量
            kline = service.get_kline_data(ts_code, period="daily", limit=30)
            kline_data[ts_code] = kline
        response_data["kline_data"] = kline_data

    return {"success": True, "data": response_data}


@router.get("/{ts_code}/kline", response_model=dict)
async def get_stock_kline(
    ts_code: str,
    period: str = Query("daily", description="K线周期: daily, weekly, monthly"),
    limit: int = Query(60, ge=1, le=365, description="返回条数"),
):
    """
    获取单只股票的K线数据

    Args:
        ts_code: 股票代码，如 600000.SH
        period: K线周期
        limit: 返回条数
    """
    service = RealtimePriceService()

    # 标准化股票代码
    normalized_code = service.normalize_ts_code(ts_code)
    if not normalized_code:
        raise HTTPException(status_code=400, detail="Invalid stock code format")

    # 获取K线数据
    kline_data = service.get_kline_data(normalized_code, period=period, limit=limit)

    if not kline_data:
        return {
            "success": True,
            "data": {
                "ts_code": normalized_code,
                "period": period,
                "data": [],
                "message": "No kline data found",
            },
        }

    return {
        "success": True,
        "data": {
            "ts_code": normalized_code,
            "period": period,
            "count": len(kline_data),
            "data": kline_data,
        },
    }


@router.post("/batch/kline", response_model=dict)
async def get_batch_kline(
    ts_codes: List[str],
    period: str = Query("daily", description="K线周期: daily, weekly, monthly"),
    limit: int = Query(60, ge=1, le=365, description="返回条数"),
):
    """
    批量获取多只股票的K线数据

    Args:
        ts_codes: 股票代码列表
        period: K线周期
        limit: 返回条数
    """
    service = RealtimePriceService()

    if not ts_codes:
        raise HTTPException(status_code=400, detail="No stock codes provided")

    if len(ts_codes) > 20:
        raise HTTPException(
            status_code=400, detail="Too many stock codes (max 20 for batch kline)"
        )

    result_data = {}
    errors = []

    for ts_code in ts_codes:
        normalized_code = service.normalize_ts_code(ts_code)
        if not normalized_code:
            errors.append({"ts_code": ts_code, "error": "Invalid code format"})
            continue

        try:
            kline_data = service.get_kline_data(
                normalized_code, period=period, limit=limit
            )
            result_data[normalized_code] = kline_data
        except Exception as e:
            errors.append({"ts_code": normalized_code, "error": str(e)})

    return {
        "success": True,
        "data": {
            "period": period,
            "kline_data": result_data,
            "errors": errors if errors else None,
        },
    }


class StockQueryRequest(BaseModel):
    ts_codes: List[str]
    query_date: str
    days: Optional[List[int]] = None


@router.post("/query-by-date", response_model=dict)
async def query_stock_prices_by_date(request: StockQueryRequest):
    """
    查询指定股票在指定日期的价格，以及 T+N 交易日的价格和涨幅
    """
    service = RealtimePriceService()

    if not request.ts_codes:
        raise HTTPException(status_code=400, detail="No stock codes provided")

    if len(request.ts_codes) > 50:
        raise HTTPException(status_code=400, detail="Too many stock codes (max 50)")

    normalized_codes = []
    for code in request.ts_codes:
        normalized = service.normalize_ts_code(code)
        if normalized:
            normalized_codes.append(normalized)

    if not normalized_codes:
        raise HTTPException(status_code=400, detail="No valid stock codes provided")

    result = service.query_stock_prices_by_date(normalized_codes, request.query_date, request.days)

    if not result.get("success"):
        raise HTTPException(
            status_code=500, detail=result.get("error", "Failed to query data")
        )

    return result


@router.get("/limit-up", response_model=dict)
async def get_limit_up_stocks(
    min_change_pct: float = Query(9.9, description="最小涨幅百分比，默认9.9%"),
    limit: int = Query(200, ge=1, le=500, description="返回的最大股票数量"),
    trade_date: Optional[str] = Query(
        None, description="指定交易日，格式 YYYY-MM-DD，默认最新交易日"
    ),
    industry: Optional[str] = Query(None, description="板块/行业筛选"),
):
    """
    获取指定交易日的涨停股票（涨幅大于等于指定百分比）

    Args:
        min_change_pct: 最小涨幅百分比，默认9.9%（涨停）
        limit: 返回的最大股票数量
        trade_date: 指定交易日，格式 YYYY-MM-DD，默认最新交易日
        industry: 板块/行业筛选

    Returns:
        涨停股票列表及交易日信息
    """
    service = RealtimePriceService()

    result = service.get_limit_up_stocks(
        min_change_pct=min_change_pct,
        limit=limit,
        trade_date=trade_date,
        industry=industry,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500, detail=result.get("error", "Failed to fetch data")
        )

    return result


@router.get("/health", response_model=dict)
async def health_check():
    """
    检查实时股价服务状态
    """
    service = RealtimePriceService()

    # 测试数据库连接
    try:
        with service.engine.connect() as conn:
            result = conn.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "success": True,
        "data": {
            "status": "healthy" if db_status == "connected" else "unhealthy",
            "database": db_status,
            "data_source": "local_db",
            "mode": "non-realtime",  # 标记为非实时模式
        },
    }


@router.get("/{ts_code}/holder-number", response_model=dict)
async def get_stock_holder_number(
    ts_code: str,
    limit: int = Query(60, ge=1, le=365, description="返回条数"),
):
    """
    获取单只股票的股东人数数据

    Args:
        ts_code: 股票代码，如 600000.SH
        limit: 返回条数
    """
    service = RealtimePriceService()

    # 标准化股票代码
    normalized_code = service.normalize_ts_code(ts_code)
    if not normalized_code:
        raise HTTPException(status_code=400, detail="Invalid stock code format")

    # 获取股东人数数据
    holder_data = service.get_holder_number_data(normalized_code, limit=limit)

    if not holder_data:
        return {
            "success": True,
            "data": {
                "ts_code": normalized_code,
                "data": [],
                "message": "No holder number data found",
            },
        }

    return {
        "success": True,
        "data": {
            "ts_code": normalized_code,
            "count": len(holder_data),
            "data": holder_data,
        },
    }
