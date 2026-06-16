import asyncio
import json
import shutil
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import select, desc, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import SyncTask, SyncTaskLog


class SyncTaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_tasks(self) -> List[Dict]:
        result = await self.session.execute(
            select(SyncTask).order_by(SyncTask.sort_order, SyncTask.id)
        )
        tasks = result.scalars().all()
        return [self._task_to_dict(t) for t in tasks]

    async def get_task(self, task_id: int) -> Optional[Dict]:
        result = await self.session.execute(
            select(SyncTask).where(SyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        return self._task_to_dict(task) if task else None

    async def create_task(self, data: Dict) -> Dict:
        task = SyncTask(
            name=data.get("name"),
            command=data.get("command", "stock-sync"),
            sub_command=data.get("sub_command", "run"),
            task_type=data.get("task_type"),
            params=data.get("params", {}),
            description=data.get("description"),
            sort_order=data.get("sort_order", 0),
            is_active=data.get("is_active", True),
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return self._task_to_dict(task)

    async def update_task(self, task_id: int, data: Dict) -> Optional[Dict]:
        result = await self.session.execute(
            select(SyncTask).where(SyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            return None

        for field in [
            "name",
            "command",
            "sub_command",
            "task_type",
            "params",
            "description",
            "sort_order",
            "is_active",
        ]:
            if field in data:
                setattr(task, field, data[field])

        await self.session.commit()
        await self.session.refresh(task)
        return self._task_to_dict(task)

    async def delete_task(self, task_id: int) -> bool:
        result = await self.session.execute(
            select(SyncTask).where(SyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            return False

        await self.session.delete(task)
        await self.session.commit()
        return True

    async def execute_task(
        self, task_id: int, runtime_params: Optional[Dict] = None
    ) -> Dict:
        result = await self.session.execute(
            select(SyncTask).where(SyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            return {"success": False, "error": "Task not found"}

        settings = get_settings()

        cmd_parts = [task.command]

        if task.sub_command == "run" and task.task_type:
            cmd_parts.append(task.task_type)
        elif task.sub_command:
            cmd_parts.append(task.sub_command)

        params = dict(task.params or {})
        if runtime_params:
            params.update(runtime_params)

        for key, value in params.items():
            if value is None or value == "":
                continue
            if key in ("days", "date", "start_date", "end_date"):
                if key == "date":
                    cmd_parts.append(f"--date")
                elif key == "start_date":
                    cmd_parts.append(f"--start-date")
                elif key == "end_date":
                    cmd_parts.append(f"--end-date")
                else:
                    cmd_parts.append(f"--{key}")
                cmd_parts.append(str(value))
            elif isinstance(value, bool):
                if value:
                    cmd_parts.append(f"--{key}")
            else:
                cmd_parts.append(f"--{key}")
                cmd_parts.append(str(value))

        cmd_str = " ".join(cmd_parts)

        executable = shutil.which(task.command)
        if executable:
            cmd_parts[0] = executable

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=settings.stock_sync_work_dir,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)

            task.last_run_at = datetime.now(timezone.utc)
            await self.session.commit()

            return {
                "success": process.returncode == 0,
                "command": cmd_str,
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
        except asyncio.TimeoutError:
            try:
                process.kill()
                await process.wait()
            except Exception:
                pass
            task.last_run_at = datetime.now(timezone.utc)
            await self.session.commit()
            return {
                "success": False,
                "error": "Task execution timed out after 600 seconds",
                "command": cmd_str,
            }
        except Exception as e:
            task.last_run_at = datetime.now(timezone.utc)
            await self.session.commit()
            return {
                "success": False,
                "error": str(e),
                "command": cmd_str,
            }

    async def get_logs(
        self,
        task_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict:
        query = select(SyncTaskLog).order_by(desc(SyncTaskLog.id))
        count_query = select(sa_func.count(SyncTaskLog.id))

        if task_name:
            query = query.where(SyncTaskLog.task_name == task_name)
            count_query = count_query.where(SyncTaskLog.task_name == task_name)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        logs = result.scalars().all()

        return {
            "items": [self._log_to_dict(log) for log in logs],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    async def get_available_task_types() -> Dict:
        """Get all available sync task types by running 'stock-sync ls --json'."""
        settings = get_settings()

        executable = shutil.which("stock-sync")
        if not executable:
            return {"success": False, "error": "stock-sync command not found"}

        cmd_parts = [
            executable,
            "-c",
            settings.stock_sync_config_path,
            "ls",
            "--json",
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=settings.stock_sync_work_dir,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)

            if process.returncode != 0:
                return {
                    "success": False,
                    "error": stderr.decode("utf-8", errors="replace").strip()
                    or f"stock-sync ls exited with code {process.returncode}",
                }

            tasks = json.loads(stdout.decode("utf-8", errors="replace"))
            return {"success": True, "data": tasks}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Timeout retrieving available tasks"}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Failed to parse task list: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _log_to_dict(self, log: SyncTaskLog) -> Dict:
        return {
            "id": log.id,
            "task_name": log.task_name,
            "task_type": log.task_type,
            "status": log.status,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            "duration_seconds": float(log.duration_seconds) if log.duration_seconds else None,
            "records_processed": log.records_processed or 0,
            "records_inserted": log.records_inserted or 0,
            "records_updated": log.records_updated or 0,
            "error_message": log.error_message,
            "stack_trace": log.stack_trace,
            "retry_count": log.retry_count or 0,
            "trigger_type": log.trigger_type,
            "triggered_by": log.triggered_by,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }

    def _task_to_dict(self, task: SyncTask) -> Dict:
        return {
            "id": task.id,
            "name": task.name,
            "command": task.command,
            "sub_command": task.sub_command,
            "task_type": task.task_type,
            "params": task.params or {},
            "description": task.description,
            "sort_order": task.sort_order,
            "is_active": task.is_active,
            "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }
