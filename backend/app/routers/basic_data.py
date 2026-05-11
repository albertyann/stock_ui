from fastapi import APIRouter, Query
from typing import Optional

from app.services.basic_data import BasicDataService


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


@router.get("/trade-cal/last", response_model=dict)
async def get_last_trade_date(
    exchange: Optional[str] = Query("SSE", description="交易所代码，默认SSE"),
):
    service = BasicDataService()
    result = service.get_last_trade_date(exchange)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": None}
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
    industry: Optional[str] = Query(None, description="行业筛选"),
):
    service = BasicDataService()
    result = service.get_stock_basic(page, page_size, name, ts_code, symbol, industry)
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


@router.get("/stk-weekly-monthly/{ts_code}", response_model=dict)
async def get_stk_weekly_monthly(
    ts_code: str,
    freq: str = Query("week", description="频率: week=周线, month=月线"),
    limit: int = Query(60, ge=1, le=500, description="最近N条"),
):
    service = BasicDataService()
    result = service.get_stk_weekly_monthly(ts_code, freq, limit)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/moneyflow/{ts_code}", response_model=dict)
async def get_moneyflow(
    ts_code: str,
    limit: int = Query(20, ge=1, le=200, description="最近N个交易日"),
):
    service = BasicDataService()
    result = service.get_moneyflow(ts_code, limit)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/moneyflow-ind-ths/history", response_model=dict)
async def get_moneyflow_ind_ths_history(
    ts_codes: str = Query(..., description="行业代码，逗号分隔，如 801010.SI,801020.SI"),
    days: int = Query(60, ge=1, le=500, description="最近N个交易日"),
):
    service = BasicDataService()
    result = service.get_moneyflow_ind_ths_history(ts_codes, days)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/moneyflow-ind-ths/industries", response_model=dict)
async def get_moneyflow_ind_ths_industries():
    service = BasicDataService()
    result = service.get_moneyflow_ind_ths_industries()
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/moneyflow-ind-ths", response_model=dict)
async def get_moneyflow_ind_ths(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    industry: Optional[str] = Query(None, description="行业名称搜索"),
    trade_date: Optional[str] = Query(None, description="交易日期搜索，格式YYYY-MM-DD"),
    ts_code: Optional[str] = Query(None, description="行业代码搜索"),
    sort_field: Optional[str] = Query(None, description="排序字段"),
    sort_order: Optional[str] = Query(None, description="排序方向: ascending/descending"),
):
    service = BasicDataService()
    result = service.get_moneyflow_ind_ths(page, page_size, industry, trade_date, ts_code, sort_field, sort_order)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/capital-flow", response_model=dict)
async def get_capital_flow(
    days: int = Query(20, ge=1, le=90, description="统计天数"),
    industry: Optional[str] = Query(None, description="行业名称搜索"),
    ts_code: Optional[str] = Query(None, description="行业代码搜索"),
    sort_field: Optional[str] = Query(None, description="排序字段"),
    sort_order: Optional[str] = Query(None, description="排序方向: ascending/descending"),
):
    service = BasicDataService()
    result = service.get_capital_flow(days, industry, ts_code, sort_field, sort_order)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/industry-daily-flow", response_model=dict)
async def get_industry_daily_flow(
    trade_date: Optional[str] = Query(None, description="交易日期，格式YYYY-MM-DD"),
    days: int = Query(30, ge=1, le=90, description="查询天数"),
    industry: Optional[str] = Query(None, description="行业名称搜索"),
    sort_field: Optional[str] = Query(None, description="排序字段"),
    sort_order: Optional[str] = Query(None, description="排序方向: ascending/descending"),
):
    service = BasicDataService()
    result = service.get_industry_daily_flow(trade_date, days, industry, sort_field, sort_order)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/incremental-industry", response_model=dict)
async def get_incremental_industry(
    days: int = Query(20, ge=5, le=60, description="查询天数，默认20"),
    min_growth_days: int = Query(3, ge=1, le=20, description="最少连续增长天数"),
    end_date: Optional[str] = Query(None, description="截止日期，格式YYYY-MM-DD，默认为今天"),
):
    service = BasicDataService()
    result = service.get_incremental_industry(days, min_growth_days, end_date)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": []}
    return result


@router.get("/hot-industries", response_model=dict)
async def get_hot_industries(
    trade_date: Optional[str] = Query(None, description="交易日期，格式YYYY-MM-DD，默认最新交易日"),
    min_amount: float = Query(1e8, ge=0, description="最小成交额阈值，默认1亿（1e8元）"),
    sort_field: Optional[str] = Query(None, description="排序字段: industry, stock_count, total_amount, avg_amount, avg_pct_chg, amount_rank"),
    sort_order: Optional[str] = Query(None, description="排序方向: ascending/descending"),
):
    service = BasicDataService()
    result = service.get_hot_industries(trade_date, min_amount, sort_field, sort_order)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": [], "meta": {}}
    return result


@router.get("/sector-heat", response_model=dict)
async def get_sector_heat(
    trade_date: Optional[str] = Query(None, description="交易日期，格式YYYY-MM-DD，默认最新交易日"),
    tab: str = Query("up_pct", description="Tab类型: up_pct=上涨占比排名, amount=成交额排名"),
    idx_type: Optional[str] = Query(None, description="板块类型过滤，如 概念板块"),
    min_stocks: Optional[int] = Query(None, description="最小板块股票数量"),
):
    service = BasicDataService()
    result = service.get_sector_heat(trade_date, tab, idx_type, min_stocks)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": [], "meta": {}}
    return result


@router.get("/industry-stock-moneyflow", response_model=dict)
async def get_industry_stock_moneyflow(
    industry: str = Query(..., description="行业名称"),
    trade_date: Optional[str] = Query(None, description="交易日期，格式YYYY-MM-DD，默认最新交易日"),
    limit: int = Query(100, ge=1, le=500, description="返回条数限制"),
):
    service = BasicDataService()
    result = service.get_industry_stock_moneyflow(industry, trade_date, limit)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": [], "meta": {}}
    return result


@router.get("/cyq-chips/{ts_code}", response_model=dict)
async def get_cyq_chips(
    ts_code: str,
    trade_date: Optional[str] = Query(None, description="交易日期，格式YYYY-MM-DD，默认最新有数据日期"),
):
    service = BasicDataService()
    result = service.get_cyq_chips(ts_code, trade_date)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": {"trade_date": None, "chips": [], "current_price": None}}
    return result


@router.get("/stock-capital-flow", response_model=dict)
async def get_stock_capital_flow(
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    limit: int = Query(20, ge=1, le=100, description="返回条数限制"),
    end_date: Optional[str] = Query(None, description="截止日期，格式YYYY-MM-DD"),
    ts_codes: Optional[str] = Query(None, description="指定股票代码，逗号分隔"),
):
    service = BasicDataService()
    code_list = [c.strip() for c in ts_codes.split(",") if c.strip()] if ts_codes else None
    result = service.get_stock_capital_flow(days, limit, end_date, code_list)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "data": {"dates": [], "stocks": []}}
    return result
