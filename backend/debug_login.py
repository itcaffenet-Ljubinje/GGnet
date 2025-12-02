#!/usr/bin/env python3
"""
Script to debug login process step by step
"""

import asyncio
from app.core.database import get_async_engine
from app.models.user import User
from app.core.security import verify_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def debug_login():
    """Debug login process step by step"""
    async_engine = get_async_engine()
    async with AsyncSession(async_engine) as session:
        try:
            username = "admin"
            password = "admin123"
            
            print(f"🔍 Debugging login for username: {username}")
            print(f"🔍 Password to verify: {password}")
            
            # Step 1: Find user
            print("\n1. Looking for user...")
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ User not found!")
                return
            
            print(f"✅ User found: {user.username}")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Role: {user.role}")
            print(f"   Status: {user.status}")
            print(f"   Is Active: {user.is_active}")
            print(f"   Failed Login Attempts: {user.failed_login_attempts}")
            print(f"   Locked Until: {user.locked_until}")
            
            # Step 2: Check if user is active
            print("\n2. Checking if user is active...")
            if not user.is_active:
                print("❌ User is not active!")
                return
            print("✅ User is active")
            
            # Step 3: Check if user is locked
            print("\n3. Checking if user is locked...")
            if user.locked_until:
                print(f"❌ User is locked until: {user.locked_until}")
                return
            print("✅ User is not locked")
            
            # Step 4: Verify password
            print("\n4. Verifying password...")
            print(f"   Stored hash: {user.hashed_password}")
            print(f"   Password to verify: {password}")
            
            is_valid = verify_password(password, user.hashed_password)
            print(f"   Verification result: {'✅ Valid' if is_valid else '❌ Invalid'}")
            
            if not is_valid:
                print("❌ Password verification failed!")
                return
            
            print("✅ Password verification successful!")
            print("\n🎉 All checks passed - login should work!")
            
        except Exception as e:
            print(f"❌ Error during debug: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(debug_login())
