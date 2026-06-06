from typing import Dict, Optional
from sqlalchemy import text

from app.market.context import get_current_market
from app.market.filter import build_sql_filter


class MarketDataServiceMixin:
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

                market = get_current_market()
                market_sql, market_params = build_sql_filter(market, "d.ts_code")
                where_clauses.append(market_sql)
                params.update(market_params)

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

                market = get_current_market()
                market_sql, market_params = build_sql_filter(market, "w.ts_code")
                where_clauses.append(market_sql)
                params.update(market_params)

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
                            "pct_chg": float(row.pct_chg) * 100
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

    def get_stk_weekly_monthly(
        self,
        ts_code: str,
        freq: str = "week",
        limit: int = 60,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT 
                        trade_date as date,
                        open,
                        high,
                        low,
                        close,
                        pre_close,
                        vol as volume,
                        amount,
                        change,
                        pct_chg as change_pct
                    FROM weekly_data 
                    WHERE ts_code = :ts_code
                    ORDER BY trade_date DESC
                    LIMIT :limit
                """)
                result = conn.execute(query, {"ts_code": ts_code, "limit": limit})
                items = []
                for row in result:
                    change_pct = float(row.change_pct) if row.change_pct else 0
                    items.append(
                        {
                            "date": row.date.strftime("%Y-%m-%d") if row.date else None,
                            "open": float(row.open) if row.open is not None else None,
                            "high": float(row.high) if row.high is not None else None,
                            "low": float(row.low) if row.low is not None else None,
                            "close": float(row.close) if row.close is not None else None,
                            "pre_close": float(row.pre_close) if row.pre_close is not None else None,
                            "volume": float(row.volume) if row.volume is not None else None,
                            "amount": float(row.amount) if row.amount is not None else None,
                            "change": float(row.change) if row.change is not None else None,
                            "change_pct": change_pct,
                        }
                    )

                # weekly_data 最晚截止上周，从 stk_weekly_monthly 补充本周数据
                if items and freq == "week":
                    last_weekly_date = items[0].date
                    supplement_query = text("""
                        SELECT
                            trade_date as date,
                            open,
                            high,
                            low,
                            close,
                            pre_close,
                            vol as volume,
                            amount,
                            change,
                            pct_chg as change_pct
                        FROM stk_weekly_monthly
                        WHERE ts_code = :ts_code AND freq = 'week'
                        ORDER BY trade_date DESC
                        LIMIT 1
                    """)
                    supp_result = conn.execute(supplement_query, {"ts_code": ts_code})
                    supp_row = supp_result.fetchone()
                    if supp_row and supp_row.date and (not last_weekly_date or supp_row.date > last_weekly_date):
                        items.insert(0, {
                            "date": supp_row.date.strftime("%Y-%m-%d"),
                            "open": float(supp_row.open) if supp_row.open is not None else None,
                            "high": float(supp_row.high) if supp_row.high is not None else None,
                            "low": float(supp_row.low) if supp_row.low is not None else None,
                            "close": float(supp_row.close) if supp_row.close is not None else None,
                            "pre_close": float(supp_row.pre_close) if supp_row.pre_close is not None else None,
                            "volume": float(supp_row.volume) if supp_row.volume is not None else None,
                            "amount": float(supp_row.amount) if supp_row.amount is not None else None,
                            "change": float(supp_row.change) if supp_row.change is not None else None,
                            "change_pct": float(supp_row.change_pct) if supp_row.change_pct else 0,
                        })

                items.reverse()
                return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}
