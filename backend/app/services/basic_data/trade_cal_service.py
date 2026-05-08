from typing import Dict, Optional, List
from sqlalchemy import text


class TradeCalServiceMixin:
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

    def get_exchanges(self) -> List[str]:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT DISTINCT exchange FROM trade_cal ORDER BY exchange")
                )
                return [row.exchange for row in result if row.exchange]
        except Exception:
            return []
