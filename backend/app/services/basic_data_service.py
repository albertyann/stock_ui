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

    def get_exchanges(self) -> List[str]:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT DISTINCT exchange FROM trade_cal ORDER BY exchange")
                )
                return [row.exchange for row in result if row.exchange]
        except Exception:
            return []
