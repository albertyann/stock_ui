from datetime import date as date_type
from typing import Dict, Optional
from sqlalchemy import text


class FundBasicServiceMixin:
    def get_fund_basic(
        self,
        page: int = 1,
        page_size: int = 20,
        name: Optional[str] = None,
        ts_code: Optional[str] = None,
        fund_type: Optional[str] = None,
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
                if fund_type:
                    where_clauses.append("fund_type = :fund_type")
                    params["fund_type"] = fund_type
                if market:
                    where_clauses.append("market = :market")
                    params["market"] = market

                where_sql = (
                    "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                )

                count_query = (
                    f"SELECT COUNT(*) as total FROM fund_basic {where_sql}"
                )
                total = conn.execute(text(count_query), params).fetchone().total

                offset = (page - 1) * page_size
                query = f"""
                    SELECT ts_code, name, management, custodian, fund_type,
                           found_date, due_date, list_date, issue_date, delist_date,
                           issue_amount, m_fee, c_fee, duration_year, p_value,
                           min_amount, exp_return, benchmark, status, invest_type,
                           "type", trustee, purc_startdate, redm_startdate, market,
                           update_time
                    FROM fund_basic
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
                            "name": row.name,
                            "management": row.management,
                            "custodian": row.custodian,
                            "fund_type": row.fund_type,
                            "found_date": row.found_date.strftime("%Y-%m-%d")
                            if row.found_date
                            else None,
                            "due_date": row.due_date.strftime("%Y-%m-%d")
                            if row.due_date
                            else None,
                            "list_date": row.list_date.strftime("%Y-%m-%d")
                            if row.list_date
                            else None,
                            "issue_date": row.issue_date.strftime("%Y-%m-%d")
                            if row.issue_date
                            else None,
                            "delist_date": row.delist_date.strftime("%Y-%m-%d")
                            if row.delist_date
                            else None,
                            "issue_amount": row.issue_amount,
                            "m_fee": row.m_fee,
                            "c_fee": row.c_fee,
                            "duration_year": row.duration_year,
                            "p_value": row.p_value,
                            "min_amount": row.min_amount,
                            "exp_return": row.exp_return,
                            "benchmark": row.benchmark,
                            "status": row.status,
                            "invest_type": row.invest_type,
                            "type": row.type,
                            "trustee": row.trustee,
                            "purc_startdate": row.purc_startdate.strftime(
                                "%Y-%m-%d"
                            )
                            if row.purc_startdate
                            else None,
                            "redm_startdate": row.redm_startdate.strftime(
                                "%Y-%m-%d"
                            )
                            if row.redm_startdate
                            else None,
                            "market": row.market,
                            "update_time": row.update_time.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            if row.update_time
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

    def get_fund_portfolio(
        self,
        ts_code: str,
    ) -> Dict:
        """获取基金持仓（fund_portfolio 表），按季度分组。"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT
                            ts_code,
                            end_date,
                            symbol,
                            ann_date,
                            mkv,
                            amount,
                            stk_mkv_ratio,
                            stk_float_ratio
                        FROM fund_portfolio
                        WHERE ts_code = :ts_code
                        ORDER BY end_date DESC, symbol
                    """),
                    {"ts_code": ts_code},
                )
                items = []
                for row in result:
                    items.append({
                        "ts_code": row.ts_code,
                        "end_date": row.end_date.strftime("%Y-%m-%d") if row.end_date else None,
                        "symbol": row.symbol,
                        "ann_date": row.ann_date.strftime("%Y-%m-%d") if row.ann_date else None,
                        "mkv": float(row.mkv) if row.mkv is not None else None,
                        "amount": float(row.amount) if row.amount is not None else None,
                        "stk_mkv_ratio": float(row.stk_mkv_ratio) if row.stk_mkv_ratio is not None else None,
                        "stk_float_ratio": float(row.stk_float_ratio) if row.stk_float_ratio is not None else None,
                    })
                return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}
