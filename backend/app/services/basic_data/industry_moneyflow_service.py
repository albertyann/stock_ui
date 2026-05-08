from typing import Dict, Optional
from sqlalchemy import text


class IndustryMoneyflowServiceMixin:
    def get_moneyflow_ind_ths(
        self,
        page: int = 1,
        page_size: int = 20,
        industry: Optional[str] = None,
        trade_date: Optional[str] = None,
        ts_code: Optional[str] = None,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                where_clauses = []
                params = {}

                if industry:
                    where_clauses.append("industry ILIKE :industry")
                    params["industry"] = f"%{industry}%"
                if trade_date:
                    where_clauses.append("trade_date = :trade_date")
                    params["trade_date"] = trade_date
                if ts_code:
                    where_clauses.append("ts_code ILIKE :ts_code")
                    params["ts_code"] = f"%{ts_code}%"

                where_sql = ""
                if where_clauses:
                    where_sql = "WHERE " + " AND ".join(where_clauses)

                count_query = f"SELECT COUNT(*) as total FROM moneyflow_ind_ths {where_sql}"
                total = conn.execute(text(count_query), params).fetchone().total

                allowed_sort_fields = {
                    'trade_date', 'ts_code', 'industry', 'lead_stock',
                    'close', 'pct_change', 'company_num',
                    'pct_change_stock', 'close_price',
                    'net_buy_amount', 'net_sell_amount', 'net_amount'
                }
                if sort_field and sort_field in allowed_sort_fields:
                    order_direction = 'DESC' if sort_order == 'descending' else 'ASC'
                    order_by = f"ORDER BY {sort_field} {order_direction}, trade_date DESC, ts_code"
                else:
                    order_by = "ORDER BY net_amount DESC, trade_date DESC, ts_code"

                offset = (page - 1) * page_size
                query = f"""
                    SELECT trade_date, ts_code, industry, lead_stock,
                           close, pct_change, company_num,
                           pct_change_stock, close_price,
                           net_buy_amount, net_sell_amount, net_amount
                    FROM moneyflow_ind_ths
                    {where_sql}
                    {order_by}
                    LIMIT :limit OFFSET :offset
                """
                params["limit"] = page_size
                params["offset"] = offset

                result = conn.execute(text(query), params)
                items = []
                for row in result:
                    items.append(
                        {
                            "trade_date": row.trade_date.strftime("%Y-%m-%d")
                            if row.trade_date
                            else None,
                            "ts_code": row.ts_code,
                            "industry": row.industry,
                            "lead_stock": row.lead_stock,
                            "close": float(row.close) if row.close is not None else None,
                            "pct_change": float(row.pct_change)
                            if row.pct_change is not None
                            else None,
                            "company_num": int(row.company_num)
                            if row.company_num is not None
                            else None,
                            "pct_change_stock": float(row.pct_change_stock)
                            if row.pct_change_stock is not None
                            else None,
                            "close_price": float(row.close_price)
                            if row.close_price is not None
                            else None,
                            "net_buy_amount": float(row.net_buy_amount)
                            if row.net_buy_amount is not None
                            else None,
                            "net_sell_amount": float(row.net_sell_amount)
                            if row.net_sell_amount is not None
                            else None,
                            "net_amount": float(row.net_amount)
                            if row.net_amount is not None
                            else None,
                        }
                    )

                return {
                    "success": True,
                    "data": items,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "total_pages": (total + page_size - 1) // page_size,
                    },
                }
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def get_moneyflow_ind_ths_industries(self) -> Dict:
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT DISTINCT ts_code, industry
                    FROM moneyflow_ind_ths
                    WHERE ts_code IS NOT NULL AND industry IS NOT NULL
                    ORDER BY ts_code
                """)
                result = conn.execute(query)
                items = []
                for row in result:
                    items.append(
                        {
                            "ts_code": row.ts_code,
                            "name": row.industry,
                        }
                    )
                return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def get_moneyflow_ind_ths_history(
        self,
        ts_codes: str,
        days: int = 60,
    ) -> Dict:
        try:
            code_list = [c.strip() for c in ts_codes.split(",") if c.strip()]
            if not code_list:
                return {"success": False, "error": "ts_codes不能为空", "data": []}

            with self.engine.connect() as conn:
                params = {}
                in_clauses = []
                for i, code in enumerate(code_list):
                    key = f"ts_code_{i}"
                    in_clauses.append(f":{key}")
                    params[key] = code
                in_sql = ", ".join(in_clauses)
                params["days"] = days

                query = text(f"""
                    SELECT ts_code, industry, trade_date, net_amount
                    FROM (
                        SELECT ts_code, industry, trade_date, net_amount,
                               ROW_NUMBER() OVER (PARTITION BY ts_code ORDER BY trade_date DESC) AS rn
                        FROM moneyflow_ind_ths
                        WHERE ts_code IN ({in_sql})
                    ) sub
                    WHERE rn <= :days
                    ORDER BY ts_code, trade_date ASC
                """)

                result = conn.execute(query, params)

                items = []
                for row in result:
                    items.append(
                        {
                            "ts_code": row.ts_code,
                            "industry": row.industry,
                            "trade_date": row.trade_date.strftime("%Y-%m-%d")
                            if row.trade_date
                            else None,
                            "net_amount": float(row.net_amount)
                            if row.net_amount is not None
                            else None,
                        }
                    )

                return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def get_capital_flow(
        self,
        days: int = 20,
        industry: Optional[str] = None,
        ts_code: Optional[str] = None,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                where_clauses = ["trade_date >= CURRENT_DATE - INTERVAL '%s days'" % days]
                params = {}

                if industry:
                    where_clauses.append("industry ILIKE :industry")
                    params["industry"] = f"%{industry}%"
                if ts_code:
                    where_clauses.append("ts_code ILIKE :ts_code")
                    params["ts_code"] = f"%{ts_code}%"

                where_sql = "WHERE " + " AND ".join(where_clauses)

                allowed_sort_fields = {
                    'ts_code', 'industry',
                    'total_inflow', 'total_outflow', 'total_net_inflow'
                }
                if sort_field and sort_field in allowed_sort_fields:
                    order_direction = 'DESC' if sort_order == 'descending' else 'ASC'
                    order_by = f"ORDER BY {sort_field} {order_direction}, ts_code"
                else:
                    order_by = "ORDER BY total_net_inflow ASC, ts_code"

                query = f"""
                    SELECT
                        ts_code,
                        industry,
                        SUM(net_buy_amount) AS total_inflow,
                        SUM(net_sell_amount) AS total_outflow,
                        SUM(net_amount) AS total_net_inflow
                    FROM moneyflow_ind_ths
                    {where_sql}
                    GROUP BY ts_code, industry
                    {order_by}
                """

                result = conn.execute(text(query), params)
                items = []
                for row in result:
                    items.append(
                        {
                            "ts_code": row.ts_code,
                            "industry": row.industry,
                            "total_inflow": float(row.total_inflow)
                            if row.total_inflow is not None
                            else 0,
                            "total_outflow": float(row.total_outflow)
                            if row.total_outflow is not None
                            else 0,
                            "total_net_inflow": float(row.total_net_inflow)
                            if row.total_net_inflow is not None
                            else 0,
                        }
                    )

                return {
                    "success": True,
                    "data": items,
                }
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def get_industry_daily_flow(
        self,
        trade_date: Optional[str] = None,
        days: int = 30,
        industry: Optional[str] = None,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                where_clauses = ["sb.industry IS NOT NULL", "sb.industry != ''"]
                params = {}

                if trade_date:
                    where_clauses.append("m.trade_date <= (:trade_date)::date")
                    where_clauses.append("m.trade_date >= (:trade_date)::date - INTERVAL '%s days'" % days)
                    params["trade_date"] = trade_date
                else:
                    where_clauses.append(
                        "m.trade_date >= CURRENT_DATE - INTERVAL '%s days'" % days
                    )

                if industry:
                    where_clauses.append("sb.industry ILIKE :industry")
                    params["industry"] = f"%{industry}%"

                where_sql = "WHERE " + " AND ".join(where_clauses)

                allowed_sort_fields = {
                    'trade_date', 'industry',
                    'total_net_inflow', 'total_buy_amount', 'total_sell_amount',
                    'stock_count'
                }
                if sort_field and sort_field in allowed_sort_fields:
                    order_direction = 'DESC' if sort_order == 'descending' else 'ASC'
                    order_by = f"ORDER BY {sort_field} {order_direction}, trade_date DESC, industry"
                else:
                    order_by = "ORDER BY trade_date DESC, total_net_inflow DESC"

                query = f"""
                    WITH industry_codes AS (
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
                        COUNT(DISTINCT m.ts_code) AS stock_count,
                        SUM(m.buy_sm_amount + m.buy_md_amount + m.buy_lg_amount + m.buy_elg_amount) AS total_buy_amount,
                        SUM(m.sell_sm_amount + m.sell_md_amount + m.sell_lg_amount + m.sell_elg_amount) AS total_sell_amount,
                        SUM(m.net_mf_amount) AS total_net_inflow
                    FROM moneyflow m
                    LEFT JOIN stock_basic sb ON sb.ts_code = m.ts_code
                    LEFT JOIN industry_codes ic ON ic.industry = sb.industry
                    {where_sql}
                    GROUP BY m.trade_date, sb.industry, ic.code
                    {order_by}
                """

                result = conn.execute(text(query), params)
                items = []
                for row in result:
                    net_inflow = float(row.total_net_inflow) if row.total_net_inflow is not None else 0
                    items.append(
                        {
                            "trade_date": row.trade_date.strftime("%Y-%m-%d")
                            if row.trade_date
                            else None,
                            "industry": row.industry,
                            "industry_code": row.industry_code,
                            "stock_count": int(row.stock_count) if row.stock_count else 0,
                            "total_buy_amount": float(row.total_buy_amount)
                            if row.total_buy_amount is not None
                            else 0,
                            "total_sell_amount": float(row.total_sell_amount)
                            if row.total_sell_amount is not None
                            else 0,
                            "total_net_inflow": net_inflow,
                        }
                    )

                return {
                    "success": True,
                    "data": items,
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "data": []}
