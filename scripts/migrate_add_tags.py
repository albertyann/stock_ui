#!/usr/bin/env python3
"""
Migration script: Create stock_tags table with GIN index
"""

import asyncio
import asyncpg
import sys

DATABASE_URL = "postgres://postgres:postgrespw@localhost:55000/stock_data"


async def migrate_database():
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Check if stock_tags table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'stock_tags'
            )
        """)

        if not table_exists:
            print("Creating stock_tags table...")
            await conn.execute("""
                CREATE TABLE stock_tags (
                    ts_code VARCHAR(20) PRIMARY KEY,
                    tags JSONB DEFAULT '[]'::jsonb NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            print("✅ stock_tags table created")
        else:
            print("✓ stock_tags table already exists")

        # Check if GIN index exists
        index_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'stock_tags' 
                AND indexname = 'idx_stock_tags_tags'
            )
        """)

        if not index_exists:
            print("Creating GIN index on tags column...")
            await conn.execute("""
                CREATE INDEX idx_stock_tags_tags 
                ON stock_tags USING GIN (tags)
            """)
            print("✅ GIN index created")
        else:
            print("✓ GIN index already exists")

        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_database())
