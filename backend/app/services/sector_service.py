"""
板块服务 - 获取行业板块数据（从 stock_basic 表 industry 字段）
"""

from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from app.config import get_settings


class SectorService:
    """板块服务类"""

    def __init__(self):
        self.settings = get_settings()
        self.sync_url = self.settings.database_url.replace("+asyncpg", "")
        self.engine = create_engine(self.sync_url)

    def get_all_sectors(self) -> List[Dict]:
        """
        获取所有板块列表（从 stock_basic 表按 industry 字段分组）

        Returns:
            板块列表
        """
        try:
            with self.engine.connect() as conn:
                # 从 stock_basic 表按 industry 字段分组获取板块信息
                query = """
                    SELECT 
                        industry as sector_name,
                        COUNT(*) as stock_count
                    FROM stock_basic
                    WHERE industry IS NOT NULL AND industry != ''
                    GROUP BY industry
                    ORDER BY stock_count DESC
                """
                result = conn.execute(text(query))

                sectors = []
                for idx, row in enumerate(result):
                    sectors.append(
                        {
                            "code": f"ind_{idx}",
                            "name": row.sector_name,
                            "type": "industry",
                            "change_pct": 0.0,
                            "total_volume": 0.0,
                            "total_amount": 0.0,
                            "stock_count": int(row.stock_count),
                        }
                    )

                return sectors

        except Exception as e:
            print(f"Get sectors error: {e}")
            import traceback

            traceback.print_exc()
            return []

    def get_sector_stocks(
        self, sector_code: str, sector_type: str = "industry"
    ) -> List[Dict]:
        """
        获取板块内的股票列表（包含实时价格数据）

        Args:
            sector_code: 板块代码（在此实现中实际上是行业名称）
            sector_type: 板块类型 (industry)

        Returns:
            股票列表（包含完整价格数据）
        """
        try:
            # 解析板块名称 - sector_code 可能是一个 ID 或直接是行业名称
            sector_name = self._get_sector_name_from_code(sector_code)

            with self.engine.connect() as conn:
                # 从 stock_basic 表和 daily_data 表获取该行业的股票及最新价格
                query = """
                    SELECT 
                        sb.ts_code,
                        sb.symbol,
                        sb.name,
                        sb.market,
                        sb.list_date,
                        dd.open,
                        dd.high,
                        dd.low,
                        dd.close as price,
                        dd.pre_close,
                        dd.vol as volume,
                        dd.amount,
                        dd.pct_chg as change_pct,
                        dd.trade_date
                    FROM stock_basic sb
                    LEFT JOIN LATERAL (
                        SELECT *
                        FROM daily_data
                        WHERE ts_code = sb.ts_code
                        ORDER BY trade_date DESC
                        LIMIT 1
                    ) dd ON true
                    WHERE sb.industry = :industry
                    ORDER BY sb.symbol
                """
                result = conn.execute(text(query), {"industry": sector_name})

                stocks = []
                for row in result:
                    # 计算涨跌额
                    price = float(row.price or 0)
                    pre_close = float(row.pre_close or 0)
                    change = price - pre_close if pre_close > 0 else 0

                    stocks.append(
                        {
                            "ts_code": row.ts_code,
                            "symbol": row.symbol,
                            "name": row.name,
                            "price": price,
                            "pre_close": pre_close,
                            "open": float(row.open or 0),
                            "high": float(row.high or 0),
                            "low": float(row.low or 0),
                            "change_pct": float(row.change_pct or 0),
                            "change": round(change, 2),
                            "volume": int(row.volume or 0),
                            "amount": float(row.amount or 0),
                            "sector_name": sector_name,
                            "trade_date": row.trade_date.strftime("%Y-%m-%d")
                            if row.trade_date
                            else "",
                            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                return stocks

        except Exception as e:
            print(f"Get sector stocks error: {e}")
            import traceback

            traceback.print_exc()
            return []

    def get_sector_detail(
        self, sector_code: str, sector_type: str = "industry"
    ) -> Optional[Dict]:
        """
        获取板块详情

        Args:
            sector_code: 板块代码（在此实现中实际上是行业名称或 ind_xxx 格式）
            sector_type: 板块类型

        Returns:
            板块详情
        """
        try:
            # 解析板块名称
            sector_name = self._get_sector_name_from_code(sector_code)

            with self.engine.connect() as conn:
                # 从 stock_basic 表获取板块详情
                query = """
                    SELECT 
                        industry as sector_name,
                        COUNT(*) as stock_count
                    FROM stock_basic
                    WHERE industry = :industry
                    GROUP BY industry
                """
                result = conn.execute(text(query), {"industry": sector_name})
                row = result.fetchone()

                if not row:
                    return None

                return {
                    "code": sector_code,
                    "name": sector_name,
                    "type": "industry",
                    "change_pct": 0.0,
                    "total_volume": 0.0,
                    "total_amount": 0.0,
                    "stock_count": int(row.stock_count),
                }

        except Exception as e:
            print(f"Get sector detail error: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _get_sector_name_from_code(self, sector_code: str) -> str:
        """
        根据板块代码获取板块名称

        如果 sector_code 以 ind_ 开头，需要从数据库查询对应名称
        否则直接返回 sector_code 作为名称
        """
        if not sector_code.startswith("ind_"):
            return sector_code

        try:
            # 解析索引
            idx = int(sector_code.replace("ind_", ""))

            with self.engine.connect() as conn:
                query = """
                    SELECT 
                        industry as sector_name,
                        COUNT(*) as stock_count
                    FROM stock_basic
                    WHERE industry IS NOT NULL AND industry != ''
                    GROUP BY industry
                    ORDER BY stock_count DESC
                """
                result = conn.execute(text(query))

                for i, row in enumerate(result):
                    if i == idx:
                        return row.sector_name

            # 如果没找到，返回原值
            return sector_code

        except Exception as e:
            print(f"Get sector name from code error: {e}")
            return sector_code

    def _normalize_code(self, code: str) -> str:
        """标准化股票代码"""
        code = str(code).strip()
        if not code:
            return ""

        # 如果已经有后缀，直接返回
        if "." in code:
            return code.upper()

        # 根据代码规则自动判断交易所
        if code.startswith("6"):
            return f"{code}.SH"
        elif code.startswith(("0", "3")):
            return f"{code}.SZ"
        elif code.startswith(("4", "8", "9")):
            return f"{code}.BJ"

        return f"{code}.SZ"
