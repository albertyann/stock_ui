from typing import Dict
from sqlalchemy import text


class FinaIndicatorServiceMixin:
    """季度业绩（财务指标）查询 Mixin。

    基于 fina_indicator 表（tushare 财务指标表，已计算好同比/环比）。
    数据为累计口径（Q1/H1/Q3/年报），同比字段已天然消除累计效应，
    可直接用于判断盈亏趋势。
    """

    def get_fina_indicator(self, ts_code: str, limit: int = 8) -> Dict:
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT ts_code, end_date, ann_date,
                           dt_eps, dt_netprofit_yoy, or_yoy, q_sales_yoy,
                           netprofit_margin, grossprofit_margin,
                           roe, q_roe
                    FROM fina_indicator
                    WHERE ts_code = :ts_code
                    ORDER BY end_date DESC
                    LIMIT :limit
                """)
                result = conn.execute(query, {"ts_code": ts_code, "limit": limit})
                items = []
                for row in result:
                    items.append({
                        "ts_code": row.ts_code,
                        "end_date": row.end_date.strftime("%Y-%m-%d") if row.end_date else None,
                        "ann_date": row.ann_date.strftime("%Y-%m-%d") if row.ann_date else None,
                        "dt_eps": float(row.dt_eps) if row.dt_eps is not None else None,
                        "dt_netprofit_yoy": float(row.dt_netprofit_yoy) if row.dt_netprofit_yoy is not None else None,
                        "or_yoy": float(row.or_yoy) if row.or_yoy is not None else None,
                        "q_sales_yoy": float(row.q_sales_yoy) if row.q_sales_yoy is not None else None,
                        "netprofit_margin": float(row.netprofit_margin) if row.netprofit_margin is not None else None,
                        "grossprofit_margin": float(row.grossprofit_margin) if row.grossprofit_margin is not None else None,
                        "roe": float(row.roe) if row.roe is not None else None,
                        "q_roe": float(row.q_roe) if row.q_roe is not None else None,
                    })
                return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}
