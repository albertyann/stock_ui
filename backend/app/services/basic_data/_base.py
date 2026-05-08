from sqlalchemy import create_engine
from app.config import get_settings


class BasicDataServiceBase:


    def __init__(self):
        self.settings = get_settings()
        self.sync_url = self.settings.database_url.replace("+asyncpg", "")
        self.engine = create_engine(self.sync_url)
