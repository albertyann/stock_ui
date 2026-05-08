from typing import Dict, Optional, List
from sqlalchemy import text


class MoneyflowServiceMixin:
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
