#!/usr/bin/env python3
"""
Setup database and create admin user for Linux
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.database import Base
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash

async def setup_database():
    """Setup database and create admin user"""
    
    print("=== DATABASE SETUP ===")
    
    # Use main database - Linux path
    db_path = os.path.join(os.path.dirname(__file__), 'backend', 'ggnet.db')
    print(f"Database path: {db_path}")
    
    if not os.path.exists(os.path.dirname(db_path)):
        print(f"Creating directory: {os.path.dirname(db_path)}")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_async_engine(f'sqlite+aiosqlite:///{db_path}')
    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        # Create all tables
        print("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully!")
        
        # Create admin user
        print("Creating admin user...")
        async with AsyncSessionLocal() as session:
            # Check if admin user already exists
            result = await session.execute(select(User).where(User.username == 'admin'))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"Admin user already exists: {existing_user.username}")
                print("Updating password...")
                existing_user.hashed_password = get_password_hash('admin123')
                existing_user.is_active = True
                existing_user.status = UserStatus.ACTIVE
                existing_user.role = UserRole.ADMIN
                await session.commit()
                print("Admin user password updated!")
            else:
                print("Creating new admin user...")
                admin_user = User(
                    username='admin',
                    email='admin@ggnet.local',
                    full_name='System Administrator',
                    hashed_password=get_password_hash('admin123'),
                    is_active=True,
                    status=UserStatus.ACTIVE,
                    role=UserRole.ADMIN
                )
                session.add(admin_user)
                await session.commit()
                print("Admin user created successfully!")
            
            # Verify admin user
            result = await session.execute(select(User).where(User.username == 'admin'))
            admin_user = result.scalar_one_or_none()
            
            if admin_user:
                print("\n=== ADMIN USER DETAILS ===")
                print(f"ID: {admin_user.id}")
                print(f"Username: {admin_user.username}")
                print(f"Email: {admin_user.email}")
                print(f"Full Name: {admin_user.full_name}")
                print(f"Role: {admin_user.role}")
                print(f"Is Active: {admin_user.is_active}")
                print(f"Status: {admin_user.status}")
                print(f"Created At: {admin_user.created_at}")
                
                print("\n=== LOGIN CREDENTIALS ===")
                print("Username: admin")
                print("Password: admin123")
                print("\n[SUCCESS] Database setup completed!")
            else:
                print("[ERROR] Admin user not found after creation!")
                
    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_database())
