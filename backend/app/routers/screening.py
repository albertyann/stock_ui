import json
import math
import bisect
from datetime import date
from typing import Optional
from collections import OrderedDict
from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_admin
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db

router = APIRouter(
    prefix="/screening",
    tags=["screening"],
    dependencies=[Depends(require_admin)],
)


@router.get("/heat", response_model=dict)
async def get_screening_heat(
    days: int = Query(120, description="回溯天数"),
    end_date: Optional[str] = Query(None, description="截止日期 (YYYY-MM-DD)"),
    strategy_name: Optional[str] = Query(None, description="按策略筛选，如 HighScoreRsiStrong / RsiStrong"),
    db: AsyncSession = Depends(get_db),
):
    """获取选股结果热度：按天统计筛选出的股票数量，反映市场交易活跃度。"""
    try:
        if end_date:
            date_condition = "AND trade_date <= :end_date"
            cal_date_condition = "AND cal_date <= :end_date"
        else:
            date_condition = ""
            cal_date_condition = ""

        if strategy_name:
            strategy_condition = "AND strategy_name = :strategy_name"
        else:
            strategy_condition = ""

        sql = text(f"""
            SELECT
                tc.cal_date::TEXT AS trade_date,
                COALESCE(sr.stock_count, 0) AS stock_count
            FROM (
                SELECT DISTINCT cal_date
                FROM trade_cal
                WHERE is_open = 1
                    AND cal_date >= CURRENT_DATE - CAST(:days AS INTEGER) * INTERVAL '1 day'
                    {cal_date_condition}
            ) tc
            LEFT JOIN (
                SELECT
                    trade_date,
                    COUNT(DISTINCT ts_code) AS stock_count
                FROM screening_results
                WHERE trade_date >= CURRENT_DATE - CAST(:days AS INTEGER) * INTERVAL '1 day'
                    {date_condition}
                    {strategy_condition}
                GROUP BY trade_date
            ) sr ON tc.cal_date = sr.trade_date
            ORDER BY tc.cal_date ASC
        """)

        params = {"days": days}
        if end_date:
            # asyncpg 的 DATE 参数不接受字符串，需转为 date 对象
            params["end_date"] = date.fromisoformat(end_date)
        if strategy_name:
            params["strategy_name"] = strategy_name

        result = await db.execute(sql, params)
        rows = result.fetchall()

        data = [
            {"trade_date": row[0], "stock_count": row[1]}
            for row in rows
        ]

        total_dates = len(data)
        avg_count = round(sum(r["stock_count"] for r in data) / total_dates, 1) if total_dates > 0 else 0

        # ---------------- industry breakdown (stacked bar) ----------------
        industry_sql = text(f"""
            SELECT
                trade_date::TEXT,
                industry,
                COUNT(DISTINCT ts_code) AS stock_count
            FROM screening_results
            WHERE trade_date >= CURRENT_DATE - CAST(:days AS INTEGER) * INTERVAL '1 day'
                {date_condition}
                {strategy_condition}
                AND industry IS NOT NULL
            GROUP BY trade_date, industry
            ORDER BY trade_date ASC, industry ASC
        """)
        industry_result = await db.execute(industry_sql, params)
        industry_rows = industry_result.fetchall()

        daily_industries = OrderedDict()
        for row in industry_rows:
            trade_date = row[0]
            industry = row[1]
            count = row[2]
            if trade_date not in daily_industries:
                daily_industries[trade_date] = {}
            daily_industries[trade_date][industry] = count

        dates = list(daily_industries.keys())
        all_industries = sorted(set(
            ind for day in daily_industries.values() for ind in day
        ))

        series = {}
        for ind in all_industries:
            vals = [daily_industries[d].get(ind, 0) for d in dates]
            vals = [v if v >= 5 else 0 for v in vals]
            if any(v > 0 for v in vals):
                series[ind] = vals

        industry_data = {"dates": dates, "series": series}
        # ----------------------------------------------------------------

        return {
            "success": True,
            "data": data,
            "industry_data": industry_data,
            "meta": {
                "days": days,
                "total_dates": total_dates,
                "avg_stock_count": avg_count,
            },
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "data": [], "meta": {}}


