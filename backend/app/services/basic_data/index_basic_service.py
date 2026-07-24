from typing import Dict, Optional
from sqlalchemy import text


class IndexBasicServiceMixin:
    def get_index_daily_overview(self):
        """Get latest daily data for all enabled indices from index_sync_config.

        Joins index_sync_config with the most recent index_daily row per index.
        Returns cards-ready data: name, price, change_pct, etc.
        """
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT
                        c.ts_code,
                        c.name,
                        c.market,
                        d.trade_date,
                        d.open,
                        d.high,
                        d.low,
                        d.close,
                        d.pre_close,
                        d.pct_chg AS change_pct,
                        d.vol AS volume,
                        d.amount
                    FROM index_sync_config c
                    LEFT JOIN index_daily d
                        ON d.ts_code = c.ts_code
                       AND d.trade_date = (
                           SELECT MAX(trade_date)
                           FROM index_daily
                           WHERE ts_code = c.ts_code
                       )
                    WHERE c.enabled = true
                    ORDER BY c.ts_code
                """)
                rows = conn.execute(query).fetchall()
                items = []
                for row in rows:
                    items.append({
                        "ts_code": row.ts_code,
                        "name": row.name,
                        "market": row.market,
                        "date": str(row.trade_date) if row.trade_date else None,
                        "open": float(row.open) if row.open is not None else None,
                        "high": float(row.high) if row.high is not None else None,
                        "low": float(row.low) if row.low is not None else None,
                        "close": float(row.close) if row.close is not None else None,
                        "pre_close": float(row.pre_close) if row.pre_close is not None else None,
                        "volume": float(row.volume) if row.volume is not None else None,
                        "amount": float(row.amount) if row.amount is not None else None,
                        "change_pct": float(row.change_pct) if row.change_pct is not None else None,
                    })
                return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def get_index_basic(
        self,
        page: int = 1,
        page_size: int = 20,
        name: Optional[str] = None,
        ts_code: Optional[str] = None,
        market: Optional[str] = None,
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
                if market:
                    where_clauses.append("market = :market")
                    params["market"] = market

                where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

                count_query = f"SELECT COUNT(*) as total FROM index_basic {where_sql}"
                total = conn.execute(text(count_query), params).fetchone().total

                offset = (page - 1) * page_size
                query = f"""
                    SELECT ts_code, name, fullname, market, publisher,
                           index_type, category, base_date, base_point,
                           list_date, weight_rule, "desc", exp_date
                    FROM index_basic
                    {where_sql}
                    ORDER BY ts_code
                    LIMIT :limit OFFSET :offset
                """
                params["limit"] = page_size
                params["offset"] = offset

                result = conn.execute(text(query), params)
                items = []
                for row in result:
                    items.append({
                        "ts_code": row.ts_code,
                        "name": row.name,
                        "fullname": row.fullname,
                        "market": row.market,
                        "publisher": row.publisher,
                        "index_type": row.index_type,
                        "category": row.category,
                        "base_date": row.base_date,
                        "base_point": row.base_point,
                        "list_date": row.list_date,
                        "weight_rule": row.weight_rule,
                        "desc": row.desc,
                        "exp_date": row.exp_date,
                    })

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

    def get_index_daily_kline(
        self,
        ts_code: str,
        limit: int = 180,
    ):
        """获取指数日 K 线数据（来自 index_daily 表）。"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT
                            trade_date as date,
                            open,
                            high,
                            low,
                            close,
                            pre_close,
                            vol as volume,
                            amount,
                            pct_chg as change_pct
                        FROM index_daily
                        WHERE ts_code = :ts_code
                        ORDER BY trade_date DESC
                        LIMIT :limit
                    """),
                    {"ts_code": ts_code, "limit": limit},
                )
                items = []
                for row in result:
                    items.append({
                        "date": row.date.strftime("%Y-%m-%d") if row.date else None,
                        "open": float(row.open) if row.open is not None else None,
                        "high": float(row.high) if row.high is not None else None,
                        "low": float(row.low) if row.low is not None else None,
                        "close": float(row.close) if row.close is not None else None,
                        "pre_close": float(row.pre_close) if row.pre_close is not None else None,
                        "volume": float(row.volume) if row.volume is not None else None,
                        "amount": float(row.amount) if row.amount is not None else None,
                        "change_pct": float(row.change_pct) if row.change_pct is not None else None,
                    })
                return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}
