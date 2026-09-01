import json
import bisect
from datetime import date
from typing import Optional
from collections import OrderedDict
from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_admin
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db

router = APIRouter(
    prefix="/screening",
    tags=["screening"],
    dependencies=[Depends(require_admin)],
)


@router.get("/heat", response_model=dict)
async def get_screening_heat(
    days: int = Query(120, description="回溯天数"),
    end_date: Optional[str] = Query(None, description="截止日期 (YYYY-MM-DD)"),
    strategy_name: Optional[str] = Query(None, description="按策略筛选，如 HighScoreRsiStrong / RsiStrong"),
    db: AsyncSession = Depends(get_db),
):
    """获取选股结果热度：按天统计筛选出的股票数量，反映市场交易活跃度。"""
    try:
        if end_date:
            date_condition = "AND trade_date <= :end_date"
            cal_date_condition = "AND cal_date <= :end_date"
        else:
            date_condition = ""
            cal_date_condition = ""

        if strategy_name:
            strategy_condition = "AND strategy_name = :strategy_name"
        else:
            strategy_condition = ""

        sql = text(f"""
            SELECT
                tc.cal_date::TEXT AS trade_date,
                COALESCE(sr.stock_count, 0) AS stock_count
            FROM (
                SELECT DISTINCT cal_date
                FROM trade_cal
                WHERE is_open = 1
                    AND cal_date >= CURRENT_DATE - CAST(:days AS INTEGER) * INTERVAL '1 day'
                    {cal_date_condition}
            ) tc
            LEFT JOIN (
                SELECT
                    trade_date,
                    COUNT(DISTINCT ts_code) AS stock_count
                FROM screening_results
                WHERE trade_date >= CURRENT_DATE - CAST(:days AS INTEGER) * INTERVAL '1 day'
                    {date_condition}
                    {strategy_condition}
                GROUP BY trade_date
            ) sr ON tc.cal_date = sr.trade_date
            ORDER BY tc.cal_date ASC
        """)

        params = {"days": days}
        if end_date:
            # asyncpg 的 DATE 参数不接受字符串，需转为 date 对象
            params["end_date"] = date.fromisoformat(end_date)
        if strategy_name:
            params["strategy_name"] = strategy_name

        result = await db.execute(sql, params)
        rows = result.fetchall()

        data = [
            {"trade_date": row[0], "stock_count": row[1]}
            for row in rows
        ]

        total_dates = len(data)
        avg_count = round(sum(r["stock_count"] for r in data) / total_dates, 1) if total_dates > 0 else 0

        # ---------------- industry breakdown (stacked bar) ----------------
        industry_sql = text(f"""
            SELECT
                trade_date::TEXT,
                industry,
                COUNT(DISTINCT ts_code) AS stock_count
            FROM screening_results
            WHERE trade_date >= CURRENT_DATE - CAST(:days AS INTEGER) * INTERVAL '1 day'
                {date_condition}
                {strategy_condition}
                AND industry IS NOT NULL
            GROUP BY trade_date, industry
            ORDER BY trade_date ASC, industry ASC
        """)
        industry_result = await db.execute(industry_sql, params)
        industry_rows = industry_result.fetchall()

        daily_industries = OrderedDict()
        for row in industry_rows:
            trade_date = row[0]
            industry = row[1]
            count = row[2]
            if trade_date not in daily_industries:
                daily_industries[trade_date] = {}
            daily_industries[trade_date][industry] = count

        dates = list(daily_industries.keys())
        all_industries = sorted(set(
            ind for day in daily_industries.values() for ind in day
        ))

        series = {}
        for ind in all_industries:
            vals = [daily_industries[d].get(ind, 0) for d in dates]
            vals = [v if v >= 5 else 0 for v in vals]
            if any(v > 0 for v in vals):
                series[ind] = vals

        industry_data = {"dates": dates, "series": series}
        # ----------------------------------------------------------------

        return {
            "success": True,
            "data": data,
            "industry_data": industry_data,
            "meta": {
                "days": days,
                "total_dates": total_dates,
                "avg_stock_count": avg_count,
            },
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "data": [], "meta": {}}


@router.get("/results", response_model=dict)
async def get_screening_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    strategy_name: Optional[str] = None,
    industry: Optional[str] = None,
    ts_code: Optional[str] = None,
    name: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    min_score: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
):
    """分页查询选股结果，支持多条件筛选，按交易日降序、评分降序排列。"""
    try:
        conditions = []
        params: dict = {}

        if strategy_name:
            conditions.append("strategy_name = :strategy_name")
            params["strategy_name"] = strategy_name
        if industry:
            conditions.append("industry = :industry")
            params["industry"] = industry
        if ts_code:
            conditions.append("ts_code ILIKE :ts_code")
            params["ts_code"] = f"%{ts_code}%"
        if name:
            conditions.append("name ILIKE :name")
            params["name"] = f"%{name}%"
        if date_start:
            conditions.append("trade_date >= :date_start")
            params["date_start"] = date_start
        if date_end:
            conditions.append("trade_date <= :date_end")
            params["date_end"] = date_end
        if min_score is not None:
            conditions.append("score >= :min_score")
            params["min_score"] = min_score

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        count_sql = text(f"SELECT COUNT(*) AS total FROM screening_results {where}")
        count_result = await db.execute(count_sql, params)
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset

        sql = text(f"""
            SELECT id, strategy_name, ts_code, name, industry, score, trade_date, details, created_at
            FROM screening_results
            {where}
            ORDER BY trade_date DESC, score DESC, ts_code ASC
            LIMIT :limit OFFSET :offset
        """)
        result = await db.execute(sql, params)
        rows = result.fetchall()

        data = []
        for row in rows:
            details = row.details
            if isinstance(details, str):
                details = json.loads(details)
            data.append(
                {
                    "id": row.id,
                    "strategy_name": row.strategy_name,
                    "ts_code": row.ts_code,
                    "name": row.name,
                    "industry": row.industry,
                    "score": float(row.score) if row.score is not None else None,
                    "trade_date": row.trade_date.strftime("%Y-%m-%d") if row.trade_date else None,
                    "details": details,
                    "created_at": (
                        row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None
                    ),
                }
            )

        return {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e), "data": [], "pagination": {}}


@router.get("/results/meta", response_model=dict)
async def get_screening_results_meta(
    db: AsyncSession = Depends(get_db),
):
    """获取筛选下拉选项：策略列表、行业列表、最新交易日。"""
    try:
        strategy_sql = text("SELECT DISTINCT strategy_name FROM screening_results ORDER BY 1")
        strategy_result = await db.execute(strategy_sql)
        strategies = [row[0] for row in strategy_result.fetchall()]

        industry_sql = text(
            "SELECT DISTINCT industry FROM screening_results WHERE industry IS NOT NULL ORDER BY 1"
        )
        industry_result = await db.execute(industry_sql)
        industries = [row[0] for row in industry_result.fetchall()]

        latest_sql = text("SELECT MAX(trade_date) AS latest FROM screening_results")
        latest_result = await db.execute(latest_sql)
        latest = latest_result.scalar()

        return {
            "success": True,
            "data": {
                "strategies": strategies,
                "industries": industries,
                "latest_date": latest.strftime("%Y-%m-%d") if latest else None,
            },
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e), "data": {}}