@router.get("/results", response_model=dict)
async def get_screening_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    strategy_name: Optional[str] = None,
    industry: Optional[str] = None,
    ts_code: Optional[str] = None,
    name: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    min_score: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
):
    """分页查询选股结果，支持多条件筛选，按交易日降序、评分降序排列。"""
    try:
        conditions = []
        params: dict = {}

        if strategy_name:
            conditions.append("strategy_name = :strategy_name")
            params["strategy_name"] = strategy_name
        if industry:
            conditions.append("industry = :industry")
            params["industry"] = industry
        if ts_code:
            conditions.append("ts_code ILIKE :ts_code")
            params["ts_code"] = f"%{ts_code}%"
        if name:
            conditions.append("name ILIKE :name")
            params["name"] = f"%{name}%"
        if date_start:
            conditions.append("trade_date >= :date_start")
            params["date_start"] = date_start
        if date_end:
            conditions.append("trade_date <= :date_end")
            params["date_end"] = date_end
        if min_score is not None:
            conditions.append("score >= :min_score")
            params["min_score"] = min_score

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        count_sql = text(f"SELECT COUNT(*) AS total FROM screening_results {where}")
        count_result = await db.execute(count_sql, params)
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset

        sql = text(f"""
            SELECT id, strategy_name, ts_code, name, industry, score, trade_date, details, created_at
            FROM screening_results
            {where}
            ORDER BY trade_date DESC, score DESC, ts_code ASC
            LIMIT :limit OFFSET :offset
        """)
        result = await db.execute(sql, params)
        rows = result.fetchall()

        data = []
        for row in rows:
            details = row.details
            if isinstance(details, str):
                details = json.loads(details)
            data.append(
                {
                    "id": row.id,
                    "strategy_name": row.strategy_name,
                    "ts_code": row.ts_code,
                    "name": row.name,
                    "industry": row.industry,
                    "score": float(row.score) if row.score is not None else None,
                    "trade_date": row.trade_date.strftime("%Y-%m-%d") if row.trade_date else None,
                    "details": details,
                    "created_at": (
                        row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None
                    ),
                }
            )

        return {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e), "data": [], "pagination": {}}


@router.get("/results/meta", response_model=dict)
async def get_screening_results_meta(
    db: AsyncSession = Depends(get_db),
):
    """获取筛选下拉选项：策略列表、行业列表、最新交易日。"""
    try:
        strategy_sql = text("SELECT DISTINCT strategy_name FROM screening_results ORDER BY 1")
        strategy_result = await db.execute(strategy_sql)
        strategies = [row[0] for row in strategy_result.fetchall()]

        industry_sql = text(
            "SELECT DISTINCT industry FROM screening_results WHERE industry IS NOT NULL ORDER BY 1"
        )
        industry_result = await db.execute(industry_sql)
        industries = [row[0] for row in industry_result.fetchall()]

        latest_sql = text("SELECT MAX(trade_date) AS latest FROM screening_results")
        latest_result = await db.execute(latest_sql)
        latest = latest_result.scalar()

        return {
            "success": True,
            "data": {
                "strategies": strategies,
                "industries": industries,
                "latest_date": latest.strftime("%Y-%m-%d") if latest else None,
            },
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e), "data": {}}


