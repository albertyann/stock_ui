#!/usr/bin/env python3
"""
Migration script to add 'updated_at' field to watchlist_stocks table.
Populates updated_at from added_at for existing records.
"""

import asyncio
import asyncpg
import sys

DATABASE_URL = "postgres://postgres:postgrespw@localhost:55000/stock_data"


async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print(
            "Starting migration: Adding 'updated_at' field to watchlist_stocks table..."
        )

        # Check if column already exists
        column_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'watchlist_stocks' 
                AND column_name = 'updated_at'
            )
        """)

        if column_exists:
            print("Column 'updated_at' already exists. Updating existing records...")
        else:
            # Add the column with default value
            await conn.execute("""
                ALTER TABLE watchlist_stocks 
                ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE
            """)
            print("✅ Column 'updated_at' added successfully")

        # Populate updated_at from added_at for records where updated_at is NULL
        result = await conn.execute("""
            UPDATE watchlist_stocks
            SET updated_at = added_at
            WHERE updated_at IS NULL AND added_at IS NOT NULL
        """)

        print(f"✅ Updated {result.split()[-2]} existing records")

        # Set NOT NULL and server default for future inserts
        await conn.execute("""
            ALTER TABLE watchlist_stocks 
            ALTER COLUMN updated_at SET DEFAULT NOW()
        """)

        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
