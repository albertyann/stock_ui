import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import AsyncSessionLocal
from sqlalchemy import text


async def create_tags_table():
    async with AsyncSessionLocal() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS tags (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)
        """))

        await session.commit()
        print("Tags table created successfully")


if __name__ == "__main__":
    asyncio.run(create_tags_table())
