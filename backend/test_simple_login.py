#!/usr/bin/env python3
"""
Test simple login endpoint
"""

import asyncio
import httpx
import json

async def test_simple_login():
    """Test simple login endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            # Test simple login
            print("Testing /auth/simple-login endpoint...")
            response = await client.post(
                "http://127.0.0.1:8000/auth/simple-login",
                json={"username": "admin", "password": "admin123"}
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    asyncio.run(test_simple_login())
