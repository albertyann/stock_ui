from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.strategy_task_service import strategy_task_manager


router = APIRouter(prefix="/strategies", tags=["strategies"])


SUPPORTED_STRATEGIES = {
    "ma-composite-proximity": {
        "name": "MA复合回踩策略选股器",
        "description": "MA20+MA2560+MA30同时筛选，汇总命中结果",
        "module": "screener.ma_composite_proximity_screener",
        "supports_output": False,
    },
    "rsi12-continuous": {
        "name": "RSI12连续强势策略选股器",
        "description": "RSI12连续5天大于65",
        "module": "screener.rsi12_continuous_screener",
        "supports_output": False,
    },
    "watchlist-continuous-shrink": {
        "name": "Watchlist持续缩量筛选器",
        "description": "连续5日成交量低于5日均量+股价波动<3%",
        "module": "screener.watchlist_continuous_volume_shrink_screener",
        "supports_output": False,
    },
}


class StrategyExecuteRequest(BaseModel):
    strategy: str = Field(..., description="策略名称")
    date: Optional[str] = Field(None, description="指定日期 (YYYY-MM-DD)")
    output: str = Field("json", description="输出格式: console / json / csv / all")
    limit: Optional[int] = Field(None, description="限制处理数量")


@router.get("/list", response_model=dict)
async def list_strategies():
    strategies = [
        {"key": key, "name": value["name"], "description": value["description"]}
        for key, value in SUPPORTED_STRATEGIES.items()
    ]
    return {"success": True, "data": strategies}


@router.post("/execute", response_model=dict)
async def execute_strategy(request: StrategyExecuteRequest):
    if request.strategy not in SUPPORTED_STRATEGIES:
        return {
            "success": False,
            "error": f"不支持的策略: {request.strategy}",
        }

    cmd_parts = ["stock-cli", request.strategy]

    if request.date:
        cmd_parts.extend(["--date", request.date])

    info = SUPPORTED_STRATEGIES[request.strategy]
    if request.output and info.get("supports_output", False):
        cmd_parts.extend(["--output", request.output])

    if request.limit:
        cmd_parts.extend(["--limit", str(request.limit)])

    task_id = strategy_task_manager.submit(request.strategy, cmd_parts)

    return {
        "success": True,
        "task_id": task_id,
        "strategy": request.strategy,
        "strategy_name": info["name"],
        "status": "pending",
        "message": "策略已提交，请通过 /execute/{task_id} 查询状态",
    }


@router.get("/execute/{task_id}", response_model=dict)
async def get_task_status(task_id: str):
    task = strategy_task_manager.get_task(task_id)
    if not task:
        return {"success": False, "error": f"任务不存在: {task_id}"}

    result = {
        "success": True,
        "task_id": task.task_id,
        "strategy": task.strategy,
        "status": task.status,
        "command": task.command,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }

    if task.status in ("completed", "failed"):
        result.update(
            {
                "returncode": task.returncode,
                "stdout": task.stdout,
                "stderr": task.stderr,
                "data": task.parsed_data,
            }
        )
        if task.error:
            result["error"] = task.error

    return result


@router.get("/tasks", response_model=dict)
async def list_strategy_tasks(
    status: Optional[str] = None, limit: int = 50
):
    return {
        "success": True,
        "data": strategy_task_manager.list_tasks(
            status_filter=status, limit=limit
        ),
    }
