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
                GROUP BY trade_date
            ) sr ON tc.cal_date = sr.trade_date
            ORDER BY tc.cal_date ASC
        """)

        params = {"days": days}
        if end_date:
            params["end_date"] = end_date

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
                AND industry IS NOT NULL
            GROUP BY trade_date, industry
            ORDER BY trade_date ASC, industry ASC
        """)
        industry_result = await db.execute(industry_sql, params)
        industry_rows = industry_result.fetchall()

        daily_industries = OrderedDict()
        for row in industry_rows:
            date = row[0]
            industry = row[1]
            count = row[2]
            if date not in daily_industries:
                daily_industries[date] = {}
            daily_industries[date][industry] = count

        dates = list(daily_industries.keys())
        all_industries = sorted(set(
            ind for day in daily_industries.values() for ind in day
        ))

        series = {}
        for ind in all_industries:
            vals = [daily_industries[d].get(ind, 0) for d in dates]
            vals = [v if v >= 2 else 0 for v in vals]
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