async def _resolve_strong_window(
    db: AsyncSession,
    strategy_name: Optional[str],
    days: int,
    min_score: float,
) -> tuple[list, list, int, dict | None]:
    """计算强势信号窗口（最近 5 个交易日）内的候选股票。

    返回 (data, date_strs, n_dates, meta)。data 为窗口内达标股票列表，
    meta 为 None 表示窗口交易日不足 days（此时 data 为空）。
    """
    strategy_name = strategy_name or "RsiStrong"
    window = 5  # 固定回溯窗口：最近 5 个交易日
    date_sql = text("""
        SELECT DISTINCT trade_date
        FROM screening_results
        WHERE strategy_name = :strategy_name
        ORDER BY trade_date DESC
        LIMIT :window
    """)
    date_result = await db.execute(
        date_sql, {"strategy_name": strategy_name, "window": window}
    )
    dates = [r[0] for r in date_result.fetchall()]

    if len(dates) < days:
        return [], [d.strftime("%Y-%m-%d") for d in dates], len(dates), None

    sql = text("""
        SELECT sr.ts_code, sr.name, sr.industry, sr.trade_date, sr.score
        FROM screening_results sr
        WHERE sr.strategy_name = :strategy_name
          AND sr.trade_date = ANY(:dates)
        ORDER BY sr.ts_code ASC, sr.trade_date ASC
    """)
    result = await db.execute(
        sql, {"strategy_name": strategy_name, "dates": dates}
    )
    rows = result.fetchall()

    from collections import defaultdict

    stock_map = defaultdict(dict)
    for row in rows:
        stock_map[row.ts_code][row.trade_date] = (row.name, row.industry, float(row.score))

    date_strs = [d.strftime("%Y-%m-%d") for d in dates]
    latest_date = max(dates)

    data = []
    for ts_code, day_map in stock_map.items():
        # 统计窗口内评分 >= min_score 的天数（不要求连续）
        qualify_days = sum(
            1 for d in dates if d in day_map and day_map[d][2] >= min_score
        )
        if qualify_days < days:
            continue

        scores = OrderedDict()
        for d in dates:
            day_str = d.strftime("%Y-%m-%d")
            scores[day_str] = day_map[d][2] if d in day_map else None

        present_scores = [s for s in scores.values() if s is not None]
        avg_score = round(sum(present_scores) / len(present_scores), 2) if present_scores else None
        first_item = next(iter(day_map.values()))

        data.append(
            {
                "ts_code": ts_code,
                "name": first_item[0],
                "industry": first_item[1],
                "scores": dict(scores),
                "latest_score": day_map[latest_date][2] if latest_date in day_map else None,
                "avg_score": avg_score,
                "days_continuous": qualify_days,
            }
        )

    data.sort(key=lambda x: x["avg_score"] if x["avg_score"] is not None else 0, reverse=True)
    return data, date_strs, len(dates), {
        "strategy_name": strategy_name,
        "min_score": min_score,
        "window": window,
    }


@router.get("/strong-continuous", response_model=dict)
async def get_screening_strong_continuous(
    strategy_name: Optional[str] = Query("RsiStrong", description="策略名称"),
    days: int = Query(2, ge=1, le=5, description="5 天窗口内需满足评分阈值的天数"),
    min_score: float = Query(95, description="最低评分阈值"),
    db: AsyncSession = Depends(get_db),
):
    """强势信号：过去 5 个交易日内评分 >= min_score 的天数 >= days 即入选（不要求连续）。

    策略固定为 RsiStrong（默认）。取最近 5 个交易日作为固定窗口，统计个股在窗口内
    评分 >= min_score（默认 95）的天数，该天数 >= days 即视为“强势”，不要求连续。
    窗口内评分低于阈值的日期也会返回，便于前端展示（且不计入达标天数）。
    """
    try:
        data, date_strs, n_dates, meta = await _resolve_strong_window(
            db, strategy_name, days, min_score
        )

        if meta is None:
            return {
                "success": True,
                "data": [],
                "dates": date_strs,
                "days": n_dates,
            }

        return {
            "success": True,
            "data": data,
            "dates": date_strs,
            "days": n_dates,
            "meta": meta,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e), "data": [], "dates": []}


