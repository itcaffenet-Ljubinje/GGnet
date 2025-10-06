#!/usr/bin/env python3
"""
Simple test for auth endpoints
"""

import asyncio
import httpx
import json

async def test_simple():
    """Test simple endpoints"""
    try:
        async with httpx.AsyncClient() as client:
            # Test 1: Test endpoint
            print("Testing /auth/test-login endpoint...")
            response = await client.post(
                "http://127.0.0.1:8000/auth/test-login",
                json={"username": "admin", "password": "admin123"}
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Test 2: Login endpoint
            print("\nTesting /auth/login endpoint...")
            response = await client.post(
                "http://127.0.0.1:8000/auth/login",
                json={"username": "admin", "password": "admin123"}
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    asyncio.run(test_simple())
