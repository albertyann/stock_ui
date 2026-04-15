import asyncio
import shutil
from typing import Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import SyncTask


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
        if settings.stock_sync_config_path:
            cmd_parts.extend(["-c", settings.stock_sync_config_path])
        if task.sub_command:
            cmd_parts.append(task.sub_command)

        cmd_parts.extend(["--task", task.task_type])

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
            return {
                "success": False,
                "error": "Task execution timed out after 600 seconds",
                "command": cmd_str,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": cmd_str,
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
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }
