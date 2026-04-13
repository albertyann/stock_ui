from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import create_engine, text
from app.config import get_settings


class StockService:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    def search_stocks(self, keyword: str, limit: int = 20) -> List[dict]:
        try:
            settings = get_settings()
            sync_url = settings.database_url.replace("+asyncpg", "")
            engine = create_engine(sync_url)

            with engine.connect() as conn:
                query = """
                    SELECT DISTINCT ts_code, symbol, name
                    FROM watchlist_stocks
                    WHERE (name ILIKE :keyword OR ts_code ILIKE :keyword OR symbol ILIKE :keyword)
                    LIMIT :limit
                """
                result = conn.execute(
                    text(query), {"keyword": f"%{keyword}%", "limit": limit}
                )

                results = []
                for row in result:
                    results.append(
                        {
                            "ts_code": row.ts_code,
                            "symbol": row.symbol,
                            "name": row.name or row.ts_code,
                            "industry": "",
                            "price": 0.0,
                            "change_pct": 0.0,
                        }
                    )

                return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def get_stock_detail(self, ts_code: str) -> Optional[dict]:
        try:
            settings = get_settings()
            sync_url = settings.database_url.replace("+asyncpg", "")
            engine = create_engine(sync_url)

            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                    SELECT ts_code, symbol, name, industry, market, list_date
                    FROM stock_basic
                    WHERE ts_code = :ts_code
                    LIMIT 1
                """),
                    {"ts_code": ts_code},
                )

                row = result.fetchone()
                if not row:
                    print(f"Stock {ts_code} not found in stock_basic table")
                    return None

                # 从 daily_data 获取最新行情数据
                daily_data_result = conn.execute(
                    text("""
                    SELECT 
                        close,
                        pct_chg,
                        vol as volume,
                        amount,
                        trade_date
                    FROM daily_data
                    WHERE ts_code = :ts_code
                    ORDER BY trade_date DESC
                    LIMIT 1
                """),
                    {"ts_code": ts_code},
                )
                daily_data_row = daily_data_result.fetchone()

                # 从 daily_indicators 获取指标数据
                indicators_result = conn.execute(
                    text("""
                    SELECT 
                        turnover_rate,
                        pe,
                        pb,
                        total_mv,
                        trade_date
                    FROM daily_indicators
                    WHERE ts_code = :ts_code
                    ORDER BY trade_date DESC
                    LIMIT 1
                """),
                    {"ts_code": ts_code},
                )
                indicators_row = indicators_result.fetchone()

                return {
                    "ts_code": ts_code,
                    "symbol": row.symbol or ts_code.split(".")[0],
                    "name": row.name or ts_code,
                    "industry": row.industry or "",
                    "current_price": float(daily_data_row.close)
                    if daily_data_row and daily_data_row.close
                    else 0,
                    "change_pct": float(daily_data_row.pct_chg)
                    if daily_data_row and daily_data_row.pct_chg
                    else 0,
                    "volume": int(daily_data_row.volume)
                    if daily_data_row and daily_data_row.volume
                    else 0,
                    "amount": float(daily_data_row.amount)
                    if daily_data_row and daily_data_row.amount
                    else 0,
                    "turnover_rate": float(indicators_row.turnover_rate)
                    if indicators_row and indicators_row.turnover_rate
                    else 0,
                    "pe": float(indicators_row.pe)
                    if indicators_row and indicators_row.pe
                    else 0,
                    "pb": float(indicators_row.pb)
                    if indicators_row and indicators_row.pb
                    else 0,
                    "market_cap": float(indicators_row.total_mv)
                    if indicators_row and indicators_row.total_mv
                    else 0,
                }

        except Exception as e:
            print(f"Detail error: {e}")
            import traceback

            traceback.print_exc()
            return None

    def get_kline_data(
        self, ts_code: str, period: str = "daily", limit: int = 60
    ) -> List[dict]:
        try:
            settings = get_settings()
            sync_url = settings.database_url.replace("+asyncpg", "")
            engine = create_engine(sync_url)

            with engine.connect() as conn:
                if period == "daily":
                    result = conn.execute(
                        text("""
                        SELECT 
                            trade_date as date,
                            open,
                            high,
                            low,
                            close,
                            vol as volume,
                            amount,
                            pct_chg as change_pct
                        FROM daily_data 
                        WHERE ts_code = :ts_code
                        ORDER BY trade_date DESC
                        LIMIT :limit
                    """),
                        {"ts_code": ts_code, "limit": limit},
                    )
                elif period == "weekly":
                    result = conn.execute(
                        text("""
                        SELECT 
                            trade_date as date,
                            open,
                            high,
                            low,
                            close,
                            vol as volume,
                            amount,
                            pct_chg as change_pct
                        FROM weekly_data 
                        WHERE ts_code = :ts_code
                        ORDER BY trade_date DESC
                        LIMIT :limit
                    """),
                        {"ts_code": ts_code, "limit": limit},
                    )
                else:
                    result = conn.execute(
                        text("""
                        SELECT 
                            date_trunc('month', trade_date) as date,
                            FIRST_VALUE(open) OVER (PARTITION BY date_trunc('month', trade_date) ORDER BY trade_date) as open,
                            MAX(high) as high,
                            MIN(low) as low,
                            FIRST_VALUE(close) OVER (PARTITION BY date_trunc('month', trade_date) ORDER BY trade_date DESC) as close,
                            SUM(vol) as volume,
                            SUM(amount) as amount,
                            SUM(pct_chg) as change_pct
                        FROM daily_data 
                        WHERE ts_code = :ts_code
                        GROUP BY date_trunc('month', trade_date)
                        ORDER BY date DESC
                        LIMIT :limit
                    """),
                        {"ts_code": ts_code, "limit": limit},
                    )

                kline_data = []
                for row in result:
                    kline_data.append(
                        {
                            "date": row.date.strftime("%Y-%m-%d"),
                            "open": float(row.open),
                            "high": float(row.high),
                            "low": float(row.low),
                            "close": float(row.close),
                            "volume": int(row.volume),
                            "amount": float(row.amount),
                            "change_pct": float(row.change_pct)
                            if row.change_pct
                            else 0,
                        }
                    )

                return list(reversed(kline_data))

        except Exception as e:
            print(f"Kline error: {e}")
            import traceback

            traceback.print_exc()
            return []
