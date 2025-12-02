"""Create admin user in PostgreSQL database"""
import asyncio
import os
from sqlalchemy import select
from app.core.database import get_async_engine, AsyncSession
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash

# Override database URL to use PostgreSQL
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://ggnet:ggnet_password@localhost:5432/ggnet'

async def create_admin_user():
    """Create or update admin user"""
    async_engine = get_async_engine()
    
    try:
        async with AsyncSession(async_engine) as session:
            async with session.begin():
                # Check if admin exists
                result = await session.execute(
                    select(User).where(User.username == 'admin')
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    print(f"Admin user already exists (ID: {existing_user.id})")
                    print(f"Updating password...")
                    existing_user.hashed_password = get_password_hash('admin123')
                    existing_user.is_active = True
                    existing_user.status = UserStatus.ACTIVE
                    existing_user.role = UserRole.ADMIN
                    await session.flush()
                    print("[OK] Admin password updated!")
                else:
                    # Create new admin user
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
                    await session.refresh(admin)
                    print(f"[OK] Admin user created with ID: {admin.id}")
                
                print("\nCredentials:")
                print("  Username: admin")
                print("  Password: admin123")
                print("\nYou can now log in!")
                
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_admin_user())

