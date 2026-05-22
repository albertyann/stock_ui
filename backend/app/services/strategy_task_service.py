import asyncio
import json
import logging
import re
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


@dataclass
class StrategyTask:
    task_id: str
    strategy: str
    command: str
    status: str
    created_at: datetime
    updated_at: datetime
    stdout: str = ""
    stderr: str = ""
    returncode: Optional[int] = None
    parsed_data: Optional[dict | list] = None
    error: Optional[str] = None
    process: Optional[asyncio.subprocess.Process] = None


class StrategyTaskManager:
    def __init__(self):
        self._tasks: dict[str, StrategyTask] = {}

    def submit(self, strategy: str, cmd_parts: list[str]) -> str:
        task_id = str(uuid.uuid4())[:8]
        cmd_str = " ".join(cmd_parts)
        task = StrategyTask(
            task_id=task_id,
            strategy=strategy,
            command=cmd_str,
            status=STATUS_PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self._tasks[task_id] = task
        asyncio.create_task(self._run_task(task_id, cmd_parts))
        logger.info(f"Strategy task submitted: {task_id} ({strategy})")
        return task_id

    async def _run_task(self, task_id: str, cmd_parts: list[str]):
        task = self._tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found, skip execution")
            return

        task.status = STATUS_RUNNING
        task.updated_at = datetime.now()
        logger.info(f"Strategy task started: {task_id}")

        settings = get_settings()
        executable = shutil.which("stock-cli")
        if executable:
            cmd_parts[0] = executable

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=settings.stock_sync_work_dir,
            )
            task.process = process
            stdout, stderr = await process.communicate()

            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            task.stdout = stdout_text
            task.stderr = stderr_text
            task.returncode = process.returncode
            task.parsed_data = self._try_parse_json(stdout_text)
            if task.parsed_data is None:
                table_data = self._parse_stdout_table(stdout_text)
                if table_data:
                    task.parsed_data = table_data

            if process.returncode == 0:
                task.status = STATUS_COMPLETED
                logger.info(f"Strategy task completed: {task_id}")
            else:
                task.status = STATUS_FAILED
                task.error = f"Exit code: {process.returncode}"
                logger.error(
                    f"Strategy task failed: {task_id}, "
                    f"returncode={process.returncode}, stderr={stderr_text[:200]}"
                )

        except Exception as e:
            logger.error(f"Strategy task exception: {task_id}, error={e}")
            task.status = STATUS_FAILED
            task.error = str(e)

        task.updated_at = datetime.now()
        task.process = None

    def _try_parse_json(self, text: str) -> Optional[dict]:
        try:
            for line in text.strip().split("\n"):
                stripped = line.strip()
                if stripped and (stripped.startswith("[") or stripped.startswith("{")):
                    return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    def _parse_stdout_table(self, text: str) -> Optional[list[dict]]:
        lines = text.strip().split("\n")
        stocks = []
        ts_code_pattern = re.compile(r"^\s*(\d+)\s+([0-9]{6}\.[A-Z]{2,3})\s+(.*)$")
        header_keywords = ["排名", "序号", "代码", "策略", "股票"]

        for line in lines:
            line = line.strip()
            if not line or line.startswith("=") or line.startswith("-"):
                continue
            if any(kw in line for kw in header_keywords) and not ts_code_pattern.match(line):
                continue

            match = ts_code_pattern.match(line)
            if not match:
                continue

            rank, ts_code, rest = match.groups()
            fields = [f.strip() for f in re.split(r"\s{2,}", rest.strip()) if f.strip()]

            stock = {"ts_code": ts_code, "rank": int(rank)}
            if fields:
                stock["name"] = fields[0]

            for i, field_val in enumerate(fields[1:], start=1):
                clean_val = field_val.replace("%", "").replace("+", "")
                if i == 1:
                    try:
                        stock["score"] = float(clean_val)
                    except ValueError:
                        stock["strategies"] = field_val
                elif i == 2:
                    try:
                        stock["close"] = float(clean_val)
                    except ValueError:
                        pass
                elif i == 3:
                    try:
                        stock["pct_chg"] = float(clean_val)
                    except ValueError:
                        pass
                else:
                    try:
                        val = float(clean_val)
                        if 0 < val < 100:
                            if "rsi" not in stock:
                                stock["rsi12"] = val
                            elif "min_rsi" not in stock:
                                stock["min_rsi"] = val
                            elif "max_rsi" not in stock:
                                stock["max_rsi"] = val
                            elif "avg_rsi" not in stock:
                                stock["avg_rsi"] = val
                    except ValueError:
                        pass

            stocks.append(stock)

        return stocks if stocks else None

    def get_task(self, task_id: str) -> Optional[StrategyTask]:
        return self._tasks.get(task_id)

    def list_tasks(
        self, status_filter: Optional[str] = None, limit: int = 50
    ) -> list[dict]:
        tasks = list(self._tasks.values())
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        tasks = sorted(tasks, key=lambda t: t.created_at, reverse=True)[:limit]

        return [
            {
                "task_id": t.task_id,
                "strategy": t.strategy,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
                "has_result": t.status in (STATUS_COMPLETED, STATUS_FAILED),
            }
            for t in tasks
        ]

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
        to_remove = [
            tid
            for tid, t in self._tasks.items()
            if t.status in (STATUS_COMPLETED, STATUS_FAILED) and t.updated_at < cutoff
        ]
        for tid in to_remove:
            del self._tasks[tid]
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} expired tasks")


strategy_task_manager = StrategyTaskManager()