@router.get("/strong-continuous", response_model=dict)
async def get_screening_strong_continuous(
    strategy_name: Optional[str] = Query("RsiStrong", description="策略名称"),
    days: int = Query(2, ge=2, le=5, description="连续天数（默认最近 2 天）"),
    min_score: float = Query(95, description="最低评分阈值"),
    db: AsyncSession = Depends(get_db),
):
    """连续强势信号：查最近 N 天评分均大于阈值的股票。

    策略固定为 RsiStrong（默认），取最近 `days` 个交易日，要求股票在每一天
    都有记录且评分 >= min_score（默认 95），即“连续强势”。
    """
    try:
        date_sql = text("""
            SELECT DISTINCT trade_date
            FROM screening_results
            WHERE strategy_name = :strategy_name
            ORDER BY trade_date DESC
            LIMIT :days
        """)
        date_result = await db.execute(
            date_sql, {"strategy_name": strategy_name, "days": days}
        )
        dates = [r[0] for r in date_result.fetchall()]

        if len(dates) < days:
            return {
                "success": True,
                "data": [],
                "dates": [d.strftime("%Y-%m-%d") for d in dates],
                "days": len(dates),
            }

        sql = text("""
            SELECT sr.ts_code, sr.name, sr.industry, sr.trade_date, sr.score
            FROM screening_results sr
            WHERE sr.strategy_name = :strategy_name
              AND sr.trade_date = ANY(:dates)
              AND sr.score >= :min_score
            ORDER BY sr.ts_code ASC, sr.trade_date ASC
        """)
        result = await db.execute(
            sql, {"strategy_name": strategy_name, "dates": dates, "min_score": min_score}
        )
        rows = result.fetchall()

        from collections import defaultdict

        stock_map = defaultdict(dict)
        for row in rows:
            stock_map[row.ts_code][row.trade_date] = (row.name, row.industry, float(row.score))

        date_strs = [d.strftime("%Y-%m-%d") for d in dates]

        data = []
        for ts_code, day_map in stock_map.items():
            if len(day_map) != len(dates):
                continue
            scores = OrderedDict()
            for d in dates:
                day_str = d.strftime("%Y-%m-%d")
                scores[day_str] = day_map[d][2]

            latest_date = max(dates)
            first_item = next(iter(day_map.values()))
            avg_score = round(sum(scores.values()) / len(scores), 2)
            data.append(
                {
                    "ts_code": ts_code,
                    "name": first_item[0],
                    "industry": first_item[1],
                    "scores": dict(scores),
                    "latest_score": day_map[latest_date][2],
                    "avg_score": avg_score,
                    "days_continuous": len(scores),
                }
            )

        data.sort(key=lambda x: x["avg_score"], reverse=True)

        return {
            "success": True,
            "data": data,
            "dates": date_strs,
            "days": len(dates),
            "meta": {"strategy_name": strategy_name, "min_score": min_score},
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e), "data": [], "dates": []}


