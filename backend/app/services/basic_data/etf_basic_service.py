from typing import Dict, Optional
from sqlalchemy import text


class EtfBasicServiceMixin:
    def _get_etf_exchange(
        self, ts_code: str
    ) -> Optional[str]:
        """根据 ts_code 查询 etf_basic 获取交易所代码."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT exchange FROM etf_basic WHERE ts_code = :ts_code"),
                    {"ts_code": ts_code},
                )
                row = result.fetchone()
                return row.exchange if row else None
        except Exception:
            return None

    def get_etf_daily_kline(
        self,
        ts_code: str,
        limit: int = 180,
    ) -> Dict:
        """获取 ETF 日 K 线数据（来自 etf_fund_daily 表）。"""
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
                        FROM etf_fund_daily
                        WHERE ts_code = :ts_code
                        ORDER BY trade_date ASC
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

    def get_etf_constituents(
        self,
        ts_code: str,
    ) -> Dict:
        """获取 ETF 成分股，根据交易所查询对应表（SZ → etf_sz_cons, SH → etf_sh_cons）。"""
        try:
            exchange = self._get_etf_exchange(ts_code)
            if not exchange:
                return {"success": False, "error": "ETF not found", "data": []}

            exchange = exchange.upper()
            if exchange in ("SZSE", "SZ"):
                table = "etf_sz_cons"
            elif exchange in ("SSE", "SH"):
                table = "etf_sh_cons"
            else:
                return {"success": False, "error": f"Unsupported exchange: {exchange}", "data": []}

            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"""
                        SELECT
                            con_code,
                            con_name,
                            qty,
                            sub_flag,
                            cpr,
                            rdr,
                            trade_date
                        FROM {table}
                        WHERE ts_code = :ts_code
                        ORDER BY con_code
                    """),
                    {"ts_code": ts_code},
                )
                items = []
                for row in result:
                    items.append({
                        "con_code": row.con_code,
                        "con_name": row.con_name,
                        "qty": row.qty,
                        "sub_flag": row.sub_flag,
                        "cpr": float(row.cpr) if row.cpr is not None else None,
                        "rdr": float(row.rdr) if row.rdr is not None else None,
                        "trade_date": row.trade_date.strftime("%Y-%m-%d") if row.trade_date else None,
                    })
                return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}
    def get_etf_basic(
        self,
        page: int = 1,
        page_size: int = 20,
        name: Optional[str] = None,
        ts_code: Optional[str] = None,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                where_clauses = []
                params = {}

                if name:
                    where_clauses.append("csname ILIKE :name")
                    params["name"] = f"%{name}%"
                if ts_code:
                    where_clauses.append("ts_code ILIKE :ts_code")
                    params["ts_code"] = f"%{ts_code}%"

                where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

                count_query = f"SELECT COUNT(*) as total FROM etf_basic {where_sql}"
                total = conn.execute(text(count_query), params).fetchone().total

                offset = (page - 1) * page_size
                query = f"""
                    SELECT ts_code, csname, extname, cname,
                           index_code, index_name, setup_date, list_date,
                           list_status, exchange, mgr_name, custod_name,
                           mgt_fee, etf_type
                    FROM etf_basic
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
                            "csname": row.csname,
                            "extname": row.extname,
                            "cname": row.cname,
                            "index_code": row.index_code,
                            "index_name": row.index_name,
                            "setup_date": row.setup_date.strftime("%Y-%m-%d")
                            if row.setup_date
                            else None,
                            "list_date": row.list_date.strftime("%Y-%m-%d")
                            if row.list_date
                            else None,
                            "list_status": row.list_status,
                            "exchange": row.exchange,
                            "mgr_name": row.mgr_name,
                            "custod_name": row.custod_name,
                            "mgt_fee": row.mgt_fee,
                            "etf_type": row.etf_type,
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
