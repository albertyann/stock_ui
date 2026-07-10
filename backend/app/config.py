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

    # 生产环境必须在 .env 中显式设置 JWT_SECRET_KEY 为强随机值（≥32 字节），
    # 否则任何人都能伪造登录态。debug=False 时应在入口处拒绝启动（P1 实现）。
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 天
    refresh_token_expire_days: int = 7
    # dev (HTTP) 用 False；prod (HTTPS) 必须 True，否则 cookie 可被中间人嗅探
    cookie_secure: bool = False
    cookie_domain: str = ""
    invitation_expire_hours: int = 24 * 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
