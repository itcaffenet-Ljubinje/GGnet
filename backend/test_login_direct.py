"""Test login endpoint directly"""
import requests
import json

# Test with localhost:8000
BASE_URL = "http://localhost:8000"

def test_login():
    """Test login endpoint"""
    
    url = f"{BASE_URL}/api/v1/auth/login"
    
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
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n[OK] Login successful!")
            print(f"Access Token (first 50 chars): {data.get('access_token', '')[:50]}...")
            print(f"Token Type: {data.get('token_type')}")
        else:
            print(f"\n[FAIL] Login failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                pass
                
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to backend!")
        print("Make sure backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_login()

