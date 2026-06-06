from typing import Dict, Optional
from sqlalchemy import text

from app.market.context import get_current_market
from app.market.filter import build_sql_filter


class StockBasicServiceMixin:
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

                market = get_current_market()
                market_sql, market_params = build_sql_filter(market, "ts_code")
                where_clauses.append(market_sql)
                params.update(market_params)

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
