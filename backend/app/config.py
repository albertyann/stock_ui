from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Stock Watchlist API"
    debug: bool = True
    database_url: str = (
        "postgresql+asyncpg://postgres:postgrespw@localhost:55000/stock_data"
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
        "/Users/yann/workspace/trading/sync/configs/sync_config.yaml"
    )
    stock_sync_work_dir: str = "/Users/yann/workspace/trading/sync"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
