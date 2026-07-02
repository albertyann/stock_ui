"""Stock Evaluation Router.

Endpoints:
    POST /api/v1/stocks/{ts_code}/evaluate   Trigger evaluation for a stock.
    GET  /api/v1/stocks/{ts_code}/evaluate-scores  Get cached evaluation scores.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from app.services.stock_eval_service import StockEvalService


router = APIRouter(prefix="/stocks", tags=["stock-eval"])


@router.post("/{ts_code}/evaluate", response_model=dict)
async def evaluate_stock(
    ts_code: str,
    date: Optional[date] = Query(None, description="Evaluation date (YYYY-MM-DD), default today"),
):
    """Trigger RSI strong evaluation for a single stock.

    Runs the worker script, caches the result in Redis, and returns scores
    for the last 5 trading days.
    """
    service = StockEvalService()
    return service.evaluate(ts_code, eval_date=date)


@router.get("/{ts_code}/evaluate-scores", response_model=dict)
async def get_eval_scores(ts_code: str):
    """Return cached evaluation scores for a stock, or error if none exist."""
    service = StockEvalService()
    return service.get_eval_scores(ts_code)
