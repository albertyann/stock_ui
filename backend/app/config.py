from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Stock Watchlist API"
    debug: bool = True
    database_url: str = (
        "postgresql+asyncpg://postgres:postgrespwd@localhost:5432/stock_data"
    )
    api_v1_prefix: str = "/api/v1"
    cors_origins: list = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ]
    data_sync_interval: int = 300
    signal_analysis_interval: int = 600
    tushare_token: str = ""
    stock_sync_config_path: str = (
        "/Users/yann/workspace/trade/sync/configs/sync_config.yaml"
    )
    stock_sync_work_dir: str = "/Users/yann/workspace/trade/sync"
    worker_work_dir: str = "/Users/yann/workspace/trade/worker"
    worker_timeout: int = 15
    worker_batch_timeout: int = 180

    redis_url: str = "redis://localhost:6379/0"

    ai_api_key: str = ""
    ai_model: str = "deepseek-v4-flash"
    ai_base_url: str = "https://api.deepseek.com"
    ai_timeout: int = 120

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
