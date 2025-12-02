#!/usr/bin/env python3
"""
Quick database status check
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_database_status():
    """Quick database status check"""
    
    print("=== DATABASE STATUS CHECK ===")
    
    # Check SQLite
    print("\n1. SQLite Database:")
    try:
        engine = create_async_engine("sqlite+aiosqlite:///./backend/ggnet.db", echo=False)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"   [OK] SQLite connected - {user_count} users")
        await engine.dispose()
    except Exception as e:
        print(f"   [ERROR] SQLite: {e}")
    
    # Check PostgreSQL
    print("\n2. PostgreSQL Database:")
    try:
        engine = create_async_engine("postgresql+asyncpg://ggnet:ggnet_password@localhost:5432/ggnet", echo=False)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"   [OK] PostgreSQL connected - {user_count} users")
        await engine.dispose()
    except Exception as e:
        print(f"   [ERROR] PostgreSQL: {e}")
    
    # Check file existence
    print("\n3. Database Files:")
    sqlite_file = "./backend/ggnet.db"
    if os.path.exists(sqlite_file):
        size = os.path.getsize(sqlite_file)
        print(f"   [OK] SQLite file exists: {sqlite_file} ({size} bytes)")
    else:
        print(f"   [MISSING] SQLite file: {sqlite_file}")

if __name__ == "__main__":
    asyncio.run(check_database_status())
