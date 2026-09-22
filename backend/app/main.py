from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

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
    ai_chat,
    indicator_calc,
    stock_eval,
    screening,
    index_sync_config,
)
from app.auth.router import router as auth_router
from app.market.middleware import MarketMiddleware
from app.tasks.scheduler import task_manager
from app.websockets.routes import router as ws_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.debug and not settings.jwt_secret_key:
        raise RuntimeError(
            "JWT_SECRET_KEY 未配置：生产环境必须在 .env 中设置强随机值，"
            "或临时设置 DEBUG=True 跳过本检查。"
        )

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

app.add_middleware(MarketMiddleware)

api_prefix = settings.api_v1_prefix
app.include_router(auth_router, prefix=api_prefix)
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
app.include_router(ai_chat.router, prefix=api_prefix)
app.include_router(indicator_calc.router, prefix=api_prefix)
app.include_router(stock_eval.router, prefix=api_prefix)
app.include_router(screening.router, prefix=api_prefix)
app.include_router(index_sync_config.router, prefix=api_prefix)
app.include_router(ws_router)


STATIC_DIR = Path(__file__).parent.parent / "static"


@app.get("/")
async def root():
    if STATIC_DIR.exists():
        return FileResponse(STATIC_DIR / "index.html")
    return {"message": "Stock Watchlist API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/tasks/status")
async def get_task_status():
    return {"success": True, "data": task_manager.get_status()}


# SPA fallback: only active when the built frontend was copied to /app/static
# (Docker image), so local dev without a build keeps working. Registered last
# so API and WebSocket routes take precedence; api/ws misses stay 404.
STATIC_DIR = Path(__file__).parent.parent / "static"

if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith(("api", "ws")):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(STATIC_DIR / "index.html")