@router.get("/trend", response_model=dict)
async def get_screening_trend(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    strategy_name: Optional[str] = None,
    industry: Optional[str] = None,
    ts_code: Optional[str] = None,
    name: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    min_score: Optional[float] = None,
    market_type: Optional[str] = Query(None, description="板块筛选：main/chye/kcb"),
    days: Optional[str] = Query(None, description="逗号分隔的 T+N 偏移，如 1,3,5,10,20"),
    db: AsyncSession = Depends(get_db),
):
    """分页查询选股信号，并计算信号日后 T+N 交易日的单日涨幅与前复权累计涨幅。"""
    try:
        if days:
            offsets = sorted({int(d.strip()) for d in days.split(",") if d.strip()})
            if any(n < 1 for n in offsets):
                raise ValueError("days 偏移必须为 >= 1 的整数")
            offsets = offsets[:10]
        else:
            offsets = [1, 3, 5, 10, 20]

        conditions = []
        params: dict = {}

        if strategy_name:
            conditions.append("strategy_name = :strategy_name")
            params["strategy_name"] = strategy_name
        if industry:
            conditions.append("industry = :industry")
            params["industry"] = industry
        if ts_code:
            conditions.append("ts_code ILIKE :ts_code")
            params["ts_code"] = f"%{ts_code}%"
        if name:
            conditions.append("name ILIKE :name")
            params["name"] = f"%{name}%"
        if date_start:
            conditions.append("trade_date >= :date_start")
            params["date_start"] = date_start
        if date_end:
            conditions.append("trade_date <= :date_end")
            params["date_end"] = date_end
        if min_score is not None:
            conditions.append("score >= :min_score")
            params["min_score"] = min_score
        if market_type:
            prefixes = {
                "main": ("600", "601", "603", "605", "000", "001", "002", "003"),
                "chye": ("300", "301"),
                "kcb": ("688", "689"),
            }.get(market_type)
            if prefixes:
                quoted = ", ".join(f"'{p}'" for p in prefixes)
                conditions.append(f"substring(ts_code, 1, 3) IN ({quoted})")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        count_sql = text(f"SELECT COUNT(*) AS total FROM screening_results {where}")
        count_result = await db.execute(count_sql, params)
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset

        sql = text(f"""
            SELECT id, strategy_name, ts_code, name, industry, score, trade_date
            FROM screening_results
            {where}
            ORDER BY trade_date DESC, score DESC, ts_code ASC
            LIMIT :limit OFFSET :offset
        """)
        result = await db.execute(sql, params)
        rows = result.fetchall()

        data = []
        trading_dates: dict = {}

        if rows:
            min_signal_date = min(row.trade_date for row in rows)

            cal_sql = text("""
                SELECT cal_date FROM trade_cal
                WHERE exchange = 'SSE' AND is_open = 1 AND cal_date >= :min_date
                ORDER BY cal_date ASC
            """)
            cal_result = await db.execute(cal_sql, {"min_date": min_signal_date})
            cal_dates = [r[0] for r in cal_result.fetchall()]

            def resolve_trade_date(base_date, n):
                """T+N = 基准日起（含）第 N 个开市交易日，与 realtime_service 语义一致。"""
                idx = bisect.bisect_left(cal_dates, base_date) + n
                return cal_dates[idx] if idx < len(cal_dates) else None

            all_offsets = [0] + offsets
            resolved = {}  # (signal_date, offset) -> resolved date or None
            date_set = set()
            code_set = set()
            for row in rows:
                code_set.add(row.ts_code)
                for n in all_offsets:
                    d = resolve_trade_date(row.trade_date, n)
                    resolved[(row.trade_date, n)] = d
                    if d is not None:
                        date_set.add(d)

            price_map = {}
            if code_set and date_set:
                price_sql = text("""
                    SELECT d.ts_code, d.trade_date, d.close, d.pct_chg, a.adj_factor
                    FROM daily_data d
                    LEFT JOIN adj_factor a ON d.ts_code = a.ts_code AND d.trade_date = a.trade_date
                    WHERE d.ts_code = ANY(:codes)
                    AND d.trade_date = ANY(:dates)
                    ORDER BY d.ts_code, d.trade_date
                """)
                price_result = await db.execute(
                    price_sql,
                    {"codes": list(code_set), "dates": list(date_set)},
                )
                for prow in price_result.fetchall():
                    date_str = prow.trade_date.strftime("%Y-%m-%d")
                    price_map[(prow.ts_code, date_str)] = {
                        "close": float(prow.close) if prow.close is not None else None,
                        "pct_chg": float(prow.pct_chg) if prow.pct_chg is not None else None,
                        "adj_factor": (
                            float(prow.adj_factor) if prow.adj_factor is not None else None
                        ),
                    }

            for row in rows:
                signal_date_str = row.trade_date.strftime("%Y-%m-%d")
                row_data = {
                    "id": row.id,
                    "strategy_name": row.strategy_name,
                    "ts_code": row.ts_code,
                    "name": row.name,
                    "industry": row.industry,
                    "score": float(row.score) if row.score is not None else None,
                    "signal_date": signal_date_str,
                }

                date_labels = {}
                for n in all_offsets:
                    d = resolved[(row.trade_date, n)]
                    date_labels[f"T+{n}"] = d.strftime("%Y-%m-%d") if d else None
                trading_dates[signal_date_str] = date_labels

                def price_at(n):
                    d = resolved[(row.trade_date, n)]
                    if d is None:
                        return None
                    return price_map.get((row.ts_code, d.strftime("%Y-%m-%d")))

                base = price_at(0)
                row_data["close_T+0"] = base["close"] if base else None
                row_data["change_T+0"] = (
                    round(base["pct_chg"], 2) if base and base["pct_chg"] is not None else None
                )

                for n in offsets:
                    info = price_at(n)
                    change = None
                    cumulative = None
                    if info:
                        if info["pct_chg"] is not None:
                            change = round(info["pct_chg"], 2)
                        if base and base["close"] and info["close"]:
                            adj_n = info["adj_factor"]
                            adj_0 = base["adj_factor"]
                            if adj_n is not None and adj_0 is not None:
                                cumulative = (
                                    (info["close"] * adj_n) / (base["close"] * adj_0) * 100 - 100
                                )
                            else:
                                cumulative = info["close"] / base["close"] * 100 - 100
                            cumulative = round(cumulative, 2)
                    row_data[f"change_T+{n}"] = change
                    row_data[f"cumulative_change_T+{n}"] = cumulative

                data.append(row_data)

        return {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
            "trading_dates": trading_dates,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "pagination": {},
            "trading_dates": {},
        }
