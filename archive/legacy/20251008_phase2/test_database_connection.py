#!/usr/bin/env python3
"""
Test database connection and verify tables
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.core.database import Base, get_db
from app.models.user import User, UserRole, UserStatus
from app.models.image import Image, ImageFormat, ImageStatus, ImageType
from app.models.machine import Machine, MachineStatus
from app.models.target import Target, TargetStatus
from app.models.session import Session, SessionStatus
from app.models.audit import AuditLog, AuditAction, AuditSeverity

async def test_database_connection():
    """Test database connection and verify all components"""
    
    print("=== DATABASE CONNECTION TEST ===")
    
    # Test both SQLite and PostgreSQL connections
    connections = [
        {
            "name": "SQLite (Default)",
            "url": "sqlite+aiosqlite:///./backend/ggnet.db",
            "sync_url": "sqlite:///./backend/ggnet.db"
        },
        {
            "name": "PostgreSQL (Production)",
            "url": "postgresql+asyncpg://ggnet:ggnet_password@localhost:5432/ggnet",
            "sync_url": "postgresql://ggnet:ggnet_password@localhost:5432/ggnet"
        }
    ]
    
    for conn_info in connections:
        print(f"\n--- Testing {conn_info['name']} ---")
        
        try:
            # Create async engine
            engine = create_async_engine(conn_info["url"], echo=False)
            AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
            
            # Test basic connection
            print("1. Testing basic connection...")
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                print(f"   Connection test: {test_value}")
            
            # Test database info
            print("2. Getting database information...")
            async with engine.begin() as conn:
                if "sqlite" in conn_info["url"]:
                    result = await conn.execute(text("SELECT sqlite_version() as version"))
                    version = result.scalar()
                    print(f"   SQLite version: {version}")
                else:
                    result = await conn.execute(text("SELECT version() as version"))
                    version = result.scalar()
                    print(f"   PostgreSQL version: {version[:50]}...")
            
            # Test table existence
            print("3. Checking table existence...")
            async with engine.begin() as conn:
                if "sqlite" in conn_info["url"]:
                    result = await conn.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                        ORDER BY name
                    """))
                else:
                    result = await conn.execute(text("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY tablename
                    """))
                
                tables = [row[0] for row in result.fetchall()]
                print(f"   Found tables: {tables}")
                
                expected_tables = ['users', 'images', 'machines', 'targets', 'sessions', 'audit_logs']
                missing_tables = [table for table in expected_tables if table not in tables]
                
                if missing_tables:
                    print(f"   [WARNING] Missing tables: {missing_tables}")
                else:
                    print("   [OK] All expected tables exist")
            
            # Test user table
            print("4. Testing user table...")
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
                print(f"   Found {len(users)} users")
                
                for user in users:
                    print(f"   - {user.username} ({user.role}) - Active: {user.is_active}")
            
            # Test admin user specifically
            print("5. Testing admin user...")
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User).where(User.username == 'admin'))
                admin_user = result.scalar_one_or_none()
                
                if admin_user:
                    print(f"   [OK] Admin user found: {admin_user.username}")
                    print(f"   - ID: {admin_user.id}")
                    print(f"   - Email: {admin_user.email}")
                    print(f"   - Role: {admin_user.role}")
                    print(f"   - Status: {admin_user.status}")
                    print(f"   - Active: {admin_user.is_active}")
                    print(f"   - Created: {admin_user.created_at}")
                else:
                    print("   [ERROR] Admin user not found!")
            
            # Test other tables
            print("6. Testing other tables...")
            async with AsyncSessionLocal() as session:
                # Images
                result = await session.execute(select(Image))
                images = result.scalars().all()
                print(f"   Images: {len(images)} records")
                
                # Machines
                result = await session.execute(select(Machine))
                machines = result.scalars().all()
                print(f"   Machines: {len(machines)} records")
                
                # Targets
                result = await session.execute(select(Target))
                targets = result.scalars().all()
                print(f"   Targets: {len(targets)} records")
                
                # Sessions
                result = await session.execute(select(Session))
                sessions = result.scalars().all()
                print(f"   Sessions: {len(sessions)} records")
                
                # Audit logs
                result = await session.execute(select(AuditLog))
                audit_logs = result.scalars().all()
                print(f"   Audit logs: {len(audit_logs)} records")
            
            print(f"   [SUCCESS] {conn_info['name']} connection working!")
            
        except Exception as e:
            print(f"   [ERROR] {conn_info['name']} connection failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            if 'engine' in locals():
                await engine.dispose()

async def test_app_database_connection():
    """Test database connection through app's get_db dependency"""
    
    print("\n=== APP DATABASE CONNECTION TEST ===")
    
    try:
        # Test the app's database dependency
        async for db in get_db():
            print("1. Testing app database dependency...")
            
            # Test basic query
            result = await db.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            print(f"   App DB test: {test_value}")
            
            # Test user query
            result = await db.execute(select(User).where(User.username == 'admin'))
            admin_user = result.scalar_one_or_none()
            
            if admin_user:
                print(f"   [OK] App can access admin user: {admin_user.username}")
            else:
                print("   [ERROR] App cannot access admin user")
            
            break  # Only test once
        
        print("   [SUCCESS] App database connection working!")
        
    except Exception as e:
        print(f"   [ERROR] App database connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_connection())
    asyncio.run(test_app_database_connection())