def _wilson_ci(success: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval（二项比例置信区间，小样本更稳健）。"""
    if total <= 0:
        return (0.0, 0.0)
    p = success / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    margin = (z * math.sqrt((p * (1 - p) / total) + (z * z / (4 * total * total)))) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


@router.get("/strong-continuous/eval", response_model=dict)
async def get_screening_strong_continuous_eval(
    strategy_name: Optional[str] = Query("RsiStrong", description="策略名称"),
    days: int = Query(2, ge=1, le=5, description="5 天窗口内需满足评分阈值的天数"),
    min_score: float = Query(95, description="最低评分阈值"),
    db: AsyncSession = Depends(get_db),
):
    """强势信号质量评估：信号出现后次日上涨概率 + 基准对照 + 逐股历史命中率。

    统计口径与 worker/scripts/analyze_rsi_strong_nextday.py 一致：
    - 原子事件 = 符合条件的 (ts_code, trade_date) 且 score >= min_score；
    - 「上涨」= 下一交易日 pct_chg > 0（次收 vs 昨收）；
    - 下一交易日 = trade_cal 中严格大于信号日的最近开市日；
    - 基准 = 同一批次日日期集合上全市场 pct_chg>0 的比例（剔除市场 beta）。
    """
    try:
        strategy_name = strategy_name or "RsiStrong"
        window_data, date_strs, n_dates, meta = await _resolve_strong_window(
            db, strategy_name, days, min_score
        )

        # 1. 原子事件
        events_sql = text("""
            SELECT ts_code, trade_date
            FROM screening_results
            WHERE strategy_name = :s AND score >= :min_score
            ORDER BY trade_date
        """)
        events = (
            await db.execute(
                events_sql, {"s": strategy_name, "min_score": min_score}
            )
        ).fetchall()

        summary = {
            "total_events": len(events),
            "valid_events": 0,
            "up_count": 0,
            "up_rate": None,
            "ci95": {"lo": None, "hi": None},
            "avg_pct_chg": None,
            "market_baseline_up_rate": None,
            "excess": None,
        }

        per_stock: dict = {}

        if events:
            # 2. 交易日历（开市日升序）
            cal_sql = text(
                "SELECT cal_date FROM trade_cal WHERE exchange = 'SSE' AND is_open = 1 ORDER BY cal_date"
            )
            cal = [r[0] for r in (await db.execute(cal_sql)).fetchall()]

            # 3. 批量解析次日 + 批量取行情
            next_dates: set = set()
            codes: set = set()
            for ts_code, trade_date in events:
                idx = bisect.bisect_right(cal, trade_date)
                if idx < len(cal):
                    next_dates.add(cal[idx])
                    codes.add(ts_code)

            price_map: dict = {}
            if codes and next_dates:
                price_sql = text("""
                    SELECT ts_code, trade_date, open, close, pct_chg
                    FROM daily_data
                    WHERE ts_code = ANY(:codes) AND trade_date = ANY(:dates)
                """)
                for prow in (
                    await db.execute(
                        price_sql, {"codes": list(codes), "dates": list(next_dates)}
                    )
                ).fetchall():
                    price_map[(prow[0], prow[1])] = (
                        float(prow[2]),  # open
                        float(prow[3]),  # close
                        float(prow[4]),  # pct_chg
                    )

            # 4. 逐事件结果 + 逐股聚合
            from collections import defaultdict

            by_code: dict = defaultdict(list)
            valid_pcts: list = []
            total_valid = 0
            up_count = 0
            used_next_dates: set = set()

            for ts_code, trade_date in events:
                idx = bisect.bisect_right(cal, trade_date)
                next_date = cal[idx] if idx < len(cal) else None
                entry = {
                    "td": trade_date,
                    "nd": next_date,
                    "pct": None,
                    "otc": None,
                }
                if next_date is not None:
                    pr = price_map.get((ts_code, next_date))
                    if pr is not None:
                        open_, close_, pct = pr
                        entry["pct"] = pct
                        if open_ and open_ != 0 and close_ is not None:
                            entry["otc"] = (close_ - open_) / open_ * 100
                        used_next_dates.add(next_date)
                        total_valid += 1
                        valid_pcts.append(pct)
                        if pct > 0:
                            up_count += 1
                by_code[ts_code].append(entry)

            # 5. 全市场基准（同一批次日日期集合横截面）
            baseline_up_rate = None
            if used_next_dates:
                base_sql = text("""
                    SELECT COUNT(*) AS total,
                           COUNT(*) FILTER (WHERE pct_chg > 0) AS up
                    FROM daily_data
                    WHERE trade_date = ANY(:dates)
                """)
                b = (await db.execute(base_sql, {"dates": list(used_next_dates)})).fetchone()
                if b and b[0]:
                    baseline_up_rate = b[1] / b[0]

            # 6. 逐股历史命中率 + 最近信号次日结果
            for ts_code, lst in by_code.items():
                valid = [x for x in lst if x["pct"] is not None]
                n = len(valid)
                up = sum(1 for x in valid if x["pct"] > 0)
                latest = max(lst, key=lambda x: x["td"])
                per_stock[ts_code] = {
                    "hist": {
                        "n": n,
                        "up": up,
                        "up_rate": round(up / n, 4) if n else None,
                    },
                    "latest_signal_date": latest["td"].strftime("%Y-%m-%d"),
                    "latest_next_date": (
                        latest["nd"].strftime("%Y-%m-%d") if latest["nd"] else None
                    ),
                    "latest_next_pct": (
                        round(latest["pct"], 2) if latest["pct"] is not None else None
                    ),
                    "latest_is_up": (
                        latest["pct"] is not None and latest["pct"] > 0
                    ),
                    "latest_otc": round(latest["otc"], 2) if latest["otc"] is not None else None,
                }

            if total_valid > 0:
                ci_lo, ci_hi = _wilson_ci(up_count, total_valid)
                summary = {
                    "total_events": len(events),
                    "valid_events": total_valid,
                    "up_count": up_count,
                    "up_rate": round(up_count / total_valid, 4),
                    "ci95": {"lo": round(ci_lo, 4), "hi": round(ci_hi, 4)},
                    "avg_pct_chg": round(sum(valid_pcts) / len(valid_pcts), 4),
                    "market_baseline_up_rate": (
                        round(baseline_up_rate, 4) if baseline_up_rate is not None else None
                    ),
                    "excess": (
                        round(up_count / total_valid - baseline_up_rate, 4)
                        if baseline_up_rate is not None
                        else None
                    ),
                }

        # 7. 逐股结果合并到窗口数据
        for stock in window_data:
            stock["hist"] = per_stock.get(stock["ts_code"], {}).get("hist", None)
            extra = per_stock.get(stock["ts_code"], {})
            stock["next_day"] = {
                "signal_date": extra.get("latest_signal_date"),
                "next_date": extra.get("latest_next_date"),
                "next_pct_chg": extra.get("latest_next_pct"),
                "is_up": extra.get("latest_is_up"),
                "open_to_close": extra.get("latest_otc"),
            }

        return {
            "success": True,
            "data": window_data,
            "dates": date_strs,
            "days": n_dates,
            "meta": meta,
            "summary": summary,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "dates": [],
            "summary": {},
        }


@router.get("/trend", response_model=dict)
async def get_screening_trend(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    strategy_name: Optional[str] = None,
    industry: Optional[str] = None,
    ts_code: Optional[str] = None,
    name: Optional[str] = None,
    signal_date: Optional[date] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    min_score: Optional[float] = None,
    market_type: Optional[str] = Query(None, description="板块筛选：main/chye/kcb"),
    days: Optional[str] = Query(None, description="逗号分隔的 T+N 偏移，如 1,3,5,10,20"),
    db: AsyncSession = Depends(get_db),
):
    """分页查询选股信号，并计算信号日后 T+N 交易日的单日涨幅与前复权累计涨幅。"""
    try:
        if days:
            offsets = sorted({int(d.strip()) for d in days.split(",") if d.strip()})
            if any(n < 1 for n in offsets):
                raise ValueError("days 偏移必须为 >= 1 的整数")
            offsets = offsets[:10]
        else:
            offsets = [1, 3, 5, 10, 20]

        conditions = []
        params: dict = {}

        if strategy_name:
            conditions.append("strategy_name = :strategy_name")
            params["strategy_name"] = strategy_name
        if industry:
            conditions.append("industry = :industry")
            params["industry"] = industry
        if ts_code:
            conditions.append("ts_code ILIKE :ts_code")
            params["ts_code"] = f"%{ts_code}%"
        if name:
            conditions.append("name ILIKE :name")
            params["name"] = f"%{name}%"
        if date_start:
            conditions.append("trade_date >= :date_start")
            params["date_start"] = date_start
        if date_end:
            conditions.append("trade_date <= :date_end")
            params["date_end"] = date_end
        if min_score is not None:
            conditions.append("score >= :min_score")
            params["min_score"] = min_score
        if signal_date:
            conditions.append("trade_date = :signal_date")
            params["signal_date"] = signal_date
        if market_type:
            prefixes = {
                "main": ("600", "601", "603", "605", "000", "001", "002", "003"),
                "chye": ("300", "301"),
                "kcb": ("688", "689"),
            }.get(market_type)
            if prefixes:
                quoted = ", ".join(f"'{p}'" for p in prefixes)
                conditions.append(f"substring(ts_code, 1, 3) IN ({quoted})")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        count_sql = text(f"SELECT COUNT(*) AS total FROM screening_results {where}")
        count_result = await db.execute(count_sql, params)
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset

        sql = text(f"""
            SELECT id, strategy_name, ts_code, name, industry, score, trade_date
            FROM screening_results
            {where}
            ORDER BY trade_date DESC, score DESC, ts_code ASC
            LIMIT :limit OFFSET :offset
        """)
        result = await db.execute(sql, params)
        rows = result.fetchall()

        data = []
        trading_dates: dict = {}

        if rows:
            min_signal_date = min(row.trade_date for row in rows)

            cal_sql = text("""
                SELECT cal_date FROM trade_cal
                WHERE exchange = 'SSE' AND is_open = 1 AND cal_date >= :min_date
                ORDER BY cal_date ASC
            """)
            cal_result = await db.execute(cal_sql, {"min_date": min_signal_date})
            cal_dates = [r[0] for r in cal_result.fetchall()]

            def resolve_trade_date(base_date, n):
                """T+N = 基准日起（含）第 N 个开市交易日，与 realtime_service 语义一致。"""
                idx = bisect.bisect_left(cal_dates, base_date) + n
                return cal_dates[idx] if idx < len(cal_dates) else None

            all_offsets = [0] + offsets
            resolved = {}  # (signal_date, offset) -> resolved date or None
            date_set = set()
            code_set = set()
            for row in rows:
                code_set.add(row.ts_code)
                for n in all_offsets:
                    d = resolve_trade_date(row.trade_date, n)
                    resolved[(row.trade_date, n)] = d
                    if d is not None:
                        date_set.add(d)

            price_map = {}
            if code_set and date_set:
                price_sql = text("""
                    SELECT d.ts_code, d.trade_date, d.close, d.pct_chg, a.adj_factor
                    FROM daily_data d
                    LEFT JOIN adj_factor a ON d.ts_code = a.ts_code AND d.trade_date = a.trade_date
                    WHERE d.ts_code = ANY(:codes)
                    AND d.trade_date = ANY(:dates)
                    ORDER BY d.ts_code, d.trade_date
                """)
                price_result = await db.execute(
                    price_sql,
                    {"codes": list(code_set), "dates": list(date_set)},
                )
                for prow in price_result.fetchall():
                    date_str = prow.trade_date.strftime("%Y-%m-%d")
                    price_map[(prow.ts_code, date_str)] = {
                        "close": float(prow.close) if prow.close is not None else None,
                        "pct_chg": float(prow.pct_chg) if prow.pct_chg is not None else None,
                        "adj_factor": (
                            float(prow.adj_factor) if prow.adj_factor is not None else None
                        ),
                    }

            for row in rows:
                signal_date_str = row.trade_date.strftime("%Y-%m-%d")
                row_data = {
                    "id": row.id,
                    "strategy_name": row.strategy_name,
                    "ts_code": row.ts_code,
                    "name": row.name,
                    "industry": row.industry,
                    "score": float(row.score) if row.score is not None else None,
                    "signal_date": signal_date_str,
                }

                date_labels = {}
                for n in all_offsets:
                    d = resolved[(row.trade_date, n)]
                    date_labels[f"T+{n}"] = d.strftime("%Y-%m-%d") if d else None
                trading_dates[signal_date_str] = date_labels

                def price_at(n):
                    d = resolved[(row.trade_date, n)]
                    if d is None:
                        return None
                    return price_map.get((row.ts_code, d.strftime("%Y-%m-%d")))

                base = price_at(0)
                row_data["close_T+0"] = base["close"] if base else None
                row_data["change_T+0"] = (
                    round(base["pct_chg"], 2) if base and base["pct_chg"] is not None else None
                )

                for n in offsets:
                    info = price_at(n)
                    change = None
                    cumulative = None
                    if info:
                        if info["pct_chg"] is not None:
                            change = round(info["pct_chg"], 2)
                        if base and base["close"] and info["close"]:
                            adj_n = info["adj_factor"]
                            adj_0 = base["adj_factor"]
                            if adj_n is not None and adj_0 is not None:
                                cumulative = (
                                    (info["close"] * adj_n) / (base["close"] * adj_0) * 100 - 100
                                )
                            else:
                                cumulative = info["close"] / base["close"] * 100 - 100
                            cumulative = round(cumulative, 2)
                    row_data[f"change_T+{n}"] = change
                    row_data[f"cumulative_change_T+{n}"] = cumulative

                data.append(row_data)

        return {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
            "trading_dates": trading_dates,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "pagination": {},
            "trading_dates": {},
        }
