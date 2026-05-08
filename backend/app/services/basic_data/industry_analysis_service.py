from typing import Dict, Optional
from sqlalchemy import text


class IndustryAnalysisServiceMixin:
    def get_incremental_industry(
        self,
        days: int = 20,
        min_growth_days: int = 3,
        end_date: Optional[str] = None,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                date_condition = "AND cal_date <= :end_date" if end_date else "AND cal_date <= CURRENT_DATE"
                query = f"""
                    WITH trade_dates AS (
                        SELECT cal_date
                        FROM trade_cal
                        WHERE exchange = 'SSE'
                        AND is_open = 1
                        {date_condition}
                        ORDER BY cal_date DESC
                        LIMIT :days
                    ),
                    industry_codes AS (
                        SELECT
                            industry,
                            CONCAT('ind_', ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) - 1) as code
                        FROM stock_basic
                        WHERE industry IS NOT NULL AND industry != ''
                        GROUP BY industry
                    )
                    SELECT
                        m.trade_date,
                        sb.industry,
                        ic.code as industry_code,
                        SUM(m.net_mf_amount) AS total_net_inflow
                    FROM moneyflow m
                    LEFT JOIN stock_basic sb ON sb.ts_code = m.ts_code
                    LEFT JOIN industry_codes ic ON ic.industry = sb.industry
                    WHERE m.trade_date IN (SELECT cal_date FROM trade_dates)
                        AND sb.industry IS NOT NULL
                        AND sb.industry != ''
                    GROUP BY m.trade_date, sb.industry, ic.code
                    ORDER BY m.trade_date ASC, sb.industry
                """
                
                params = {"days": days}
                if end_date:
                    params["end_date"] = end_date
                result = conn.execute(text(query), params)
                
                industry_data = {}
                date_set = set()
                
                for row in result:
                    date_str = row.trade_date.strftime("%Y-%m-%d")
                    date_set.add(date_str)
                    
                    industry = row.industry
                    if industry not in industry_data:
                        industry_data[industry] = {
                            "industry": industry,
                            "industry_code": row.industry_code,
                            "daily_data": {}
                        }
                    
                    net_inflow = float(row.total_net_inflow) if row.total_net_inflow is not None else 0
                    industry_data[industry]["daily_data"][date_str] = net_inflow / 10000
                
                sorted_dates = sorted(date_set)
                
                industries = []
                for industry, data in industry_data.items():
                    daily_values = []
                    cumulative_values = []
                    cumulative = 0
                    
                    for date in sorted_dates:
                        daily = data["daily_data"].get(date, 0)
                        daily_values.append(round(daily, 2))
                        cumulative += daily
                        cumulative_values.append(round(cumulative, 2))
                    
                    growth_days = 0
                    max_growth_days = 0
                    for i in range(1, len(cumulative_values)):
                        if cumulative_values[i] > cumulative_values[i-1]:
                            growth_days += 1
                            max_growth_days = max(max_growth_days, growth_days)
                        else:
                            growth_days = 0
                    
                    if len(cumulative_values) > 0 and cumulative_values[0] > 0:
                        max_growth_days = max(max_growth_days, 1)
                    
                    total_net_inflow = cumulative_values[-1] if cumulative_values else 0
                    
                    if total_net_inflow > 0 and max_growth_days >= min_growth_days:
                        industries.append({
                            "industry": industry,
                            "industry_code": data["industry_code"],
                            "daily_values": daily_values,
                            "cumulative_values": cumulative_values,
                            "total_net_inflow": round(total_net_inflow, 2),
                            "growth_days": max_growth_days
                        })
                
                industries.sort(key=lambda x: x["total_net_inflow"], reverse=True)
                
                return {
                    "success": True,
                    "data": {
                        "dates": sorted_dates,
                        "industries": industries
                    }
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "data": {"dates": [], "industries": []}}

    def get_hot_industries(
        self,
        trade_date: Optional[str] = None,
        min_amount: float = 1e8,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                date_params = {}
                if trade_date:
                    date_where = "d.trade_date = :trade_date"
                    date_params["trade_date"] = trade_date
                else:
                    date_where = """
                        d.trade_date = (
                            SELECT MAX(trade_date) FROM daily_data
                            WHERE trade_date <= CURRENT_DATE
                        )
                    """

                allowed_sort_fields = {
                    'industry', 'stock_count', 'total_amount',
                    'avg_amount', 'avg_pct_chg', 'amount_rank'
                }
                if sort_field and sort_field in allowed_sort_fields:
                    order_direction = 'DESC' if sort_order == 'descending' else 'ASC'
                    order_by = f"ORDER BY {sort_field} {order_direction}, industry"
                else:
                    order_by = "ORDER BY total_amount DESC, industry"

                query = f"""
                    WITH industry_amounts AS (
                        SELECT
                            s.industry,
                            COUNT(DISTINCT d.ts_code) AS stock_count,
                            SUM(d.amount) AS total_amount,
                            AVG(d.amount) AS avg_amount,
                            AVG(d.pct_chg) AS avg_pct_chg,
                            ROW_NUMBER() OVER (ORDER BY SUM(d.amount) DESC) AS amount_rank
                        FROM daily_data d
                        JOIN stock_basic s ON d.ts_code = s.ts_code
                        WHERE {date_where}
                            AND s.industry IS NOT NULL
                            AND s.industry != ''
                            AND s.name NOT LIKE '%%ST%%'
                            AND s.name NOT LIKE '%%退%%'
                        GROUP BY s.industry
                        HAVING SUM(d.amount) >= :min_amount
                    )
                    SELECT * FROM industry_amounts
                    {order_by}
                """
                date_params["min_amount"] = min_amount

                result = conn.execute(text(query), date_params)
                items = []
                for row in result:
                    items.append(
                        {
                            "industry": row.industry,
                            "stock_count": int(row.stock_count) if row.stock_count else 0,
                            "total_amount": float(row.total_amount) if row.total_amount is not None else 0,
                            "avg_amount": float(row.avg_amount) if row.avg_amount is not None else 0,
                            "avg_pct_chg": float(row.avg_pct_chg) if row.avg_pct_chg is not None else 0,
                            "amount_rank": int(row.amount_rank) if row.amount_rank else 0,
                        }
                    )

                if trade_date:
                    latest_date_str = trade_date
                else:
                    date_res = conn.execute(
                        text("SELECT MAX(trade_date) as latest_date FROM daily_data WHERE trade_date <= CURRENT_DATE")
                    )
                    latest_date = date_res.fetchone()
                    latest_date_str = latest_date[0].strftime("%Y-%m-%d") if latest_date and latest_date[0] else None

                return {
                    "success": True,
                    "data": items,
                    "meta": {
                        "trade_date": latest_date_str,
                        "min_amount": min_amount,
                        "total_industries": len(items),
                    }
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "data": [], "meta": {}}
