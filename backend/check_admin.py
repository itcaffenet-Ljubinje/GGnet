#!/usr/bin/env python3
"""
Script to check admin user and test login
"""

import asyncio
from app.core.database import async_engine
from app.models.user import User
from app.core.security import verify_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def check_admin_user():
    """Check admin user and test password"""
    async with AsyncSession(async_engine) as session:
        try:
            # Check if admin user exists
            result = await session.execute(select(User).where(User.username == 'admin'))
            user = result.scalar_one_or_none()
            
            if not user:
                print('❌ Admin user not found!')
                return False
            
            print('✅ Admin user found')
            print(f'   Username: {user.username}')
            print(f'   Email: {user.email}')
            print(f'   Role: {user.role}')
            print(f'   Status: {user.status}')
            print(f'   Is Active: {user.is_active}')
            print(f'   Password hash: {user.hashed_password[:30]}...')
            
            # Test password verification
            test_password = 'admin123'
            is_valid = verify_password(test_password, user.hashed_password)
            print(f'   Password verification for "{test_password}": {"✅ Valid" if is_valid else "❌ Invalid"}')
            
            return True
            
        except Exception as e:
            print(f'❌ Error checking admin user: {e}')
            return False

if __name__ == '__main__':
    asyncio.run(check_admin_user())
