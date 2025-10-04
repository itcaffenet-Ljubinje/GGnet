#!/usr/bin/env python3
"""
Change admin user password - Linux version
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.user import User
from app.core.security import get_password_hash

async def change_password(new_password=None):
    """Change admin user password"""
    
    # Get new password from argument or user input
    if not new_password:
        try:
            new_password = input("Enter new password for admin user: ").strip()
        except EOFError:
            print("Usage: python3 change_password_linux.py <new_password>")
            return
    
    if not new_password:
        print("Password cannot be empty!")
        return
    
    if len(new_password) < 6:
        print("Password must be at least 6 characters long!")
        return
    
    # Use main database - Linux path
    db_path = os.path.join(os.path.dirname(__file__), 'backend', 'ggnet.db')
    engine = create_async_engine(f'sqlite+aiosqlite:///{db_path}')
    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Find admin user
        result = await session.execute(select(User).where(User.username == 'admin'))
        user = result.scalar_one_or_none()
        
        if user:
            print(f'Found admin user: {user.username}')
            
            # Change password
            user.hashed_password = get_password_hash(new_password)
            user.is_active = True
            user.status = 'active'
            user.failed_login_attempts = 0
            user.locked_until = None
            
            await session.commit()
            print(f'Password changed successfully!')
            print(f'New credentials:')
            print(f'  Username: admin')
            print(f'  Password: {new_password}')
        else:
            print('Admin user not found!')
    
    await engine.dispose()

if __name__ == "__main__":
    # Get password from command line argument
    new_password = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(change_password(new_password))
