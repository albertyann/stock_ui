import json
import shutil
import subprocess
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import create_engine, text
from app.config import get_settings
from app.market.context import get_current_market
from app.market.filter import build_sql_filter


class StockService:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    def search_stocks(self, keyword: str, limit: int = 20) -> List[dict]:
        try:
            settings = get_settings()
            sync_url = settings.database_url.replace("+asyncpg", "")
            engine = create_engine(sync_url)

            with engine.connect() as conn:
                market = get_current_market()
                market_sql, market_params = build_sql_filter(market, "ts_code")
                params = {"keyword": f"%{keyword}%", "limit": limit}
                params.update(market_params)

                query = f"""
                    SELECT DISTINCT ts_code, symbol, name
                    FROM watchlist_stocks
                    WHERE (name ILIKE :keyword OR ts_code ILIKE :keyword OR symbol ILIKE :keyword)
                    AND {market_sql}
                    LIMIT :limit
                """
                result = conn.execute(text(query), params)

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

                indicators_result = conn.execute(
                    text("""
                    SELECT 
                        turnover_rate,
                        pe,
                        pb,
                        total_mv,
                        trade_date
                    FROM daily_basic
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
                            d.trade_date as date,
                            d.open,
                            d.high,
                            d.low,
                            d.close,
                            d.vol as volume,
                            d.amount,
                            d.pct_chg as change_pct,
                            a.adj_factor
                        FROM daily_data d
                        LEFT JOIN adj_factor a ON d.ts_code = a.ts_code AND d.trade_date = a.trade_date
                        WHERE d.ts_code = :ts_code
                        ORDER BY d.trade_date DESC
                        LIMIT :limit
                    """),
                        {"ts_code": ts_code, "limit": limit},
                    )
                elif period == "weekly":
                    result = conn.execute(
                        text("""
                        SELECT 
                            w.trade_date as date,
                            w.open,
                            w.high,
                            w.low,
                            w.close,
                            w.vol as volume,
                            w.amount,
                            w.pct_chg as change_pct,
                            a.adj_factor
                        FROM weekly_data w
                        LEFT JOIN adj_factor a ON w.ts_code = a.ts_code AND w.trade_date = a.trade_date
                        WHERE w.ts_code = :ts_code
                        ORDER BY w.trade_date DESC
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
                    change_pct = float(row.change_pct) if row.change_pct else 0
                    # weekly_data 中 pct_chg 存储为小数(如0.05表示5%)，需乘以100
                    if period == "weekly":
                        change_pct = change_pct * 100
                    kline_data.append(
                        {
                            "date": row.date.strftime("%Y-%m-%d"),
                            "open": float(row.open),
                            "high": float(row.high),
                            "low": float(row.low),
                            "close": float(row.close),
                            "volume": int(row.volume),
                            "amount": float(row.amount),
                            "change_pct": change_pct,
                            "adj_factor": float(row.adj_factor) if row.adj_factor else None,
                        }
                    )

                if period == "weekly" and kline_data:
                    last_weekly_date = kline_data[0]["date"]
                    supp_result = conn.execute(
                        text("""
                        SELECT
                            s.trade_date as date,
                            s.open, s.high, s.low, s.close,
                            s.vol as volume,
                            s.amount,
                            s.pct_chg as change_pct,
                            a.adj_factor
                        FROM stk_weekly_monthly s
                        LEFT JOIN adj_factor a ON s.ts_code = a.ts_code AND s.trade_date = a.trade_date
                        WHERE s.ts_code = :ts_code AND s.freq = 'week'
                        ORDER BY s.trade_date DESC
                        LIMIT 1
                    """),
                        {"ts_code": ts_code},
                    )
                    supp_row = supp_result.fetchone()
                    if supp_row and supp_row.date:
                        supp_date_str = supp_row.date.strftime("%Y-%m-%d")
                        if not last_weekly_date or supp_date_str > last_weekly_date:
                            supp_pct = float(supp_row.change_pct) if supp_row.change_pct else 0
                            # stk_weekly_monthly 的 pct_chg 也是小数，需乘以100
                            # supp_pct = supp_pct
                            kline_data.insert(0, {
                                "date": supp_date_str,
                                "open": float(supp_row.open) if supp_row.open is not None else None,
                                "high": float(supp_row.high) if supp_row.high is not None else None,
                                "low": float(supp_row.low) if supp_row.low is not None else None,
                                "close": float(supp_row.close) if supp_row.close is not None else None,
                                "volume": int(supp_row.volume) if supp_row.volume is not None else None,
                                "amount": float(supp_row.amount) if supp_row.amount is not None else None,
                                "change_pct": supp_pct,
                                "adj_factor": float(supp_row.adj_factor) if supp_row.adj_factor else None,
                            })

                return list(reversed(kline_data))

        except Exception as e:
            print(f"Kline error: {e}")
            import traceback

            traceback.print_exc()
            return []

    def sync_kline_data(self, ts_code: str) -> dict:
        """Delete existing kline data for a stock and re-sync from 2018-01-01.

        Step 1: Delete all daily_data and weekly_data for this ts_code.
        Step 2: Run stock-sync daily_data and weekly_data with date range.
        """
        settings = get_settings()
        sync_url = settings.database_url.replace("+asyncpg", "")
        engine = create_engine(sync_url)

        today = datetime.now().strftime("%Y-%m-%d")
        start_date = "2018-01-01"

        deleted_daily = 0
        deleted_weekly = 0
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("DELETE FROM daily_data WHERE ts_code = :ts_code"),
                    {"ts_code": ts_code},
                )
                deleted_daily = result.rowcount
                conn.commit()

                result = conn.execute(
                    text("DELETE FROM weekly_data WHERE ts_code = :ts_code"),
                    {"ts_code": ts_code},
                )
                deleted_weekly = result.rowcount
                conn.commit()
        except Exception as e:
            print(f"Delete error: {e}")
            return {"success": False, "error": f"Failed to delete data: {str(e)}"}

        try:
            cmd_parts = ["stock-sync"]
            cmd_parts.extend(["run", "daily_data", "--start-date", start_date, "--end-date", today])

            executable = shutil.which("stock-sync")
            if executable:
                cmd_parts[0] = executable

            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=settings.stock_sync_work_dir,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Sync command failed: {result.stderr[:500]}",
                    "deleted_daily": deleted_daily,
                    "deleted_weekly": deleted_weekly,
                }

            return {
                "success": True,
                "deleted_daily": deleted_daily,
                "deleted_weekly": deleted_weekly,
                "sync_output": result.stdout[-500:] if result.stdout else "",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Sync command timed out",
                "deleted_daily": deleted_daily,
                "deleted_weekly": deleted_weekly,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "deleted_daily": deleted_daily,
                "deleted_weekly": deleted_weekly,
            }

    def get_buy_signals(self, ts_code: str, check_days: int = 3) -> dict:
        """调用 worker CLI 检测最近 N 个交易日的买入信号（ma2560 + rsi12）。

        与 sync_kline_data 同样的 subprocess 模式：优先用 shutil.which 找到
        stock-cli 可执行文件，cwd 设为 worker 目录以便读取 worker 的 .env。

        性能优化（Plan A）：先查 Redis 指标批量缓存；命中即直接返回，未命中
        再 fallback 到原 subprocess 实时计算并回写缓存。批量缓存由
        IndicatorCalcService 维护，key 形如 "indicator:calc:result:{date}"。
        """
        cached = self._lookup_buy_signals_cache(ts_code)
        if cached is not None:
            return {"success": True, "data": cached, "source": "cache"}

        settings = get_settings()

        cmd_parts = [
            "stock-cli", "buy-signals",
            "--ts-code", ts_code,
            "--check-days", str(check_days),
            "--output", "stdout-json",
        ]
        executable = shutil.which("stock-cli")
        if executable:
            cmd_parts[0] = executable

        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=settings.worker_timeout,
                cwd=settings.worker_work_dir,
            )
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"worker timeout ({settings.worker_timeout}s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

        if result.returncode != 0:
            err_tail = (result.stderr or "")[-300:]
            return {"success": False, "error": f"worker failed (rc={result.returncode}): {err_tail}"}

        stdout = (result.stdout or "").strip()
        data = None
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            for line in reversed(stdout.splitlines()):
                line = line.strip()
                if line.startswith("{"):
                    try:
                        data = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue
        if data is None:
            return {"success": False, "error": "no JSON found in worker stdout"}

        return {"success": True, "data": data}

    def _lookup_buy_signals_cache(self, ts_code: str) -> Optional[dict]:
        """Look up the batch-computed indicator cache for one stock.

        Returns a buy-signals-shaped dict on hit, or None on miss / when the
        stock is not in the watchlist (non-watchlist stocks have no batch
        cache and must fall back to live subprocess).

        Shape produced here matches `stock-cli buy-signals` stdout so the
        frontend's `response.data.signals` consumption path is unchanged.
        Note: cache reflects only the latest trade date (check_days=1),
        whereas live worker output may cover up to `check_days` days.
        """
        # Local import to avoid circular dependency at module load time.
        from app.redis_client import get_cached_json

        summary = get_cached_json("indicator:calc:last")
        if not summary:
            return None
        end_date = summary.get("end_date")
        if not end_date:
            return None
        result = get_cached_json(f"indicator:calc:result:{end_date}")
        if not result:
            return None

        stock_entry = result.get("stocks", {}).get(ts_code)
        if stock_entry is None:
            return None

        rsi12 = self._convert_indicator_to_buy_signal_shape(
            "rsi12", stock_entry.get("rsi12")
        )
        ma10 = self._convert_indicator_to_buy_signal_shape(
            "ma10", stock_entry.get("ma10")
        )
        ma2560 = self._convert_indicator_to_buy_signal_shape(
            "ma2560", stock_entry.get("ma2560")
        )

        signals = []
        if rsi12 or ma10 or ma2560:
            current_price = None
            for ind in (rsi12, ma10, ma2560):
                if ind and ind.get("_current_price") is not None:
                    current_price = ind["_current_price"]
            for ind in (rsi12, ma10, ma2560):
                if ind:
                    ind.pop("_current_price", None)
            signals.append(
                {
                    "date": end_date,
                    "close": current_price,
                    "ma2560": ma2560,
                    "rsi12": rsi12,
                    "ma10": ma10,
                }
            )

        return {
            "ts_code": ts_code,
            "end_date": end_date,
            "check_days": 1,
            "signals": signals,
        }

    @staticmethod
    def _convert_indicator_to_buy_signal_shape(ind_key: str, cached: Optional[dict]) -> Optional[dict]:
        """Convert one cached indicator entry to the buy-signals entry shape.

        buy-signals output (consumed by frontend charts) per indicator:
            rsi12:  {score, rsi12, consecutive_days}
            ma10:   {score, proximity_pct, ma10, ma60}
            ma2560: {score, proximity_pct, ma25, ma60}

        Cache entry shape:
            {passed, score, details: <raw m_signals indicators JSON>,
             current_price, signal_strength}
        """
        if not cached or not cached.get("passed"):
            return None
        score = float(cached.get("score", 0) or 0)
        details = cached.get("details") or {}
        current_price = cached.get("current_price")

        if ind_key == "rsi12":
            out = {
                "score": score,
                "rsi12": float(details.get("rsi12", 0) or 0),
                "consecutive_days": int(details.get("consecutive_days", 0) or 0),
            }
        elif ind_key == "ma10":
            out = {
                "score": score,
                "proximity_pct": float(details.get("ma10_proximity_pct", 0) or 0),
                "ma10": float(details.get("ma10", 0) or 0),
                "ma60": float(details.get("ma60", 0) or 0),
            }
        elif ind_key == "ma2560":
            out = {
                "score": score,
                "proximity_pct": float(details.get("ma25_proximity_pct", 0) or 0),
                "ma25": float(details.get("ma25", 0) or 0),
                "ma60": float(details.get("ma60", 0) or 0),
            }
        else:
            return None

        # Stash price so the caller can populate `close` once per signal entry.
        out["_current_price"] = current_price
        return out
