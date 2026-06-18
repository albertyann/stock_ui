"""Indicator Calculation router.

Endpoints:
    POST /api/v1/indicator-calc/compute        Trigger batch computation.
    GET  /api/v1/indicator-calc/last           Return last calc summary.
    GET  /api/v1/indicator-calc/all            Return full per-stock cache.
    GET  /api/v1/indicator-calc/{ts_code}      Return one stock's indicators.
"""

from fastapi import APIRouter

from app.services.indicator_calc_service import IndicatorCalcService


router = APIRouter(prefix="/indicator-calc", tags=["indicator-calc"])


@router.post("/compute", response_model=dict)
async def compute_all():
    """Trigger batch computation. Long-running (up to ~3 min).

    Frontend should call via the longRunningApi client (300s timeout).
    """
    service = IndicatorCalcService()
    return service.compute_all()


@router.get("/last", response_model=dict)
async def get_last():
    service = IndicatorCalcService()
    data = service.get_last()
    return {"success": bool(data), "data": data}


@router.get("/all", response_model=dict)
async def get_all():
    service = IndicatorCalcService()
    return service.get_all()


@router.get("/{ts_code}", response_model=dict)
async def get_by_ts_code(ts_code: str):
    service = IndicatorCalcService()
    return service.get_by_ts_code(ts_code)
