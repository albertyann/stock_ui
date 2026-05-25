from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db
from app.routers import (
    watchlists,
    stocks,
    signals,
    realtime,
    sectors,
    basic_data,
    sync_tasks,
    tags,
    stock_info,
    strategies,
    daily_scores,
)
from app.tasks.scheduler import task_manager
from app.websockets.routes import router as ws_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    from app.events import event_bus, NOTE_CREATED
    from app.services.signal_service import SignalService

    event_bus.subscribe(NOTE_CREATED, SignalService.handle_note_created)

    task_manager.start()
    yield
    task_manager.shutdown()


app = FastAPI(
    title=settings.app_name,
    description="Stock Watchlist Management API with Buy/Sell Signals",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = settings.api_v1_prefix
app.include_router(watchlists.router, prefix=api_prefix)
app.include_router(stocks.router, prefix=api_prefix)
app.include_router(signals.router, prefix=api_prefix)
app.include_router(realtime.router, prefix=api_prefix)
app.include_router(sectors.router, prefix=api_prefix)
app.include_router(basic_data.router, prefix=api_prefix)
app.include_router(sync_tasks.router, prefix=api_prefix)
app.include_router(tags.router, prefix=api_prefix)
app.include_router(stock_info.router, prefix=api_prefix)
app.include_router(strategies.router, prefix=api_prefix)
app.include_router(daily_scores.router, prefix=api_prefix)
app.include_router(ws_router)


@app.get("/")
async def root():
    return {"message": "Stock Watchlist API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/tasks/status")
async def get_task_status():
    return {"success": True, "data": task_manager.get_status()}
