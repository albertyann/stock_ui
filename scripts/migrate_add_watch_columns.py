#!/usr/bin/env python3
"""
Migration script: Add watch_date and watch_reason columns to watchlist_stocks table
"""

import asyncio
import asyncpg
import sys

DATABASE_URL = "postgres://postgres:postgrespwd@localhost:5432/stock_data"


async def migrate_database():
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Check if watch_date column exists
        watch_date_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'watchlist_stocks' 
                AND column_name = 'watch_date'
            )
        """)

        if not watch_date_exists:
            print("Adding watch_date column...")
            await conn.execute("""
                ALTER TABLE watchlist_stocks 
                ADD COLUMN watch_date VARCHAR(10)
            """)

            # Create index for watch_date
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_watchlist_stocks_watch_date 
                ON watchlist_stocks(watch_date)
            """)

            # Migrate data from added_date to watch_date if exists
            added_date_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'watchlist_stocks' 
                    AND column_name = 'added_date'
                )
            """)

            if added_date_exists:
                await conn.execute("""
                    UPDATE watchlist_stocks 
                    SET watch_date = added_date 
                    WHERE watch_date IS NULL AND added_date IS NOT NULL
                """)
                print("✅ Data migrated from added_date to watch_date")

            print("✅ watch_date column added")
        else:
            print("✓ watch_date column already exists")

        # Check if watch_reason column exists
        watch_reason_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'watchlist_stocks' 
                AND column_name = 'watch_reason'
            )
        """)

        if not watch_reason_exists:
            print("Adding watch_reason column...")
            await conn.execute("""
                ALTER TABLE watchlist_stocks 
                ADD COLUMN watch_reason VARCHAR(50)
            """)
            print("✅ watch_reason column added")
        else:
            print("✓ watch_reason column already exists")

        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_database())
