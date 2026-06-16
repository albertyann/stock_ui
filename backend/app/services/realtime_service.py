"""
实时股价服务 - 基于本地数据库获取股票价格和K线数据
"""

from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from app.config import get_settings
from app.market.context import get_current_market
from app.market.filter import build_sql_filter


class RealtimePriceService:
    """实时股价服务类 - 从本地数据库查询"""

    def __init__(self):
        self.settings = get_settings()
        self.sync_url = self.settings.database_url.replace("+asyncpg", "")
        self.engine = create_engine(
            self.sync_url,
            connect_args={"options": "-c timezone=Asia/Shanghai"}
        )

    async def get_realtime_prices(self, ts_codes: List[str]) -> Dict:
        """
        获取股票最新价格数据（从本地 daily_data 表）

        Args:
            ts_codes: 股票代码列表，如 ['600000.SH', '000001.SZ']

        Returns:
            包含股价数据的字典
        """
        if not ts_codes:
            return {"success": True, "data": []}

        try:
            with self.engine.connect() as conn:
                # 从 daily_data 获取每个股票的最新数据
                # 参数化查询防止 SQL 注入：使用 ANY(:codes) 替代字符串拼接
                query = """
                    SELECT DISTINCT ON (ts_code)
                        ts_code,
                        trade_date,
                        open as open_price,
                        high as high_price,
                        low as low_price,
                        close as close_price,
                        vol as volume,
                        amount,
                        pct_chg as change_pct,
                        pre_close
                    FROM daily_data 
                    WHERE ts_code = ANY(:codes)
                    ORDER BY ts_code, trade_date DESC
                """

                result = conn.execute(text(query), {"codes": ts_codes})

                stocks = []
                for row in result:
                    stocks.append(self._format_stock_data(row))

                return {"success": True, "data": stocks, "count": len(stocks)}

        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def _format_stock_data(self, row) -> Dict:
        """
        格式化股票数据

        Args:
            row: 数据库查询结果行

        Returns:
            格式化后的股票数据
        """
        ts_code = row.ts_code
        pre_close = float(row.pre_close or 0)
        close = float(row.close_price or 0)
        change_pct = float(row.change_pct or 0)

        # 计算涨跌额
        change = close - pre_close if pre_close > 0 else 0

        return {
            "ts_code": ts_code,
            "symbol": ts_code.split(".")[0] if "." in ts_code else ts_code,
            "name": self._get_stock_name(ts_code),
            "industry": self._get_stock_industry(ts_code),
            "pre_close": pre_close,
            "open": float(row.open_price or 0),
            "high": float(row.high_price or 0),
            "low": float(row.low_price or 0),
            "close": close,
            "price": close,  # 当前价格（本地最新收盘价）
            "change_pct": round(change_pct, 2),
            "change": round(change, 2),
            "volume": int(row.volume or 0),
            "amount": float(row.amount or 0),
            "trade_date": row.trade_date.strftime("%Y-%m-%d") if row.trade_date else "",
            "updated_at": row.updated_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(row, "updated_at") and row.updated_at else None,
            "data_source": "local_db",  # 标记数据来源
        }

    def _get_stock_name(self, ts_code: str) -> str:
        """从数据库获取股票名称"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT name FROM watchlist_stocks 
                        WHERE ts_code = :ts_code 
                        LIMIT 1
                    """),
                    {"ts_code": ts_code},
                )
                row = result.fetchone()
                if row and row.name:
                    return row.name

                # 如果没有在 watchlist 中找到，尝试从 stock_basic 查找
                result = conn.execute(
                    text("""
                        SELECT name FROM stock_basic 
                        WHERE ts_code = :ts_code 
                        LIMIT 1
                    """),
                    {"ts_code": ts_code},
                )
                row = result.fetchone()
                return row.name if row and row.name else ts_code
        except:
            return ts_code

    def _get_stock_industry(self, ts_code: str) -> str:
        """从数据库获取股票所属行业"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT industry FROM stock_basic 
                        WHERE ts_code = :ts_code 
                        LIMIT 1
                    """),
                    {"ts_code": ts_code},
                )
                row = result.fetchone()
                return row.industry if row and row.industry else ""
        except:
            return ""

    def get_kline_data(
        self, ts_code: str, period: str = "daily", limit: int = 60
    ) -> List[Dict]:
        """
        获取K线数据

        Args:
            ts_code: 股票代码
            period: 周期 (daily/weekly/monthly)
            limit: 返回条数

        Returns:
            K线数据列表
        """
        try:
            with self.engine.connect() as conn:
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
                    # 月K线通过日K线聚合
                    result = conn.execute(
                        text("""
                            SELECT 
                                date_trunc('month', trade_date) as date,
                                FIRST_VALUE(open) OVER w as open,
                                MAX(high) as high,
                                MIN(low) as low,
                                LAST_VALUE(close) OVER w as close,
                                SUM(vol) as volume,
                                SUM(amount) as amount,
                                SUM(pct_chg) as change_pct
                            FROM daily_data 
                            WHERE ts_code = :ts_code
                            WINDOW w AS (PARTITION BY date_trunc('month', trade_date) ORDER BY trade_date ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
                            GROUP BY date_trunc('month', trade_date), open, close
                            ORDER BY date DESC
                            LIMIT :limit
                        """),
                        {"ts_code": ts_code, "limit": limit},
                    )

                stock_name = self._get_stock_name(ts_code)
                kline_data = []
                for row in result:
                    kline_data.append(
                        {
                            "date": row.date.strftime("%Y-%m-%d")
                            if hasattr(row.date, "strftime")
                            else str(row.date)[:10],
                            "name": stock_name,
                            "open": float(row.open or 0),
                            "high": float(row.high or 0),
                            "low": float(row.low or 0),
                            "close": float(row.close or 0),
                            "volume": int(row.volume or 0),
                            "amount": float(row.amount or 0),
                            "change_pct": float(row.change_pct or 0),
                        }
                    )

                return list(reversed(kline_data))

        except Exception as e:
            print(f"Kline error: {e}")
            import traceback

            traceback.print_exc()
            return []

    def get_holder_number_data(self, ts_code: str, limit: int = 60) -> List[Dict]:
        """
        获取股东人数数据

        Args:
            ts_code: 股票代码
            limit: 返回条数

        Returns:
            股东人数数据列表
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT 
                            ann_date,
                            end_date,
                            holder_num
                        FROM holder_number
                        WHERE ts_code = :ts_code
                        ORDER BY end_date DESC
                        LIMIT :limit
                    """),
                    {"ts_code": ts_code, "limit": limit},
                )

                holder_data = []
                for row in result:
                    holder_data.append(
                        {
                            "date": row.end_date.strftime("%Y-%m-%d")
                            if hasattr(row.end_date, "strftime")
                            else str(row.end_date)[:10],
                            "ann_date": row.ann_date.strftime("%Y-%m-%d")
                            if hasattr(row.ann_date, "strftime")
                            else str(row.ann_date)[:10],
                            "holder_num": int(row.holder_num or 0),
                        }
                    )

                return list(reversed(holder_data))

        except Exception as e:
            print(f"Holder number error: {e}")
            import traceback

            traceback.print_exc()
            return []

    def get_watchlist_stocks(self, watchlist_id: Optional[int] = None) -> List[Dict]:
        """
        获取股票池中的股票列表

        Args:
            watchlist_id: 股票池ID，为None时获取所有股票池的股票

        Returns:
            股票列表
        """
        try:
            with self.engine.connect() as conn:
                if watchlist_id:
                    result = conn.execute(
                        text("""
                            SELECT ws.ts_code, ws.symbol, ws.name, w.name as watchlist_name
                            FROM watchlist_stocks ws
                            JOIN watchlists w ON ws.watchlist_id = w.id
                            WHERE ws.watchlist_id = :watchlist_id
                            ORDER BY ws.added_at DESC
                        """),
                        {"watchlist_id": watchlist_id},
                    )
                else:
                    # 获取所有股票池的股票（使用子查询去重）
                    result = conn.execute(
                        text("""
                            SELECT DISTINCT ON (ws.ts_code) 
                                ws.ts_code, ws.symbol, ws.name, w.name as watchlist_name
                            FROM watchlist_stocks ws
                            JOIN watchlists w ON ws.watchlist_id = w.id
                            ORDER BY ws.ts_code, ws.added_at DESC
                        """)
                    )

                stocks = []
                for row in result:
                    stocks.append(
                        {
                            "ts_code": row.ts_code,
                            "symbol": row.symbol,
                            "name": row.name,
                            "watchlist_name": row.watchlist_name,
                        }
                    )

                return stocks
        except Exception as e:
            print(f"Get watchlist stocks error: {e}")
            return []

    def validate_ts_code(self, ts_code: str) -> bool:
        """
        验证股票代码格式

        Args:
            ts_code: 股票代码

        Returns:
            是否有效
        """
        if not ts_code:
            return False

        # 支持的交易所后缀
        valid_suffixes = [".SH", ".SZ", ".BJ"]

        # 检查是否包含有效后缀
        has_suffix = any(ts_code.upper().endswith(suffix) for suffix in valid_suffixes)

        # 也可以支持没有后缀的代码（自动判断）
        if not has_suffix:
            # 纯数字代码也是有效的，后面会自动添加后缀
            code = ts_code.strip()
            return code.isdigit() and len(code) in [5, 6]

        return True

    def normalize_ts_code(self, ts_code: str) -> Optional[str]:
        """
        标准化股票代码格式

        Args:
            ts_code: 原始股票代码

        Returns:
            标准化后的代码，如 600000.SH
        """
        if not ts_code:
            return None

        ts_code = ts_code.strip().upper()

        # 如果已经有后缀，直接返回
        if any(ts_code.endswith(suffix) for suffix in [".SH", ".SZ", ".BJ"]):
            return ts_code

        # 根据代码规则自动判断交易所
        if ts_code.startswith("6"):
            return f"{ts_code}.SH"
        elif ts_code.startswith(("0", "3")):
            return f"{ts_code}.SZ"
        elif ts_code.startswith(("4", "8", "9")):
            return f"{ts_code}.BJ"
        elif ts_code.startswith("688"):
            return f"{ts_code}.SH"

        # 默认返回深圳
        return f"{ts_code}.SZ"

    def _resolve_stock_names(self, names: List[str]) -> List[str]:
        """根据股票名称从 stock_basic 查询对应的 ts_code"""
        if not names:
            return []
        try:
            with self.engine.connect() as conn:
                params = {f"name{i}": name for i, name in enumerate(names)}
                placeholders = ", ".join([f":name{i}" for i in range(len(names))])
                query = f"""
                    SELECT ts_code, name FROM stock_basic
                    WHERE name IN ({placeholders})
                """
                result = conn.execute(text(query), params)
                return [row.ts_code for row in result]
        except Exception as e:
            print(f"Resolve stock names error: {e}")
            import traceback

            traceback.print_exc()
            return []

    def parse_ts_codes_input(self, input_text: str) -> List[str]:
        """
        解析用户输入的股票代码或名称
        支持逗号分隔或换行分隔；对无法识别为代码的输入会按名称到 stock_basic 查询

        Args:
            input_text: 用户输入文本

        Returns:
            标准化后的股票代码列表
        """
        if not input_text:
            return []

        # 支持逗号和换行分隔
        separators = [",", "，", "\n", "\t"]
        codes = [input_text]

        for sep in separators:
            new_codes = []
            for code in codes:
                new_codes.extend(code.split(sep))
            codes = new_codes

        # 清理并标准化
        result = []
        names_to_lookup = []
        for code in codes:
            code = code.strip()
            if not code:
                continue
            if self.validate_ts_code(code):
                normalized = self.normalize_ts_code(code)
                if normalized and normalized not in result:
                    result.append(normalized)
            else:
                names_to_lookup.append(code)

        if names_to_lookup:
            resolved = self._resolve_stock_names(names_to_lookup)
            for ts_code in resolved:
                if ts_code not in result:
                    result.append(ts_code)

        return result

    def query_stock_prices_by_date(self, ts_codes: List[str], query_date: str, days: List[int] = None) -> Dict:
        """
        查询指定股票在指定日期的价格，以及 T+N 交易日的价格和涨幅

        Args:
            ts_codes: 股票代码列表
            query_date: 查询日期，格式 YYYY-MM-DD
            days: T+N 的天数列表，默认 [1, 3, 7, 30]

        Returns:
            包含各股票 T, T+N 价格及涨幅的字典
        """
        try:
            from datetime import datetime

            parsed_date = datetime.strptime(query_date, "%Y-%m-%d").date()

            if days is None:
                days = [1, 3, 7, 30]

            with self.engine.connect() as conn:
                trading_dates = {}
                all_offsets = [0] + sorted(set(days))
                for offset in all_offsets:
                    result = conn.execute(
                        text("""
                            SELECT cal_date trade_date FROM trade_cal
                            WHERE exchange = 'SSE' AND is_open = 1 AND cal_date >= :base_date
                            ORDER BY cal_date ASC
                            LIMIT 1 OFFSET :offset
                        """),
                        {"base_date": parsed_date, "offset": offset},
                    )
                    row = result.fetchone()
                    if row:
                        trading_dates[f"T+{offset}"] = row.trade_date

                if not trading_dates:
                    return {
                        "success": False,
                        "error": "无法找到交易日",
                        "data": [],
                    }

                all_dates = list(set(trading_dates.values()))

                # 参数化绑定防止 SQL 注入
                query = """
                    SELECT ts_code, trade_date, close, pct_chg
                    FROM daily_data
                    WHERE ts_code = ANY(:codes)
                    AND trade_date = ANY(:dates)
                    ORDER BY ts_code, trade_date
                """
                result = conn.execute(
                    text(query),
                    {"codes": ts_codes, "dates": all_dates},
                )

                price_map = {}
                for row in result:
                    date_str = row.trade_date.strftime("%Y-%m-%d")
                    price_map[(row.ts_code, date_str)] = {
                        "close": float(row.close or 0),
                        "pct_chg": float(row.pct_chg or 0),
                    }

                stock_names = {}
                stock_industries = {}
                for ts_code in ts_codes:
                    stock_names[ts_code] = self._get_stock_name(ts_code)
                    stock_industries[ts_code] = self._get_stock_industry(ts_code)

                results = []
                for ts_code in ts_codes:
                    row_data = {
                        "ts_code": ts_code,
                        "name": stock_names.get(ts_code, ts_code),
                        "industry": stock_industries.get(ts_code, ""),
                    }

                    base_price = None
                    for label, trade_date in trading_dates.items():
                        date_str = trade_date.strftime("%Y-%m-%d")
                        key = (ts_code, date_str)
                        if key in price_map:
                            price_info = price_map[key]
                            row_data[f"date_{label}"] = date_str
                            row_data[f"close_{label}"] = price_info["close"]
                            row_data[f"pct_chg_{label}"] = price_info["pct_chg"]

                            if label == "T+0":
                                base_price = price_info["close"]
                        else:
                            row_data[f"date_{label}"] = date_str
                            row_data[f"close_{label}"] = None
                            row_data[f"pct_chg_{label}"] = None

                    for day in days:
                        label = f"T+{day}"
                        pct_chg_val = row_data.get(f"pct_chg_{label}")
                        row_data[f"change_{label}"] = pct_chg_val if pct_chg_val is not None else None

                    results.append(row_data)

                return {
                    "success": True,
                    "data": results,
                    "query_date": query_date,
                    "trading_dates": {
                        k: v.strftime("%Y-%m-%d") for k, v in trading_dates.items()
                    },
                }

        except Exception as e:
            import traceback

            traceback.print_exc()
            return {"success": False, "error": str(e), "data": []}

    def get_limit_up_stocks(
        self,
        min_change_pct: float = 9.9,
        limit: int = 200,
        trade_date: str = None,
        industry: str = None,
    ) -> Dict:
        """
        获取指定交易日的涨停股票（涨幅大于等于指定百分比）

        Args:
            min_change_pct: 最小涨幅百分比，默认9.9%（涨停）
            limit: 返回的最大股票数量
            trade_date: 指定交易日，格式 YYYY-MM-DD，默认为最新交易日
            industry: 板块/行业筛选，默认为None表示所有板块

        Returns:
            包含涨停股票数据的字典
        """
        try:
            with self.engine.connect() as conn:
                if trade_date:
                    try:
                        from datetime import datetime

                        parsed_date = datetime.strptime(trade_date, "%Y-%m-%d").date()
                    except ValueError:
                        return {
                            "success": False,
                            "error": "Invalid date format. Use YYYY-MM-DD",
                            "data": [],
                            "trade_date": None,
                            "count": 0,
                        }
                else:
                    latest_date_result = conn.execute(
                        text("SELECT MAX(trade_date) as latest_date FROM daily_data")
                    )
                    latest_date_row = latest_date_result.fetchone()

                    if not latest_date_row or not latest_date_row.latest_date:
                        return {
                            "success": True,
                            "data": [],
                            "trade_date": None,
                            "count": 0,
                        }

                    parsed_date = latest_date_row.latest_date

                market = get_current_market()
                market_sql, market_params = build_sql_filter(market, "d.ts_code")
                params = {
                    "trade_date": parsed_date,
                    "min_change_pct": min_change_pct,
                    "limit": limit,
                }
                params.update(market_params)

                if industry:
                    query = f"""
                        SELECT 
                            d.ts_code,
                            d.trade_date,
                            d.open as open_price,
                            d.high as high_price,
                            d.low as low_price,
                            d.close as close_price,
                            d.vol as volume,
                            d.amount,
                            d.pct_chg as change_pct,
                        d.pre_close,
                        d.updated_at
                    FROM daily_data d
                    JOIN stock_basic s ON d.ts_code = s.ts_code
                    WHERE d.trade_date = :trade_date
                    AND d.pct_chg >= :min_change_pct
                    AND s.industry = :industry
                    AND {market_sql}
                    ORDER BY d.pct_chg DESC
                    LIMIT :limit
                    """
                    params["industry"] = industry
                    result = conn.execute(text(query), params)
                else:
                    query = f"""
                        SELECT 
                            d.ts_code,
                            d.trade_date,
                            d.open as open_price,
                            d.high as high_price,
                            d.low as low_price,
                            d.close as close_price,
                            d.vol as volume,
                            d.amount,
                            d.pct_chg as change_pct,
                        d.pre_close,
                        d.updated_at
                    FROM daily_data d
                    WHERE d.trade_date = :trade_date
                    AND d.pct_chg >= :min_change_pct
                    AND {market_sql}
                    ORDER BY d.pct_chg DESC
                    LIMIT :limit
                    """
                    result = conn.execute(text(query), params)

                stocks = []
                for row in result:
                    stocks.append(self._format_stock_data(row))

                return {
                    "success": True,
                    "data": stocks,
                    "trade_date": parsed_date.strftime("%Y-%m-%d")
                    if hasattr(parsed_date, "strftime")
                    else str(parsed_date),
                    "count": len(stocks),
                }

        except Exception as e:
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "trade_date": None,
                "count": 0,
            }
