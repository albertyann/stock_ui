"""Indicator Calculation Service.

Batch-computes three buy-point indicators (rsi12-continuous, ma10-proximity,
ma2560-proximity) for ALL watchlist stocks in one go and caches the result in
Redis so that page reads are O(1) instead of triggering per-stock subprocess
calls.

Flow:
    1. Resolve latest trade date.
    2. Fan out 3 stock-cli subprocess calls (concurrency=4, but only 3 jobs),
       each in `--save` mode so they write passed signals into m_signals.
    3. Read m_signals for the latest date and build per-stock indicator map.
    4. Write the per-stock map + summary into Redis.

Standalone screeners vs the old `buy-signals` command:
    - `buy-signals` checks one ts_code at a time across a 5-day window.
    - Standalone screeners iterate the whole watchlist in one process at a
      single end_date. Much faster (3 subprocess calls vs N per-stock calls),
      but only the natural strategy lookback (rsi12=5d consecutive, etc.)
      is reflected — not a 5-day hit window.
"""

import json
import logging
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import bindparam, create_engine, text

from app.config import get_settings
from app.redis_client import cache_json, get_cached_json

logger = logging.getLogger(__name__)


# Indicator → stock-cli command mapping.
# signal_type: matches what each screener writes into m_signals.signal_type.
# needs_watchlist_flag: rsi12 + ma2560 need `--watchlist`; ma10 defaults to it.
INDICATORS: Dict[str, Dict[str, Any]] = {
    "rsi12": {
        "cli_name": "rsi12-continuous",
        "signal_type": "RSI12_CONTINUOUS",
        "needs_watchlist_flag": True,
    },
    "ma10": {
        "cli_name": "ma10-proximity",
        "signal_type": "MA10_PROXIMITY",
        "needs_watchlist_flag": False,
    },
    "ma2560": {
        "cli_name": "ma2560-proximity",
        "signal_type": "MA25_PROXIMITY",  # screener writes MA25_PROXIMITY, not MA2560_*
        "needs_watchlist_flag": True,
    },
}

REDIS_KEY_RESULT_PREFIX = "indicator:calc:result"
REDIS_KEY_LAST = "indicator:calc:last"


