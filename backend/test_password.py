"""Test password verification"""
import asyncio
from sqlalchemy import select
from app.core.database import get_async_engine, AsyncSession
from app.models.user import User
from app.core.security import verify_password

async def test_login():
    """Test login credentials"""
    async_engine = get_async_engine()
    
    async with AsyncSession(async_engine) as session:
        async with session.begin():
            # Get admin user
            result = await session.execute(
                select(User).where(User.username == 'admin')
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print("Admin user not found!")
                return
            
            print(f"User found: {user.username}")
            print(f"Email: {user.email}")
            print(f"Is Active: {user.is_active}")
            print(f"Status: {user.status}")
            print(f"Role: {user.role}")
            print(f"Hashed Password (first 50 chars): {user.hashed_password[:50]}...")
            
            # Test password
            test_password = "admin123"
            print(f"\nTesting password: {test_password}")
            
            is_valid = verify_password(test_password, user.hashed_password)
            print(f"Password valid: {is_valid}")
            
            if is_valid:
                print("\n[OK] Login should work!")
            else:
                print("\n[FAIL] Password verification failed!")
                print("Try recreating the admin user with create_admin.py")

if __name__ == "__main__":
    asyncio.run(test_login())

