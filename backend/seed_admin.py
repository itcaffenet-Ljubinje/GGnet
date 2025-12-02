"""
Script to create default admin user in the database

This is a wrapper that uses the unified create_admin script.
For more options, use: python -m app.scripts.create_admin
"""

import asyncio
from app.scripts.create_admin import create_admin_user


async def seed_admin():
    """Create default admin user if it doesn't exist"""
    await create_admin_user(create_tables=True, update_if_exists=False)


if __name__ == "__main__":
    asyncio.run(seed_admin())



