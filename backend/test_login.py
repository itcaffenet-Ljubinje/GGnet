#!/usr/bin/env python3
"""
Script to test login endpoint
"""

import asyncio
import httpx
import json

async def test_login():
    """Test login endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            # Test login data
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            print("Testing login endpoint...")
            print(f"URL: http://127.0.0.1:8000/auth/login")
            print(f"Data: {login_data}")
            
            response = await client.post(
                "http://127.0.0.1:8000/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Login successful!")
                print(f"Access Token: {data.get('access_token', 'N/A')[:50]}...")
                print(f"Refresh Token: {data.get('refresh_token', 'N/A')[:50]}...")
                print(f"Token Type: {data.get('token_type', 'N/A')}")
                print(f"Expires In: {data.get('expires_in', 'N/A')}")
            else:
                print(f"❌ Login failed!")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error testing login: {e}")

if __name__ == '__main__':
    asyncio.run(test_login())
