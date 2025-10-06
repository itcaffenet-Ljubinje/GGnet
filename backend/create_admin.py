#!/usr/bin/env python3
"""
Script to create default admin user for GGnet Diskless Server
"""

import asyncio
from app.core.database import async_engine
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def create_admin_user():
    """Create default admin user if it doesn't exist"""
    async with AsyncSession(async_engine) as session:
        try:
            # Check if admin user exists
            result = await session.execute(select(User).where(User.username == 'admin'))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print('✅ Admin user already exists')
                print(f'   Username: {existing_user.username}')
                print(f'   Email: {existing_user.email}')
                print(f'   Role: {existing_user.role}')
                return existing_user
            
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@ggnet.local',
                full_name='System Administrator',
                hashed_password=get_password_hash('admin123'),
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                is_active=True
            )
            
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            print('✅ Admin user created successfully!')
            print('   Username: admin')
            print('   Password: admin123')
            print('   Email: admin@ggnet.local')
            print('   Role: admin')
            print('')
            print('⚠️  IMPORTANT: Change the password after first login!')
            
            return admin_user
            
        except Exception as e:
            print(f'❌ Error creating admin user: {e}')
            await session.rollback()
            raise

if __name__ == '__main__':
    asyncio.run(create_admin_user())
