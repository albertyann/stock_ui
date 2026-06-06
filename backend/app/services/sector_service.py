"""
板块服务 - 获取行业板块数据（从 stock_basic 表 industry 字段）
概念板块数据来源: dc_index（板块列表）+ dc_member（板块成分股）
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from app.config import get_settings
from app.market.context import get_current_market
from app.market.filter import build_sql_filter

logger = logging.getLogger(__name__)


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
                market = get_current_market()
                market_sql, market_params = build_sql_filter(market, "ts_code")
                params = dict(market_params)

                # 从 stock_basic 表按 industry 字段分组获取板块信息
                query = f"""
                    SELECT 
                        industry as sector_name,
                        COUNT(*) as stock_count
                    FROM stock_basic
                    WHERE industry IS NOT NULL AND industry != ''
                    AND {market_sql}
                    GROUP BY industry
                    ORDER BY stock_count DESC
                """
                result = conn.execute(text(query), params)

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
        self, sector_code: str, sector_type: str = "industry", sort: str = "default", trend: Optional[str] = None
    ) -> List[Dict]:
        """
        获取板块内的股票列表（包含实时价格数据）

        Args:
            sector_code: 板块代码（在此实现中实际上是行业名称）
            sector_type: 板块类型 (industry)
            sort: 排序方式 (default, asc, desc)

        Returns:
            股票列表（包含完整价格数据）
        """
        try:
            # 解析板块名称 - sector_code 可能是一个 ID 或直接是行业名称
            sector_name = self._get_sector_name_from_code(sector_code)

            with self.engine.connect() as conn:
                # 从 stock_basic 表和 daily_data 表获取该行业的股票及最新价格
                order_clause = "sb.symbol"
                if sort == "asc":
                    order_clause = "dd.pct_chg ASC NULLS LAST"
                elif sort == "desc":
                    order_clause = "dd.pct_chg DESC NULLS LAST"
                elif sort == "volume_asc":
                    order_clause = "dd.vol ASC NULLS LAST"
                elif sort == "volume_desc":
                    order_clause = "dd.vol DESC NULLS LAST"

                # 构建趋势过滤条件
                market = get_current_market()
                market_sql, market_params = build_sql_filter(market, "sb.ts_code")
                trend_params = {"industry": sector_name}
                trend_params.update(market_params)
                trend_clause = ""
                if trend == "up":
                    trend_clause = "AND sb.trend = 1"
                elif trend == "down":
                    trend_clause = "AND sb.trend = -1"

                query = f"""
                    SELECT
                        sb.ts_code,
                        sb.symbol,
                        sb.name,
                        sb.industry,
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
                    WHERE sb.industry = :industry {trend_clause}
                    AND {market_sql}
                    ORDER BY {order_clause}
                """
                result = conn.execute(text(query), trend_params)

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
                            "industry": row.industry,
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
                market = get_current_market()
                market_sql, market_params = build_sql_filter(market, "ts_code")
                params = dict(market_params)

                query = f"""
                    SELECT 
                        industry as sector_name,
                        COUNT(*) as stock_count
                    FROM stock_basic
                    WHERE industry IS NOT NULL AND industry != ''
                    AND {market_sql}
                    GROUP BY industry
                    ORDER BY stock_count DESC
                """
                result = conn.execute(text(query), params)

                for i, row in enumerate(result):
                    if i == idx:
                        return row.sector_name

            # 如果没找到，返回原值
            return sector_code

        except Exception as e:
            print(f"Get sector name from code error: {e}")
            return sector_code

    SECTOR_TYPE_MAP = {
        "concept": "概念板块",
        "industry": "行业板块",
        "region": "地域板块",
    }

    def get_concept_sectors(self, trade_date: Optional[str] = None, sector_type: Optional[str] = None) -> List[Dict]:
        """
        获取板块列表（从 dc_index 表获取数据）

        Args:
            trade_date: 交易日期，格式 YYYY-MM-DD，为 None 时返回最新日期数据
            sector_type: 板块类型 (concept/industry/region)，为 None 时返回所有类型

        Returns:
            板块列表
        """
        try:
            idx_type = self.SECTOR_TYPE_MAP.get(sector_type) if sector_type else None

            with self.engine.connect() as conn:
                if trade_date:
                    from datetime import datetime as dt
                    query_date = dt.strptime(trade_date, "%Y-%m-%d").date()
                else:
                    if idx_type:
                        date_query = "SELECT MAX(trade_date) as latest_date FROM dc_index WHERE idx_type = :idx_type"
                        date_result = conn.execute(text(date_query), {"idx_type": idx_type})
                    else:
                        date_query = "SELECT MAX(trade_date) as latest_date FROM dc_index"
                        date_result = conn.execute(text(date_query))
                    latest_date_row = date_result.fetchone()
                    if not latest_date_row or not latest_date_row.latest_date:
                        return []
                    query_date = latest_date_row.latest_date

                where_clause = "trade_date = :trade_date"
                params = {"trade_date": query_date}
                if idx_type:
                    where_clause += " AND idx_type = :idx_type"
                    params["idx_type"] = idx_type

                query = f"""
                    SELECT
                        ts_code,
                        name,
                        "leading",
                        leading_code,
                        pct_change,
                        leading_pct,
                        total_mv,
                        turnover_rate,
                        up_num,
                        down_num,
                        idx_type,
                        "level"
                    FROM dc_index
                    WHERE {where_clause}
                    ORDER BY ABS(COALESCE(pct_change, 0)) DESC
                """
                result = conn.execute(text(query), params)

                sectors = []
                for row in result:
                    row_type = self._map_idx_type_to_sector_type(row.idx_type)
                    sectors.append({
                        "code": row.ts_code,
                        "name": row.name,
                        "type": row_type,
                        "change_pct": float(row.pct_change or 0),
                        "leading": row.leading,
                        "leading_code": row.leading_code,
                        "leading_pct": float(row.leading_pct or 0),
                        "total_mv": float(row.total_mv or 0),
                        "turnover_rate": float(row.turnover_rate or 0),
                        "up_num": int(row.up_num or 0),
                        "down_num": int(row.down_num or 0),
                        "idx_type": row.idx_type,
                        "level": row.level,
                        "trade_date": query_date.strftime("%Y-%m-%d") if hasattr(query_date, 'strftime') else str(query_date),
                        "stock_count": int(row.up_num or 0) + int(row.down_num or 0),
                    })

                return sectors

        except Exception as e:
            print(f"Get concept sectors error: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def _map_idx_type_to_sector_type(idx_type: str) -> str:
        mapping = {"概念板块": "concept", "行业板块": "industry", "地域板块": "region"}
        return mapping.get(idx_type, "concept")

    def get_concept_sector_detail(self, ts_code: str, trade_date: Optional[str] = None) -> Optional[Dict]:
        """
        获取概念板块详情

        Args:
            ts_code: 板块代码
            trade_date: 交易日期，格式 YYYY-MM-DD，为 None 时返回最新日期数据

        Returns:
            板块详情
        """
        try:
            with self.engine.connect() as conn:
                ts_code_variants = [ts_code]
                if ts_code.endswith('.DC'):
                    ts_code_variants.append(ts_code[:-3])
                else:
                    ts_code_variants.append(ts_code + '.DC')

                if trade_date:
                    from datetime import datetime as dt
                    query_date = dt.strptime(trade_date, "%Y-%m-%d").date()
                    matched_ts_code = None
                    for variant in ts_code_variants:
                        check_query = "SELECT 1 FROM dc_index WHERE ts_code = :ts_code AND trade_date = :trade_date LIMIT 1"
                        check_result = conn.execute(text(check_query), {"ts_code": variant, "trade_date": query_date})
                        if check_result.fetchone():
                            matched_ts_code = variant
                            break
                    if not matched_ts_code:
                        return None
                    latest_date = query_date
                else:
                    latest_date = None
                    matched_ts_code = None
                    for variant in ts_code_variants:
                        date_query = "SELECT MAX(trade_date) as latest_date FROM dc_index WHERE ts_code = :ts_code"
                        date_result = conn.execute(text(date_query), {"ts_code": variant})
                        row = date_result.fetchone()
                        if row and row.latest_date:
                            latest_date = row.latest_date
                            matched_ts_code = variant
                            break

                if not latest_date:
                    return None

                query = """
                    SELECT 
                        ts_code,
                        name,
                        "leading",
                        leading_code,
                        pct_change,
                        leading_pct,
                        total_mv,
                        turnover_rate,
                        up_num,
                        down_num,
                        idx_type,
                        "level"
                    FROM dc_index
                    WHERE ts_code = :ts_code AND trade_date = :trade_date
                """
                result = conn.execute(text(query), {"ts_code": matched_ts_code, "trade_date": latest_date})
                row = result.fetchone()

                if not row:
                    return None

                return {
                    "code": row.ts_code,
                    "name": row.name,
                    "type": "concept",
                    "change_pct": float(row.pct_change or 0),
                    "leading": row.leading,
                    "leading_code": row.leading_code,
                    "leading_pct": float(row.leading_pct or 0),
                    "total_mv": float(row.total_mv or 0),
                    "turnover_rate": float(row.turnover_rate or 0),
                    "up_num": int(row.up_num or 0),
                    "down_num": int(row.down_num or 0),
                    "idx_type": row.idx_type,
                    "level": row.level,
                    "trade_date": latest_date.strftime("%Y-%m-%d") if hasattr(latest_date, 'strftime') else str(latest_date),
                    "stock_count": int(row.up_num or 0) + int(row.down_num or 0),
                }

        except Exception as e:
            print(f"Get concept sector detail error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_concept_sector_stocks(
        self, ts_code: str, sort: str = "default", trend: Optional[str] = None, trade_date: Optional[str] = None
    ) -> List[Dict]:
        try:
            with self.engine.connect() as conn:
                ts_code_variants = [ts_code]
                if ts_code.endswith('.DC'):
                    ts_code_variants.append(ts_code[:-3])
                else:
                    ts_code_variants.append(ts_code + '.DC')

                if trade_date:
                    from datetime import datetime as dt
                    query_date = dt.strptime(trade_date, "%Y-%m-%d").date()
                    matched_ts_code = None
                    for variant in ts_code_variants:
                        check_query = "SELECT 1 FROM dc_member WHERE ts_code = :ts_code AND trade_date = :trade_date LIMIT 1"
                        check_result = conn.execute(text(check_query), {"ts_code": variant, "trade_date": query_date})
                        if check_result.fetchone():
                            matched_ts_code = variant
                            break
                    if not matched_ts_code:
                        logger.warning(f"dc_member no data found for ts_code={ts_code}, trade_date={trade_date}")
                        return []
                    latest_date = query_date
                else:
                    latest_date = None
                    matched_ts_code = None
                    for variant in ts_code_variants:
                        date_query = "SELECT MAX(trade_date) as latest_date FROM dc_member WHERE ts_code = :ts_code"
                        date_result = conn.execute(text(date_query), {"ts_code": variant})
                        row = date_result.fetchone()
                        if row and row.latest_date:
                            latest_date = row.latest_date
                            matched_ts_code = variant
                            break

                    if not latest_date:
                        logger.warning(f"dc_member no data found for ts_code variants: {ts_code_variants}")
                        return []

                logger.info(f"dc_member query: ts_code={matched_ts_code}, trade_date={latest_date}")

                order_clause = "sb.symbol"
                if sort == "asc":
                    order_clause = "dd.pct_chg ASC NULLS LAST"
                elif sort == "desc":
                    order_clause = "dd.pct_chg DESC NULLS LAST"
                elif sort == "volume_asc":
                    order_clause = "dd.vol ASC NULLS LAST"
                elif sort == "volume_desc":
                    order_clause = "dd.vol DESC NULLS LAST"

                trend_params = {"ts_code": matched_ts_code, "trade_date": latest_date}

                query = f"""
                    SELECT
                        COALESCE(sb.ts_code, dm.con_code) as ts_code,
                        COALESCE(sb.symbol, SPLIT_PART(dm.con_code, '.', 1)) as symbol,
                        COALESCE(sb.name, dm.name) as name,
                        sb.industry,
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
                    FROM dc_member dm
                    LEFT JOIN stock_basic sb ON sb.ts_code = dm.con_code
                    LEFT JOIN LATERAL (
                        SELECT *
                        FROM daily_data
                        WHERE ts_code = dm.con_code
                        ORDER BY trade_date DESC
                        LIMIT 1
                    ) dd ON true
                    WHERE dm.ts_code = :ts_code 
                      AND dm.trade_date = :trade_date
                      {'AND (sb.trend = 1 OR sb.trend IS NULL)' if trend == 'up' else 'AND (sb.trend = -1 OR sb.trend IS NULL)' if trend == 'down' else ''}
                    ORDER BY {order_clause}
                """
                result = conn.execute(text(query), trend_params)

                stocks = []
                for row in result:
                    price = float(row.price or 0)
                    pre_close = float(row.pre_close or 0)
                    change = price - pre_close if pre_close > 0 else 0

                    stocks.append({
                        "ts_code": row.ts_code,
                        "symbol": row.symbol,
                        "name": row.name,
                        "industry": row.industry,
                        "price": price,
                        "pre_close": pre_close,
                        "open": float(row.open or 0),
                        "high": float(row.high or 0),
                        "low": float(row.low or 0),
                        "change_pct": float(row.change_pct or 0),
                        "change": round(change, 2),
                        "volume": int(row.volume or 0),
                        "amount": float(row.amount or 0),
                        "trade_date": row.trade_date.strftime("%Y-%m-%d") if row.trade_date else "",
                        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })

                return stocks

        except Exception as e:
            logger.error(f"Get concept sector stocks error: {e}", exc_info=True)
            return []

    def get_sector_large_orders(self, trade_date: str) -> List[Dict]:
        """
        获取板块大单交易统计（按行业汇总）

        Args:
            trade_date: 交易日期，格式 YYYY-MM-DD

        Returns:
            板块大单统计数据列表
        """
        try:
            with self.engine.connect() as conn:
                query = """
                    SELECT 
                        m.trade_date,
                        sb.industry,
                        ROUND(SUM(m.buy_lg_amount)::numeric, 2) as buy_lg_amount,
                        ROUND(SUM(m.sell_lg_amount)::numeric, 2) as sell_lg_amount,
                        ROUND(SUM(m.buy_elg_amount)::numeric, 2) as buy_elg_amount,
                        ROUND(SUM(m.sell_elg_amount)::numeric, 2) as sell_elg_amount
                    FROM moneyflow m
                    LEFT JOIN stock_basic sb ON sb.ts_code = m.ts_code
                    WHERE m.trade_date = :trade_date
                      AND sb.industry IS NOT NULL
                      AND sb.industry != ''
                    GROUP BY m.trade_date, sb.industry
                    ORDER BY (SUM(m.buy_lg_amount) + SUM(m.buy_elg_amount)) DESC
                """
                result = conn.execute(text(query), {"trade_date": trade_date})

                items = []
                for row in result:
                    buy_lg = float(row.buy_lg_amount or 0)
                    sell_lg = float(row.sell_lg_amount or 0)
                    buy_elg = float(row.buy_elg_amount or 0)
                    sell_elg = float(row.sell_elg_amount or 0)
                    net_lg = buy_lg - sell_lg
                    net_elg = buy_elg - sell_elg
                    net_total = net_lg + net_elg

                    items.append({
                        "trade_date": row.trade_date.strftime("%Y-%m-%d") if row.trade_date else trade_date,
                        "industry": row.industry,
                        "buy_lg_amount": buy_lg,
                        "sell_lg_amount": sell_lg,
                        "buy_elg_amount": buy_elg,
                        "sell_elg_amount": sell_elg,
                        "net_lg_amount": round(net_lg, 2),
                        "net_elg_amount": round(net_elg, 2),
                        "net_total_amount": round(net_total, 2),
                    })

                return items

        except Exception as e:
            print(f"Get sector large orders error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_stock_concepts(self, con_code: str) -> List[Dict]:
        """
        获取股票所属的概念板块列表（反向查询：根据股票代码查 dc_member + dc_index）

        Args:
            con_code: 股票代码，如 688275.SH

        Returns:
            概念板块名称列表
        """
        try:
            with self.engine.connect() as conn:
                # 获取最新的 trade_date
                date_query = "SELECT MAX(trade_date) as latest_date FROM dc_member WHERE con_code = :con_code"
                date_result = conn.execute(text(date_query), {"con_code": con_code})
                date_row = date_result.fetchone()
                if not date_row or not date_row.latest_date:
                    return []
                latest_date = date_row.latest_date

                query = """
                    SELECT DISTINCT di.name, di.ts_code, di.pct_change
                    FROM dc_member dm
                    LEFT JOIN dc_index di ON di.ts_code = dm.ts_code AND di.trade_date = dm.trade_date
                    WHERE dm.con_code = :con_code
                      AND dm.trade_date = :trade_date
                      AND di.idx_type = '概念板块'
                    ORDER BY di.name
                """
                result = conn.execute(text(query), {"con_code": con_code, "trade_date": latest_date})

                concepts = []
                for row in result:
                    concepts.append({
                        "name": row.name,
                        "ts_code": row.ts_code,
                        "change_pct": float(row.pct_change or 0),
                    })

                return concepts

        except Exception as e:
            logger.error(f"Get stock concepts error: {e}", exc_info=True)
            return []

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
