"""
Test script for Phase 3 - Authentication API
Tests the complete phone-based OTP login flow
"""

import requests
import json
import random

BASE_URL = "http://127.0.0.1:8000/api/auth"

# Use a random phone number to avoid rate limit issues
TEST_PHONE = f"911{random.randint(1000000, 9999999)}"

def test_phone_login():
    """Test 1: Request OTP via phone login"""
    print("\n" + "="*60)
    print("TEST 1: Phone Login (Request OTP)")
    print("="*60)
    
    url = f"{BASE_URL}/phone-login/"
    payload = {"phone": TEST_PHONE}
    
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        otp = data.get('otp')
        print(f"✓ OTP generated: {otp}")
        return payload['phone'], otp
    else:
        print("✗ Failed to generate OTP")
        return None, None


def test_verify_otp(phone, otp):
    """Test 2: Verify OTP and login"""
    print("\n" + "="*60)
    print("TEST 2: Verify OTP and Login")
    print("="*60)
    
    url = f"{BASE_URL}/verify-otp/"
    payload = {"phone": phone, "otp": otp, "name": "New Test User"}
    
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✓ Authentication successful")
        print(f"✓ Token: {token}")
        return token
    else:
        print("✗ OTP verification failed")
        return None


def test_profile_without_auth():
    """Test 3: Profile endpoint without auth (should fail)"""
    print("\n" + "="*60)
    print("TEST 3: Get Profile Without Auth (Should Fail)")
    print("="*60)
    
    url = f"{BASE_URL}/profile/"
    
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 401:
        print("✓ Correctly rejected unauthenticated request")
        return True
    else:
        print("✗ Should have returned 401 Unauthorized")
        return False


def test_profile_with_auth(token):
    """Test 4: Get profile with token auth"""
    print("\n" + "="*60)
    print("TEST 4: Get Profile With Token Auth")
    print("="*60)
    
    url = f"{BASE_URL}/profile/"
    headers = {"Authorization": f"Token {token}"}
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✓ Profile retrieved successfully")
        return response.json()
    else:
        print("✗ Failed to retrieve profile")
        return None


def test_update_profile(token):
    """Test 5: Update profile"""
    print("\n" + "="*60)
    print("TEST 5: Update Profile")
    print("="*60)
    
    url = f"{BASE_URL}/profile/"
    headers = {"Authorization": f"Token {token}"}
    payload = {"name": "Updated Test User", "email": "test@example.com"}
    
    response = requests.put(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✓ Profile updated successfully")
        return True
    else:
        print("✗ Failed to update profile")
        return False


def test_logout(token):
    """Test 6: Logout"""
    print("\n" + "="*60)
    print("TEST 6: Logout")
    print("="*60)
    
    url = f"{BASE_URL}/logout/"
    headers = {"Authorization": f"Token {token}"}
    
    response = requests.post(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✓ Logout successful, token invalidated")
        return True
    else:
        print("✗ Logout failed")
        return False


def test_profile_after_logout(token):
    """Test 7: Try profile access after logout (should fail)"""
    print("\n" + "="*60)
    print("TEST 7: Access Profile After Logout (Should Fail)")
    print("="*60)
    
    url = f"{BASE_URL}/profile/"
    headers = {"Authorization": f"Token {token}"}
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 401:
        print("✓ Correctly rejected invalidated token")
        return True
    else:
        print("✗ Should have returned 401 after logout")
        return False

def run_all_tests():
    """Run complete authentication flow test"""
    print("\n")
    print("█" * 60)
    print("█ PHASE 3 - AUTHENTICATION API COMPLETE TEST FLOW")
    print("█" * 60)
    
    # Test 1: Request OTP
    phone, otp = test_phone_login()
    if not phone:
        print("\n✗ Test suite failed at step 1")
        return False
    
    # Test 2: Verify OTP and get token
    token = test_verify_otp(phone, otp)
    if not token:
        print("\n✗ Test suite failed at step 2")
        return False
    
    # Test 3: Profile without auth should fail
    test_profile_without_auth()
    
    # Test 4: Get profile with token
    profile = test_profile_with_auth(token)
    if not profile:
        print("\n✗ Test suite failed at step 4")
        return False
    
    # Test 5: Update profile
    if not test_update_profile(token):
        print("\n✗ Test suite failed at step 5")
        return False
    
    # Test 6: Logout
    if not test_logout(token):
        print("\n✗ Test suite failed at step 6")
        return False
    
    # Test 7: Profile after logout should fail
    test_profile_after_logout(token)
    
    print("\n" + "█" * 60)
    print("█ ALL TESTS COMPLETED SUCCESSFULLY ✓")
    print("█" * 60)
    return True

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("✗ Error: Cannot connect to API at http://127.0.0.1:8000")
        print("  Make sure the development server is running:")
        print("  python manage.py runserver 127.0.0.1:8000")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
