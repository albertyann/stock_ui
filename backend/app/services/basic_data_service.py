from typing import List, Dict, Optional
from sqlalchemy import create_engine, text
from app.config import get_settings


class BasicDataService:
    def __init__(self):
        self.settings = get_settings()
        self.sync_url = self.settings.database_url.replace("+asyncpg", "")
        self.engine = create_engine(self.sync_url)

    def get_trade_cal(
        self,
        page: int = 1,
        page_size: int = 20,
        exchange: Optional[str] = None,
        cal_date: Optional[str] = None,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                where_clauses = []
                params = {}

                if exchange:
                    where_clauses.append("exchange = :exchange")
                    params["exchange"] = exchange
                if cal_date:
                    where_clauses.append("cal_date = :cal_date")
                    params["cal_date"] = cal_date

                where_sql = ""
                if where_clauses:
                    where_sql = "WHERE " + " AND ".join(where_clauses)

                count_query = f"SELECT COUNT(*) as total FROM trade_cal {where_sql}"
                total = conn.execute(text(count_query), params).fetchone().total

                offset = (page - 1) * page_size
                query = f"""
                    SELECT exchange, cal_date, is_open, pretrade_date
                    FROM trade_cal
                    {where_sql}
                    ORDER BY cal_date DESC, exchange
                    LIMIT :limit OFFSET :offset
                """
                params["limit"] = page_size
                params["offset"] = offset

                result = conn.execute(text(query), params)
                items = []
                for row in result:
                    items.append(
                        {
                            "exchange": row.exchange,
                            "cal_date": row.cal_date.strftime("%Y-%m-%d")
                            if row.cal_date
                            else None,
                            "is_open": bool(row.is_open)
                            if row.is_open is not None
                            else None,
                            "pretrade_date": row.pretrade_date.strftime("%Y-%m-%d")
                            if row.pretrade_date
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

    def get_stock_basic(
        self,
        page: int = 1,
        page_size: int = 20,
        name: Optional[str] = None,
        ts_code: Optional[str] = None,
        symbol: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                where_clauses = []
                params = {}

                if name:
                    where_clauses.append("name ILIKE :name")
                    params["name"] = f"%{name}%"
                if ts_code:
                    where_clauses.append("ts_code ILIKE :ts_code")
                    params["ts_code"] = f"%{ts_code}%"
                if symbol:
                    where_clauses.append("symbol ILIKE :symbol")
                    params["symbol"] = f"%{symbol}%"
                if industry:
                    where_clauses.append("industry = :industry")
                    params["industry"] = industry

                where_sql = ""
                if where_clauses:
                    where_sql = "WHERE " + " AND ".join(where_clauses)

                count_query = f"SELECT COUNT(*) as total FROM stock_basic {where_sql}"
                total = conn.execute(text(count_query), params).fetchone().total

                offset = (page - 1) * page_size
                query = f"""
                    SELECT ts_code, symbol, name, industry,
                           market, list_date
                    FROM stock_basic
                    {where_sql}
                    ORDER BY ts_code
                    LIMIT :limit OFFSET :offset
                """
                params["limit"] = page_size
                params["offset"] = offset

                result = conn.execute(text(query), params)
                items = []
                for row in result:
                    items.append(
                        {
                            "ts_code": row.ts_code,
                            "symbol": row.symbol,
                            "name": row.name,
                            "industry": row.industry,
                            "market": row.market,
                            "list_date": row.list_date.strftime("%Y-%m-%d")
                            if row.list_date
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

    def get_daily_data(
        self,
        page: int = 1,
        page_size: int = 20,
        name: Optional[str] = None,
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                where_clauses = []
                params = {}

                if name:
                    where_clauses.append("sb.name ILIKE :name")
                    params["name"] = f"%{name}%"
                if ts_code:
                    where_clauses.append("d.ts_code ILIKE :ts_code")
                    params["ts_code"] = f"%{ts_code}%"
                if trade_date:
                    where_clauses.append("d.trade_date = :trade_date")
                    params["trade_date"] = trade_date

                where_sql = ""
                if where_clauses:
                    where_sql = "WHERE " + " AND ".join(where_clauses)

                count_query = f"""
                    SELECT COUNT(*) as total
                    FROM daily_data d
                    LEFT JOIN stock_basic sb ON d.ts_code = sb.ts_code
                    {where_sql}
                """
                total = conn.execute(text(count_query), params).fetchone().total

                offset = (page - 1) * page_size
                query = f"""
                    SELECT d.ts_code, sb.name, d.trade_date,
                           d.open, d.high, d.low, d.close,
                           d.pre_close, d.change, d.pct_chg, d.vol, d.amount
                    FROM daily_data d
                    LEFT JOIN stock_basic sb ON d.ts_code = sb.ts_code
                    {where_sql}
                    ORDER BY d.trade_date DESC, d.ts_code
                    LIMIT :limit OFFSET :offset
                """
                params["limit"] = page_size
                params["offset"] = offset

                result = conn.execute(text(query), params)
                items = []
                for row in result:
                    items.append(
                        {
                            "ts_code": row.ts_code,
                            "name": row.name,
                            "trade_date": row.trade_date.strftime("%Y-%m-%d")
                            if row.trade_date
                            else None,
                            "open": float(row.open) if row.open is not None else None,
                            "high": float(row.high) if row.high is not None else None,
                            "low": float(row.low) if row.low is not None else None,
                            "close": float(row.close)
                            if row.close is not None
                            else None,
                            "pre_close": float(row.pre_close)
                            if row.pre_close is not None
                            else None,
                            "change": float(row.change)
                            if row.change is not None
                            else None,
                            "pct_chg": float(row.pct_chg)
                            if row.pct_chg is not None
                            else None,
                            "vol": float(row.vol) if row.vol is not None else None,
                            "amount": float(row.amount)
                            if row.amount is not None
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

    def get_weekly_data(
        self,
        page: int = 1,
        page_size: int = 20,
        name: Optional[str] = None,
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                where_clauses = []
                params = {}

                if name:
                    where_clauses.append("sb.name ILIKE :name")
                    params["name"] = f"%{name}%"
                if ts_code:
                    where_clauses.append("w.ts_code ILIKE :ts_code")
                    params["ts_code"] = f"%{ts_code}%"
                if trade_date:
                    where_clauses.append("w.trade_date = :trade_date")
                    params["trade_date"] = trade_date

                where_sql = ""
                if where_clauses:
                    where_sql = "WHERE " + " AND ".join(where_clauses)

                count_query = f"""
                    SELECT COUNT(*) as total
                    FROM weekly_data w
                    LEFT JOIN stock_basic sb ON w.ts_code = sb.ts_code
                    {where_sql}
                """
                total = conn.execute(text(count_query), params).fetchone().total

                offset = (page - 1) * page_size
                query = f"""
                    SELECT w.ts_code, sb.name, w.trade_date,
                           w.open, w.high, w.low, w.close,
                           w.pre_close, w.change, w.pct_chg, w.vol, w.amount
                    FROM weekly_data w
                    LEFT JOIN stock_basic sb ON w.ts_code = sb.ts_code
                    {where_sql}
                    ORDER BY w.trade_date DESC, w.ts_code
                    LIMIT :limit OFFSET :offset
                """
                params["limit"] = page_size
                params["offset"] = offset

                result = conn.execute(text(query), params)
                items = []
                for row in result:
                    items.append(
                        {
                            "ts_code": row.ts_code,
                            "name": row.name,
                            "trade_date": row.trade_date.strftime("%Y-%m-%d")
                            if row.trade_date
                            else None,
                            "open": float(row.open) if row.open is not None else None,
                            "high": float(row.high) if row.high is not None else None,
                            "low": float(row.low) if row.low is not None else None,
                            "close": float(row.close)
                            if row.close is not None
                            else None,
                            "pre_close": float(row.pre_close)
                            if row.pre_close is not None
                            else None,
                            "change": float(row.change)
                            if row.change is not None
                            else None,
                            "pct_chg": float(row.pct_chg)
                            if row.pct_chg is not None
                            else None,
                            "vol": float(row.vol) if row.vol is not None else None,
                            "amount": float(row.amount)
                            if row.amount is not None
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

    def get_moneyflow(
        self,
        ts_code: str,
        limit: int = 20,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT trade_date,
                           buy_sm_amount, sell_sm_amount,
                           buy_md_amount, sell_md_amount,
                           buy_lg_amount, sell_lg_amount,
                           buy_elg_amount, sell_elg_amount,
                           net_mf_amount
                    FROM moneyflow
                    WHERE ts_code = :ts_code
                    ORDER BY trade_date DESC
                    LIMIT :limit
                """)
                result = conn.execute(query, {"ts_code": ts_code, "limit": limit})
                items = []
                for row in result:
                    items.append(
                        {
                            "trade_date": row.trade_date.strftime("%Y-%m-%d")
                            if row.trade_date
                            else None,
                            "buy_sm_amount": float(row.buy_sm_amount)
                            if row.buy_sm_amount is not None
                            else 0,
                            "sell_sm_amount": float(row.sell_sm_amount)
                            if row.sell_sm_amount is not None
                            else 0,
                            "buy_md_amount": float(row.buy_md_amount)
                            if row.buy_md_amount is not None
                            else 0,
                            "sell_md_amount": float(row.sell_md_amount)
                            if row.sell_md_amount is not None
                            else 0,
                            "buy_lg_amount": float(row.buy_lg_amount)
                            if row.buy_lg_amount is not None
                            else 0,
                            "sell_lg_amount": float(row.sell_lg_amount)
                            if row.sell_lg_amount is not None
                            else 0,
                            "buy_elg_amount": float(row.buy_elg_amount)
                            if row.buy_elg_amount is not None
                            else 0,
                            "sell_elg_amount": float(row.sell_elg_amount)
                            if row.sell_elg_amount is not None
                            else 0,
                            "net_mf_amount": float(row.net_mf_amount)
                            if row.net_mf_amount is not None
                            else 0,
                        }
                    )
                items.reverse()
                return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

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

    def get_last_trade_date(self, exchange: Optional[str] = "SSE") -> Dict:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT cal_date FROM trade_cal
                        WHERE exchange = :exchange
                        AND is_open = 1
                        AND cal_date <= CURRENT_DATE
                        ORDER BY cal_date DESC
                        LIMIT 1
                    """),
                    {"exchange": exchange},
                )
                row = result.fetchone()
                if row and row.cal_date:
                    return {
                        "success": True,
                        "data": row.cal_date.strftime("%Y-%m-%d"),
                    }
                return {
                    "success": False,
                    "error": "未找到交易日",
                    "data": None,
                }
        except Exception as e:
            return {"success": False, "error": str(e), "data": None}

    def get_industry_stock_moneyflow(
        self,
        industry: str,
        trade_date: Optional[str] = None,
        limit: int = 100,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                params = {"industry": industry, "limit": limit}

                if trade_date:
                    date_condition = "m.trade_date = (:trade_date)::date"
                    params["trade_date"] = trade_date
                else:
                    date_condition = """
                        m.trade_date = (
                            SELECT MAX(m2.trade_date)
                            FROM moneyflow m2
                            JOIN stock_basic sb2 ON sb2.ts_code = m2.ts_code
                            WHERE sb2.industry = :industry
                        )
                    """

                query = text(f"""
                    SELECT
                        sb.ts_code,
                        sb.name,
                        sb.industry,
                        m.trade_date,
                        m.buy_sm_amount, m.sell_sm_amount,
                        m.buy_md_amount, m.sell_md_amount,
                        m.buy_lg_amount, m.sell_lg_amount,
                        m.buy_elg_amount, m.sell_elg_amount,
                        m.net_mf_amount
                    FROM moneyflow m
                    JOIN stock_basic sb ON sb.ts_code = m.ts_code
                    WHERE sb.industry = :industry
                    AND {date_condition}
                    ORDER BY m.net_mf_amount DESC
                    LIMIT :limit
                """)

                result = conn.execute(query, params)
                items = []
                for row in result:
                    items.append(
                        {
                            "ts_code": row.ts_code,
                            "name": row.name,
                            "industry": row.industry,
                            "trade_date": row.trade_date.strftime("%Y-%m-%d")
                            if row.trade_date
                            else None,
                            "buy_sm_amount": float(row.buy_sm_amount)
                            if row.buy_sm_amount is not None
                            else 0,
                            "sell_sm_amount": float(row.sell_sm_amount)
                            if row.sell_sm_amount is not None
                            else 0,
                            "buy_md_amount": float(row.buy_md_amount)
                            if row.buy_md_amount is not None
                            else 0,
                            "sell_md_amount": float(row.sell_md_amount)
                            if row.sell_md_amount is not None
                            else 0,
                            "buy_lg_amount": float(row.buy_lg_amount)
                            if row.buy_lg_amount is not None
                            else 0,
                            "sell_lg_amount": float(row.sell_lg_amount)
                            if row.sell_lg_amount is not None
                            else 0,
                            "buy_elg_amount": float(row.buy_elg_amount)
                            if row.buy_elg_amount is not None
                            else 0,
                            "sell_elg_amount": float(row.sell_elg_amount)
                            if row.sell_elg_amount is not None
                            else 0,
                            "net_mf_amount": float(row.net_mf_amount)
                            if row.net_mf_amount is not None
                            else 0,
                        }
                    )

                return {
                    "success": True,
                    "data": items,
                    "meta": {
                        "industry": industry,
                        "trade_date": items[0]["trade_date"] if items else trade_date,
                        "total": len(items),
                    },
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "data": [], "meta": {}}

    def get_stock_capital_flow(
        self,
        days: int = 30,
        limit: int = 20,
        end_date: Optional[str] = None,
        ts_codes: Optional[List[str]] = None,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                date_params = {"days": days}
                if end_date:
                    date_condition = """
                        m.trade_date IN (
                            SELECT cal_date FROM trade_cal
                            WHERE exchange = 'SSE'
                            AND is_open = 1
                            AND cal_date <= :end_date
                            ORDER BY cal_date DESC
                            LIMIT :days
                        )
                    """
                    date_params["end_date"] = end_date
                else:
                    date_condition = """
                        m.trade_date IN (
                            SELECT cal_date FROM trade_cal
                            WHERE exchange = 'SSE'
                            AND is_open = 1
                            AND cal_date <= CURRENT_DATE
                            ORDER BY cal_date DESC
                            LIMIT :days
                        )
                    """

                date_query = text(f"""
                    SELECT cal_date FROM trade_cal
                    WHERE exchange = 'SSE'
                    AND is_open = 1
                    {'AND cal_date <= :end_date' if end_date else 'AND cal_date <= CURRENT_DATE'}
                    ORDER BY cal_date DESC
                    LIMIT :days
                """)
                date_result = conn.execute(date_query, date_params)
                trade_dates = [row.cal_date.strftime("%Y-%m-%d") for row in date_result]
                trade_dates.sort()

                if not trade_dates:
                    return {"success": True, "data": {"dates": [], "stocks": []}}

                params = {"days": days}
                ts_code_filter = ""
                if ts_codes and len(ts_codes) > 0:
                    in_clauses = []
                    for i, code in enumerate(ts_codes):
                        key = f"ts_code_{i}"
                        in_clauses.append(f":{key}")
                        params[key] = code
                    ts_code_filter = f"AND m.ts_code IN ({', '.join(in_clauses)})"

                query = text(f"""
                    SELECT
                        m.ts_code,
                        sb.name,
                        sb.industry,
                        m.trade_date,
                        m.net_mf_amount,
                        d.pct_chg
                    FROM moneyflow m
                    JOIN stock_basic sb ON sb.ts_code = m.ts_code
                    LEFT JOIN daily_data d ON d.ts_code = m.ts_code AND d.trade_date = m.trade_date
                    WHERE {date_condition}
                    {ts_code_filter}
                    ORDER BY m.ts_code, m.trade_date ASC
                """)

                result = conn.execute(query, params)

                stock_data = {}
                for row in result:
                    ts_code = row.ts_code
                    date_str = row.trade_date.strftime("%Y-%m-%d")
                    net_mf = float(row.net_mf_amount) if row.net_mf_amount is not None else 0
                    pct_chg = float(row.pct_chg) if row.pct_chg is not None else None

                    # 修正逻辑：净流出为负但股价上涨时，将负金额改为正金额
                    if net_mf < 0 and pct_chg is not None and pct_chg > 0:
                        net_mf = -net_mf

                    if ts_code not in stock_data:
                        stock_data[ts_code] = {
                            "ts_code": ts_code,
                            "name": row.name,
                            "industry": row.industry,
                            "daily_data": {},
                        }
                    stock_data[ts_code]["daily_data"][date_str] = net_mf / 10000

                stocks = []
                for ts_code, data in stock_data.items():
                    daily_values = []
                    cumulative_values = []
                    cumulative = 0

                    for date in trade_dates:
                        daily = data["daily_data"].get(date, 0)
                        daily_values.append(round(daily, 2))
                        cumulative += daily
                        cumulative_values.append(round(cumulative, 2))

                    total_net_inflow = cumulative_values[-1] if cumulative_values else 0

                    stocks.append({
                        "ts_code": data["ts_code"],
                        "name": data["name"],
                        "industry": data["industry"],
                        "daily_values": daily_values,
                        "cumulative_values": cumulative_values,
                        "total_net_inflow": round(total_net_inflow, 2),
                    })

                stocks.sort(key=lambda x: x["total_net_inflow"], reverse=True)

                if ts_codes and len(ts_codes) > 0:
                    specified_stocks = [s for s in stocks if s["ts_code"] in ts_codes]
                    other_stocks = [s for s in stocks if s["ts_code"] not in ts_codes]
                    stocks = specified_stocks + other_stocks[:limit]
                else:
                    stocks = stocks[:limit]

                return {
                    "success": True,
                    "data": {
                        "dates": trade_dates,
                        "stocks": stocks,
                    }
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "data": {"dates": [], "stocks": []}}

    def get_exchanges(self) -> List[str]:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT DISTINCT exchange FROM trade_cal ORDER BY exchange")
                )
                return [row.exchange for row in result if row.exchange]
        except Exception:
            return []
