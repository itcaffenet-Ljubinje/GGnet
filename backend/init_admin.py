#!/usr/bin/env python3
"""Initialize admin user on startup - to be run in Docker container"""
import asyncio
import sys
from sqlalchemy import select
from app.core.database import get_async_engine, AsyncSession
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash

async def init_admin():
    """Create admin user if it doesn't exist"""
    try:
        async_engine = get_async_engine()
        
        async with AsyncSession(async_engine) as session:
            async with session.begin():
                # Check if any admin exists
                result = await session.execute(
                    select(User).where(User.username == 'admin')
                )
                admin_user = result.scalar_one_or_none()
                
                if not admin_user:
                    # Create admin user
                    admin = User(
                        username='admin',
                        email='admin@ggnet.local',
                        full_name='System Administrator',
                        hashed_password=get_password_hash('admin123'),
                        is_active=True,
                        status=UserStatus.ACTIVE,
                        role=UserRole.ADMIN
                    )
                    session.add(admin)
                    await session.flush()
                    print("✓ Admin user created successfully")
                    print("  Username: admin")
                    print("  Password: admin123")
                else:
                    print("✓ Admin user already exists")
                    
    except Exception as e:
        print(f"✗ Error initializing admin user: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(init_admin())

