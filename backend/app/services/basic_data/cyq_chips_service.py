from typing import Dict, Optional
from sqlalchemy import text


class CyqChipsServiceMixin:
    def get_cyq_chips(
        self,
        ts_code: str,
        trade_date: Optional[str] = None,
        limit: int = 1,
    ) -> Dict:
        try:
            with self.engine.connect() as conn:
                if not trade_date:
                    date_result = conn.execute(
                        text("""
                            SELECT MAX(trade_date) as latest_date
                            FROM cyq_chips
                            WHERE ts_code = :ts_code
                        """),
                        {"ts_code": ts_code},
                    )
                    row = date_result.fetchone()
                    if row and row.latest_date:
                        trade_date = row.latest_date.strftime("%Y-%m-%d")
                    else:
                        return {"success": True, "data": {"trade_date": None, "chips": [], "current_price": None}}
                else:
                    # 如果指定日期没有数据，查找最近的可用日期
                    # 优先往回找（找更早的日期），如果没有则往前找（找更晚的日期）
                    date_result = conn.execute(
                        text("""
                            SELECT MAX(trade_date) as nearest_date
                            FROM cyq_chips
                            WHERE ts_code = :ts_code AND trade_date <= :trade_date
                        """),
                        {"ts_code": ts_code, "trade_date": trade_date},
                    )
                    row = date_result.fetchone()
                    if row and row.nearest_date:
                        actual_date = row.nearest_date.strftime("%Y-%m-%d")
                        if actual_date != trade_date:
                            trade_date = actual_date
                    else:
                        # 没有更早的数据，尝试找最早的可用数据
                        date_result = conn.execute(
                            text("""
                                SELECT MIN(trade_date) as earliest_date
                                FROM cyq_chips
                                WHERE ts_code = :ts_code
                            """),
                            {"ts_code": ts_code},
                        )
                        row = date_result.fetchone()
                        if row and row.earliest_date:
                            trade_date = row.earliest_date.strftime("%Y-%m-%d")
                        else:
                            return {"success": True, "data": {"trade_date": trade_date, "chips": [], "current_price": None}}

                price_result = conn.execute(
                    text("""
                        SELECT close FROM daily_data
                        WHERE ts_code = :ts_code AND trade_date = :trade_date
                        LIMIT 1
                    """),
                    {"ts_code": ts_code, "trade_date": trade_date},
                )
                price_row = price_result.fetchone()
                current_price = float(price_row.close) if price_row and price_row.close else None

                result = conn.execute(
                    text("""
                        SELECT price, percent
                        FROM cyq_chips
                        WHERE ts_code = :ts_code AND trade_date = :trade_date
                        ORDER BY price ASC
                    """),
                    {"ts_code": ts_code, "trade_date": trade_date},
                )

                chips = []
                for row in result:
                    chips.append({
                        "price": float(row.price) if row.price is not None else 0,
                        "percent": float(row.percent) if row.percent is not None else 0,
                    })

                return {
                    "success": True,
                    "data": {
                        "trade_date": trade_date,
                        "chips": chips,
                        "current_price": current_price,
                    }
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "data": {"trade_date": None, "chips": [], "current_price": None}}
