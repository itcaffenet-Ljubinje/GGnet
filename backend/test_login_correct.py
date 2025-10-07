"""Test login with correct endpoint"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """Test login endpoint"""
    
    url = f"{BASE_URL}/auth/login"
    
    payload = {
        "username": "admin",
        "password": "admin123"
    }
    
    print(f"Testing login at: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ [SUCCESS] Login successful!")
            print(f"Access Token (first 50 chars): {data.get('access_token', '')[:50]}...")
            print(f"Token Type: {data.get('token_type')}")
            print(f"Expires In: {data.get('expires_in')} seconds")
            return True
        else:
            print(f"\n❌ [FAIL] Login failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                pass
            return False
                
    except requests.exceptions.ConnectionError:
        print("\n❌ [ERROR] Cannot connect to backend!")
        print("Make sure backend is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"\n❌ [ERROR] {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_login()
    exit(0 if success else 1)

