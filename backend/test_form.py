#!/usr/bin/env python3
"""
Test login with form data
"""

import asyncio
import httpx

async def test_form_login():
    """Test login with form data"""
    try:
        async with httpx.AsyncClient() as client:
            # Test with form data
            print("Testing /auth/login with form data...")
            response = await client.post(
                "http://127.0.0.1:8000/auth/login",
                data={"username": "admin", "password": "admin123"}
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    asyncio.run(test_form_login())
