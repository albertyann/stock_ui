#!/usr/bin/env python3
"""
Migration script: Add note_content column to signals table
"""

import asyncio
import asyncpg
import sys

DATABASE_URL = "postgres://postgres:postgrespwd@localhost:5432/stock_data"


async def migrate_database():
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        note_content_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'm_signals' 
                AND column_name = 'note_content'
            )
        """)

        if not note_content_exists:
            print("Adding note_content column...")
            await conn.execute("""
                ALTER TABLE m_signals 
                ADD COLUMN note_content TEXT
            """)
            print("✅ note_content column added")
        else:
            print("✓ note_content column already exists")

        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_database())