class IndicatorCalcService:
    """Batch-computes indicators for all watchlist stocks and caches in Redis."""

    def __init__(self) -> None:
        self.settings = get_settings()
        sync_url = self.settings.database_url.replace("+asyncpg", "")
        self.engine = create_engine(sync_url)

    def compute_all(self) -> Dict[str, Any]:
        """Run all three indicators against the full watchlist and cache results.

        Returns a summary dict; never raises — failures land in `errors`.
        """
        started_at = datetime.now()

        end_date = self._get_latest_trade_date()
        if not end_date:
            return {"success": False, "error": "no trade date available"}

        watchlist_codes = self._get_all_watchlist_codes()
        if not watchlist_codes:
            return {"success": False, "error": "watchlist is empty"}

        indicator_results: Dict[str, Dict[str, Any]] = {}
        errors: List[str] = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_key = {
                executor.submit(self._run_screener, key, info, end_date): key
                for key, info in INDICATORS.items()
            }
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    ok, msg = future.result()
                except Exception as e:  # defensive: thread shouldn't raise, but be safe
                    ok, msg = False, f"exception: {e}"
                indicator_results[key] = {"success": ok, "message": msg}
                if not ok:
                    errors.append(f"{key}: {msg}")

        signals_map = self._read_signals(end_date, watchlist_codes)

        per_stock: Dict[str, Dict[str, Any]] = {}
        for ts_code in watchlist_codes:
            entry: Dict[str, Any] = {"ts_code": ts_code}
            for ind_key in INDICATORS:
                entry[ind_key] = signals_map.get(ind_key, {}).get(ts_code)
            per_stock[ts_code] = entry

        finished_at = datetime.now()
        summary: Dict[str, Any] = {
            "end_date": str(end_date),
            "computed_at": finished_at.isoformat(),
            "duration_sec": round((finished_at - started_at).total_seconds(), 2),
            "watchlist_total": len(watchlist_codes),
            "passed_counts": {
                k: len(signals_map.get(k, {})) for k in INDICATORS
            },
            "indicator_results": indicator_results,
            "errors": errors,
        }

        # Cache regardless of partial failures — partial data is still useful.
        result_payload = {
            "end_date": str(end_date),
            "computed_at": summary["computed_at"],
            "watchlist_total": len(watchlist_codes),
            "stocks": per_stock,
        }
        self._enrich_with_daily_change(result_payload)
        cache_json(f"{REDIS_KEY_RESULT_PREFIX}:{end_date}", result_payload)
        cache_json(REDIS_KEY_LAST, summary)

        return {"success": True, "data": summary}

    def _enrich_with_daily_change(self, result_payload: Dict[str, Any]) -> None:
        end_date = result_payload.get("end_date")
        stocks = result_payload.get("stocks")
        if not end_date or not stocks:
            return
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(
                    text(
                        """
                        SELECT ts_code, pct_chg
                        FROM daily_data
                        WHERE trade_date = :end_date
                          AND ts_code IN :ts_codes
                        """
                    ).bindparams(bindparam("ts_codes", expanding=True)),
                    {"end_date": end_date, "ts_codes": list(stocks.keys())},
                ).fetchall()
                for r in rows:
                    entry = stocks.get(r.ts_code)
                    if entry is not None:
                        entry["pct_chg"] = float(r.pct_chg) if r.pct_chg is not None else None
        except Exception as e:
            logger.warning("Failed to enrich indicator calc result with daily pct_chg: %s", e)

    def get_last(self) -> Dict[str, Any]:
        """Return the last calc summary (or empty dict if nothing cached)."""
        data = get_cached_json(REDIS_KEY_LAST)
        return data or {}

    def get_all(self) -> Dict[str, Any]:
        """Return the full per-stock result for the latest cached calc."""
        summary = get_cached_json(REDIS_KEY_LAST)
        if not summary:
            return {"success": False, "error": "no cached calc yet"}
        end_date = summary.get("end_date")
        if not end_date:
            return {"success": False, "error": "cached summary missing end_date"}
        result = get_cached_json(f"{REDIS_KEY_RESULT_PREFIX}:{end_date}")
        if not result:
            return {
                "success": False,
                "error": f"result key missing for end_date={end_date}",
            }
        return {"success": True, "data": result}

    def get_by_ts_code(self, ts_code: str) -> Dict[str, Any]:
        """Return one stock's indicators from the latest cached calc."""
        all_resp = self.get_all()
        if not all_resp.get("success"):
            return all_resp
        stocks = all_resp["data"].get("stocks", {})
        if ts_code not in stocks:
            return {"success": False, "error": f"{ts_code} not in watchlist cache"}
        return {"success": True, "data": stocks[ts_code]}

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_latest_trade_date(self) -> Optional[date]:
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT MAX(cal_date) "
                    "FROM trade_cal "
                    "WHERE is_open = 1 AND cal_date <= CURRENT_DATE"
                )
            ).fetchone()
            return row[0] if row else None

    def _get_all_watchlist_codes(self) -> List[str]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT DISTINCT ts_code FROM watchlist_stocks "
                    "WHERE ts_code IS NOT NULL AND ts_code != '' "
                    "ORDER BY ts_code"
                )
            ).fetchall()
            return [r[0] for r in rows]

    def _run_screener(
        self, ind_key: str, info: Dict[str, Any], end_date: date
    ) -> Tuple[bool, str]:
        """Invoke one stock-cli screener in watchlist+save mode."""
        cmd: List[str] = [
            "stock-cli",
            info["cli_name"],
            "--save",
            "--date",
            str(end_date),
        ]
        if info["needs_watchlist_flag"]:
            cmd.append("--watchlist")

        executable = shutil.which("stock-cli")
        if executable:
            cmd[0] = executable

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.settings.worker_batch_timeout,
                cwd=self.settings.worker_work_dir,
            )
        except subprocess.TimeoutExpired:
            return False, f"timeout ({self.settings.worker_batch_timeout}s)"
        except FileNotFoundError:
            return False, "stock-cli not found in PATH"
        except Exception as e:
            return False, f"subprocess error: {e}"

        if result.returncode != 0:
            err_tail = (result.stderr or "")[-300:].strip()
            return False, f"rc={result.returncode}: {err_tail or 'no stderr'}"

        return True, "ok"

    def _read_signals(
        self, end_date: date, ts_codes: List[str]
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Read m_signals for the given date and group by indicator key.

        Returns: {indicator_key: {ts_code: signal_dict}}
        """
        out: Dict[str, Dict[str, Dict[str, Any]]] = {k: {} for k in INDICATORS}
        if not ts_codes:
            return out

        stmt = text(
            """
            SELECT ts_code, signal_type, current_price, indicators,
                   signal_strength, signal_date
            FROM m_signals
            WHERE signal_date = :end_date
              AND is_active = TRUE
              AND ts_code IN :ts_codes
            """
        ).bindparams(bindparam("ts_codes", expanding=True))

        sig_type_to_key = {
            info["signal_type"]: key for key, info in INDICATORS.items()
        }

        with self.engine.connect() as conn:
            rows = conn.execute(
                stmt, {"end_date": end_date, "ts_codes": ts_codes}
            ).fetchall()

        for row in rows:
            ind_key = sig_type_to_key.get(row.signal_type)
            if not ind_key:
                continue  # not one of the three we care about
            indicators_field = row.indicators
            if isinstance(indicators_field, str):
                try:
                    indicators_field = json.loads(indicators_field)
                except (json.JSONDecodeError, TypeError):
                    indicators_field = {}
            elif indicators_field is None:
                indicators_field = {}

            out[ind_key][row.ts_code] = {
                "passed": True,
                "score": float(indicators_field.get("score", 0) or 0),
                "details": indicators_field,
                "current_price": (
                    float(row.current_price) if row.current_price is not None else None
                ),
                "signal_strength": row.signal_strength,
            }

        return out
