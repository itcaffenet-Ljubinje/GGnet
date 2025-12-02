#!/usr/bin/env python3
"""
Unified Admin User Creation Script for GGnet

This script creates the default admin user for GGnet Diskless Server.
It works with both SQLite and PostgreSQL databases and can be used
standalone or in Docker containers.

Usage:
    python -m app.scripts.create_admin
    # or
    python backend/scripts/create_admin.py

Environment Variables:
    DATABASE_URL: Database connection string (optional, uses config default)
    ADMIN_USERNAME: Admin username (default: admin)
    ADMIN_PASSWORD: Admin password (default: admin123)
    ADMIN_EMAIL: Admin email (default: admin@ggnet.local)
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import async_engine, AsyncSessionLocal, Base
from app.core.config import get_settings
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash

logger = structlog.get_logger(__name__)


async def create_admin_user(
    username: Optional[str] = None,
    password: Optional[str] = None,
    email: Optional[str] = None,
    create_tables: bool = True,
    update_if_exists: bool = False
) -> User:
    """
    Create or update default admin user in the database.
    
    Args:
        username: Admin username (default: 'admin')
        password: Admin password (default: 'admin123')
        email: Admin email (default: 'admin@ggnet.local')
        create_tables: Whether to create database tables if they don't exist
        update_if_exists: Whether to update existing admin user's password
        
    Returns:
        User: The admin user object
        
    Raises:
        Exception: If database operations fail
    """
    # Get settings
    settings = get_settings()
    
    # Get credentials from environment or use defaults
    admin_username = username or os.getenv("ADMIN_USERNAME", "admin")
    admin_password = password or os.getenv("ADMIN_PASSWORD", "admin123")
    admin_email = email or os.getenv("ADMIN_EMAIL", "admin@ggnet.local")
    
    logger.info(
        "Creating admin user",
        username=admin_username,
        email=admin_email,
        database_url=settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
    )
    
    # Create tables if requested and they don't exist
    if create_tables:
        try:
            # Import all models to ensure they're registered
            from app.models import user, image, machine, target, session, audit
            
            # Create tables
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.warning("Could not create tables (may already exist)", error=str(e))
    
    # Create or update admin user
    async with AsyncSessionLocal() as db:
        try:
            # Check if admin user exists
            result = await db.execute(
                select(User).where(User.username == admin_username)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                if update_if_exists:
                    # Update existing user
                    existing_user.hashed_password = get_password_hash(admin_password)
                    existing_user.email = admin_email
                    existing_user.is_active = True
                    existing_user.status = UserStatus.ACTIVE
                    existing_user.role = UserRole.ADMIN
                    
                    await db.commit()
                    await db.refresh(existing_user)
                    
                    logger.info(
                        "Admin user updated",
                        username=admin_username,
                        email=admin_email
                    )
                    
                    print("\n" + "="*60)
                    print("✅ Admin user UPDATED successfully!")
                    print("="*60)
                    print(f"  Username: {admin_username}")
                    print(f"  Email: {admin_email}")
                    print(f"  Role: admin")
                    print(f"  Status: active")
                    print("="*60 + "\n")
                    
                    return existing_user
                else:
                    logger.info(
                        "Admin user already exists",
                        username=admin_username,
                        user_id=existing_user.id
                    )
                    
                    print("\n" + "="*60)
                    print("ℹ️  Admin user already exists")
                    print("="*60)
                    print(f"  Username: {admin_username}")
                    print(f"  Email: {existing_user.email}")
                    print(f"  Role: {existing_user.role}")
                    print(f"  Status: {existing_user.status}")
                    print("="*60)
                    print("\n💡 To update the password, run with --update flag")
                    print("="*60 + "\n")
                    
                    return existing_user
            else:
                # Create new admin user
                admin_user = User(
                    username=admin_username,
                    email=admin_email,
                    full_name="System Administrator",
                    hashed_password=get_password_hash(admin_password),
                    role=UserRole.ADMIN,
                    status=UserStatus.ACTIVE,
                    is_active=True
                )
                
                db.add(admin_user)
                await db.commit()
                await db.refresh(admin_user)
                
                logger.info(
                    "Admin user created",
                    username=admin_username,
                    email=admin_email,
                    user_id=admin_user.id
                )
                
                print("\n" + "="*60)
                print("✅ Admin user created successfully!")
                print("="*60)
                print(f"  Username: {admin_username}")
                print(f"  Password: {admin_password}")
                print(f"  Email: {admin_email}")
                print(f"  Role: admin")
                print(f"  Status: active")
                print("="*60)
                print("\n⚠️  IMPORTANT: Change the password after first login!")
                print("="*60 + "\n")
                
                return admin_user
                
        except Exception as e:
            logger.error(
                "Failed to create admin user",
                error=str(e),
                error_type=type(e).__name__
            )
            await db.rollback()
            raise


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create or update default admin user for GGnet"
    )
    parser.add_argument(
        "--username",
        default=None,
        help="Admin username (default: admin)"
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Admin password (default: admin123)"
    )
    parser.add_argument(
        "--email",
        default=None,
        help="Admin email (default: admin@ggnet.local)"
    )
    parser.add_argument(
        "--no-create-tables",
        action="store_true",
        help="Skip database table creation"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing admin user's password"
    )
    
    args = parser.parse_args()
    
    try:
        await create_admin_user(
            username=args.username,
            password=args.password,
            email=args.email,
            create_tables=not args.no_create_tables,
            update_if_exists=args.update
        )
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}\n", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

