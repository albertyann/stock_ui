from typing import Dict, Optional
from sqlalchemy import text


class SectorHeatServiceMixin:
    """板块热度服务 - 统计板块上涨占比和成交额排名"""

    def get_sector_heat(
        self,
        trade_date: Optional[str] = None,
        tab: str = "up_pct",
        idx_type: Optional[str] = None,
        min_stocks: Optional[int] = None,
    ) -> Dict:
        """
        获取板块热度数据

        Args:
            trade_date: 交易日期，格式 YYYY-MM-DD，为 None 时返回最新日期数据
            tab: up_pct=上涨占比排名, amount=成交额排名
            idx_type: 板块类型过滤，如 "概念板块"
            min_stocks: 最小板块股票数量过滤

        Returns:
            板块热度数据列表
        """
        try:
            with self.engine.connect() as conn:
                if trade_date:
                    query_date = trade_date
                else:
                    date_result = conn.execute(
                        text("SELECT MAX(trade_date) as latest_date FROM dc_index")
                    )
                    row = date_result.fetchone()
                    if not row or not row.latest_date:
                        return {"success": True, "data": [], "meta": {"trade_date": None, "tab": tab, "total": 0}}
                    query_date = row.latest_date
                    if hasattr(query_date, 'strftime'):
                        query_date = query_date.strftime("%Y-%m-%d")

                if tab == "up_pct":
                    items = self._get_up_pct_ranking(conn, query_date, idx_type, min_stocks)
                else:
                    items = self._get_amount_ranking(conn, query_date, idx_type, min_stocks)

                return {
                    "success": True,
                    "data": items,
                    "meta": {
                        "trade_date": query_date,
                        "tab": tab,
                        "total": len(items),
                    },
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "data": [], "meta": {}}

    def _get_up_pct_ranking(self, conn, trade_date: str, idx_type: Optional[str] = None, min_stocks: Optional[int] = None) -> list:
        """
        统计每个板块中上涨超过1%的股票占板块总股票数的比例，按比例降序取前30

        利用 dc_index + dc_member + daily_data 三表关联
        """
        query = """
            WITH sector_stocks AS (
                SELECT
                    di.ts_code AS sector_code,
                    di.name AS sector_name,
                    di.idx_type,
                    dm.con_code,
                    dd.pct_chg
                FROM dc_index di
                JOIN dc_member dm ON dm.ts_code = di.ts_code AND dm.trade_date = di.trade_date
                LEFT JOIN daily_data dd ON dd.ts_code = dm.con_code AND dd.trade_date = di.trade_date
                LEFT JOIN stock_basic sb ON sb.ts_code = dm.con_code
                WHERE di.trade_date = :trade_date
                    AND (sb.name IS NULL OR (sb.name NOT LIKE '%%ST%%' AND sb.name NOT LIKE '%%退%%'))
            ),
            sector_stats AS (
                SELECT
                    sector_code,
                    sector_name,
                    idx_type,
                    COUNT(*) AS total_stocks,
                    COUNT(*) FILTER (WHERE pct_chg > 1) AS up_stocks,
                    CASE
                        WHEN COUNT(*) > 0 THEN ROUND(
                            COUNT(*) FILTER (WHERE pct_chg > 1)::numeric / COUNT(*)::numeric * 100, 2
                        )
                        ELSE 0
                    END AS up_pct
                FROM sector_stocks
                GROUP BY sector_code, sector_name, idx_type
                HAVING COUNT(*) > 0
            )
            SELECT sector_code, sector_name, idx_type, total_stocks, up_stocks, up_pct
            FROM sector_stats
            WHERE 1=1
            {idx_type_filter}
            {min_stocks_filter}
            ORDER BY up_pct DESC, up_stocks DESC
            LIMIT 30
        """
        idx_type_filter = "AND idx_type = :idx_type" if idx_type else ""
        min_stocks_filter = "AND total_stocks > :min_stocks" if min_stocks else ""
        query = query.format(idx_type_filter=idx_type_filter, min_stocks_filter=min_stocks_filter)

        params = {"trade_date": trade_date}
        if idx_type:
            params["idx_type"] = idx_type
        if min_stocks:
            params["min_stocks"] = min_stocks

        result = conn.execute(text(query), params)
        items = []
        for idx, row in enumerate(result):
            items.append({
                "rank": idx + 1,
                "sector_code": row.sector_code,
                "sector_name": row.sector_name,
                "idx_type": row.idx_type,
                "total_stocks": int(row.total_stocks),
                "up_stocks": int(row.up_stocks),
                "up_pct": float(row.up_pct),
            })
        return items

    def _get_amount_ranking(self, conn, trade_date: str, idx_type: Optional[str] = None, min_stocks: Optional[int] = None) -> list:
        """
        按板块内所有股票交易金额汇总排序，降序取前30

        利用 dc_index + dc_member + daily_data 三表关联
        """
        query = """
            WITH sector_amount AS (
                SELECT
                    di.ts_code AS sector_code,
                    di.name AS sector_name,
                    di.idx_type,
                    COUNT(DISTINCT dm.con_code) AS total_stocks,
                    COALESCE(SUM(dd.amount), 0) AS total_amount,
                    CASE
                        WHEN COUNT(DISTINCT dm.con_code) > 0
                        THEN COALESCE(SUM(dd.amount), 0) / COUNT(DISTINCT dm.con_code)
                        ELSE 0
                    END AS avg_amount
                FROM dc_index di
                JOIN dc_member dm ON dm.ts_code = di.ts_code AND dm.trade_date = di.trade_date
                LEFT JOIN daily_data dd ON dd.ts_code = dm.con_code AND dd.trade_date = di.trade_date
                LEFT JOIN stock_basic sb ON sb.ts_code = dm.con_code
                WHERE di.trade_date = :trade_date
                    AND (sb.name IS NULL OR (sb.name NOT LIKE '%%ST%%' AND sb.name NOT LIKE '%%退%%'))
                GROUP BY di.ts_code, di.name, di.idx_type
                HAVING SUM(dd.amount) > 0
            )
            SELECT sector_code, sector_name, idx_type, total_stocks, total_amount, avg_amount
            FROM sector_amount
            WHERE 1=1
            {idx_type_filter}
            {min_stocks_filter}
            ORDER BY total_amount DESC
            LIMIT 30
        """
        idx_type_filter = "AND idx_type = :idx_type" if idx_type else ""
        min_stocks_filter = "AND total_stocks > :min_stocks" if min_stocks else ""
        query = query.format(idx_type_filter=idx_type_filter, min_stocks_filter=min_stocks_filter)

        params = {"trade_date": trade_date}
        if idx_type:
            params["idx_type"] = idx_type
        if min_stocks:
            params["min_stocks"] = min_stocks

        result = conn.execute(text(query), params)
        items = []
        for idx, row in enumerate(result):
            items.append({
                "rank": idx + 1,
                "sector_code": row.sector_code,
                "sector_name": row.sector_name,
                "idx_type": row.idx_type,
                "total_stocks": int(row.total_stocks),
                "total_amount": float(row.total_amount),
                "avg_amount": float(row.avg_amount),
            })
        return items
