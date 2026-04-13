#!/usr/bin/env python3
"""
Migration script to add 'added_date' field to existing watchlist_stocks table
Populates added_date from existing added_at timestamps
"""

import asyncio
import asyncpg
import sys

DATABASE_URL = "postgres://postgres:postgrespw@localhost:55000/stock_data"


async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print(
            "Starting migration: Adding 'added_date' field to watchlist_stocks table..."
        )

        # Check if column already exists
        column_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'watchlist_stocks' 
                AND column_name = 'added_date'
            )
        """)

        if column_exists:
            print("Column 'added_date' already exists. Updating existing records...")
        else:
            # Add the column
            await conn.execute("""
                ALTER TABLE watchlist_stocks 
                ADD COLUMN IF NOT EXISTS added_date VARCHAR(10)
            """)
            print("✅ Column 'added_date' added successfully")

        # Update existing records to populate added_date from added_at
        result = await conn.execute("""
            UPDATE watchlist_stocks
            SET added_date = TO_CHAR(added_at, 'YYYY-MM-DD')
            WHERE added_date IS NULL AND added_at IS NOT NULL
        """)

        print(f"✅ Updated {result.split()[-2]} existing records")

        # Create index on added_date for better search performance
        index_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM pg_indexes 
                WHERE tablename = 'watchlist_stocks' 
                AND indexname = 'idx_watchlist_stocks_added_date'
            )
        """)

        if not index_exists:
            await conn.execute("""
                CREATE INDEX idx_watchlist_stocks_added_date 
                ON watchlist_stocks(added_date)
            """)
            print("✅ Index on 'added_date' created successfully")
        else:
            print("Index on 'added_date' already exists")

        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
