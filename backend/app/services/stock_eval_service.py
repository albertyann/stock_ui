"""Stock Evaluation Service.

Evaluates a single stock using the worker's RSI strong scoring engine
via subprocess, caching the result in Redis for frontend consumption.

Flow:
    1. Frontend triggers evaluation via POST /api/v1/stocks/{ts_code}/evaluate
    2. This service calls worker/evaluate_stock.py via subprocess
    3. Results are stored in Redis keyed by `stock:eval:{ts_code}`
    4. Frontend polls via GET /api/v1/stocks/{ts_code}/evaluate-scores
"""

import json
import logging
import shutil
import subprocess
from datetime import date, datetime
from typing import Optional

from app.config import get_settings
from app.redis_client import cache_json, get_cached_json

logger = logging.getLogger(__name__)

REDIS_KEY_PREFIX = "stock:eval"

# TTL: 7 days — enough for weekly review; stale data is fine since evaluation
# is manual-trigger-only and the user controls when to re-run.
EVAL_CACHE_TTL = 7 * 24 * 3600


class StockEvalService:
    """Stock evaluation service with Redis caching."""

    def __init__(self) -> None:
        self.settings = get_settings()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, ts_code: str, eval_date: Optional[date] = None) -> dict:
        """Trigger evaluation for a single stock.

        Calls worker/evaluate_stock.py via subprocess, caches in Redis.
        """
        eval_date_str = str(eval_date or date.today())

        result = self._run_worker(ts_code, eval_date_str)
        if not result.get("success"):
            return result

        # Cache the full result in Redis
        redis_key = f"{REDIS_KEY_PREFIX}:{ts_code}"
        cache_json(redis_key, result, ttl=EVAL_CACHE_TTL)

        return result

    def get_eval_scores(self, ts_code: str) -> dict:
        """Return cached evaluation scores for a stock, if any."""
        redis_key = f"{REDIS_KEY_PREFIX}:{ts_code}"
        cached = get_cached_json(redis_key)
        if cached is None:
            return {"success": False, "error": "No cached evaluation data"}
        return {"success": True, "data": cached}

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _run_worker(self, ts_code: str, eval_date: str) -> dict:
        """Run worker/evaluate_stock.py subprocess and return parsed JSON."""
        script_path = f"{self.settings.worker_work_dir}/evaluate_stock.py"

        cmd = [
            "python3",
            script_path,
            "--ts-code",
            ts_code,
            "--date",
            eval_date,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.settings.worker_timeout * 10,  # evaluation needs more time
                cwd=self.settings.worker_work_dir,
            )
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Evaluation timeout ({self.settings.worker_timeout * 10}s)"}
        except FileNotFoundError:
            return {"success": False, "error": "evaluate_stock.py not found"}
        except Exception as e:
            return {"success": False, "error": f"Subprocess error: {e}"}

        if result.returncode != 0:
            err_tail = (result.stderr or "")[-500:]
            return {"success": False, "error": f"Worker failed (rc={result.returncode}): {err_tail}"}

        stdout = (result.stdout or "").strip()
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON from worker: {e}. Output: {stdout[:200]}"}
