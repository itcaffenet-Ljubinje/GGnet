#!/usr/bin/env python3
"""
Setup PostgreSQL database and create admin user
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.database import Base  # pyright: ignore[reportMissingImports]
from app.models.user import User, UserRole, UserStatus  # pyright: ignore[reportMissingImports]
from app.core.security import get_password_hash  # pyright: ignore[reportMissingImports]

async def setup_database():
    """Setup PostgreSQL database and create admin user"""
    
    print("=== POSTGRESQL DATABASE SETUP ===")
    
    # PostgreSQL connection parameters
    DB_USER = "ggnet"
    DB_PASS = "ggnet_password"
    DB_NAME = "ggnet"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    
    # PostgreSQL async URL
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print(f"Database URL: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        
        # Test connection
        print("Testing database connection...")
        async with engine.begin() as conn:
            result = await conn.execute(select(1))
            print("Database connection successful!")
        
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
                print("\n[SUCCESS] PostgreSQL database setup completed!")
            else:
                print("[ERROR] Admin user not found after creation!")
                
    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        print("\nMake sure PostgreSQL is running and configured:")
        print("1. sudo systemctl start postgresql")
        print("2. sudo -u postgres psql")
        print("3. CREATE USER ggnet WITH PASSWORD 'ggnet_password';")
        print("4. CREATE DATABASE ggnet OWNER ggnet;")
        print("5. GRANT ALL PRIVILEGES ON DATABASE ggnet TO ggnet;")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_database())
