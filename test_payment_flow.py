"""
Phase 4 - Razorpay Payment Integration Test
Tests complete payment flow: create order → verify payment
"""
import requests
import json
import hmac
import hashlib
import random

BASE_URL = 'http://127.0.0.1:8000/api'

# Test data
TEST_PHONE = f"911{random.randint(1000000, 9999999)}"
TEST_USER = {
    'phone': TEST_PHONE,
    'name': 'Payment Test User',
    'email': 'paytest@example.com'
}

# Razorpay test credentials (from .env)
RAZORPAY_KEY_ID = 'rzp_test_T33Adp2MkuoFbJ'
RAZORPAY_KEY_SECRET = 'bMwaIXnmQfg43GFHgtBTXgpJ'

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")


def print_success(text):
    print(f"{GREEN}[✓] {text}{RESET}")


def print_error(text):
    print(f"{RED}[✗] {text}{RESET}")


def print_info(text):
    print(f"{YELLOW}[i] {text}{RESET}")


def print_result(response_data):
    print(f"{BLUE}{json.dumps(response_data, indent=2)}{RESET}")


# ==================== TEST FUNCTIONS ====================

def test_phone_login():
    """Test 1: Request OTP with phone number"""
    print_header("TEST 1: Phone Login (Request OTP)")
    
    response = requests.post(
        f'{BASE_URL}/auth/phone-login/',
        json={'phone': TEST_USER['phone']}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print_result(data)
    
    if response.status_code == 200:
        print_success("OTP generated successfully")
        return data.get('otp')
    else:
        print_error("Failed to generate OTP")
        return None


def test_verify_otp(otp):
    """Test 2: Verify OTP and get authentication token"""
    print_header("TEST 2: Verify OTP and Get Token")
    
    response = requests.post(
        f'{BASE_URL}/auth/verify-otp/',
        json={
            'phone': TEST_USER['phone'],
            'otp': otp,
            'name': TEST_USER['name']
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print_result(data)
    
    if response.status_code == 200:
        print_success("OTP verified and token received")
        token = data.get('token')
        user_id = data.get('user', {}).get('id')
        return token, user_id
    else:
        print_error("Failed to verify OTP")
        return None, None


def test_create_service_if_needed(token=None):
    """Create test service if none exists"""
    print_info("Checking for existing services...")
    
    response = requests.get(f'{BASE_URL}/services/services/')
    services = response.json().get('results', [])
    
    if services:
        print_success(f"Found {len(services)} existing service(s)")
        return services[0]['id']
    
    print_info("No services found, creating test service...")
    
    if not token:
        # Create a temporary token for setup
        print_info("Getting temporary admin token for setup...")
        temp_phone = f"911{random.randint(1000000, 9999999)}"
        response = requests.post(f'{BASE_URL}/auth/phone-login/', json={'phone': temp_phone})
        otp = response.json().get('otp')
        response = requests.post(
            f'{BASE_URL}/auth/verify-otp/',
            json={'phone': temp_phone, 'otp': otp, 'name': 'Setup User'}
        )
        token = response.json().get('token')
        print_success(f"Temporary token obtained for setup")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Create category first
    category_data = {
        'name': 'Test Hair Services',
        'description': 'Test category for payment flow',
        'is_active': True
    }
    
    response = requests.post(
        f'{BASE_URL}/services/categories/',
        json=category_data,
        headers=headers
    )
    
    print(f"Category Response Status: {response.status_code}")
    if response.status_code not in [200, 201]:
        print_error("Failed to create service category")
        print_result(response.json())
        return None
    
    category_id = response.json().get('id')
    print_success(f"Service category created: {category_id}")
    
    # Create service
    service_data = {
        'category': category_id,
        'name': 'Test Hair Cut',
        'description': 'Test service for payment flow',
        'price': '500.00',
        'duration_minutes': 60,
        'is_active': True
    }
    
    response = requests.post(
        f'{BASE_URL}/services/services/',
        json=service_data,
        headers=headers
    )
    
    print(f"Service Response Status: {response.status_code}")
    if response.status_code not in [200, 201]:
        print_error("Failed to create service")
        print_result(response.json())
        return None
    
    service_id = response.json().get('id')
    print_success(f"Service created: {service_id}")
    
    return service_id


def test_create_booking(token):
    """Test 3: Create a booking"""
    print_header("TEST 3: Create a Booking")
    
    # First get service list
    response = requests.get(f'{BASE_URL}/services/services/')
    services = response.json().get('results', [])
    
    if not services:
        print_error("No services available")
        return None
    
    service_id = services[0]['id']
    
    booking_data = {
        'service': service_id,
        'booking_date': '2026-06-25',
        'booking_time': '14:00:00',
        'duration_minutes': 60,
        'total_price': '500.00',
        'notes': 'Test booking for payment'
    }
    
    headers = {'Authorization': f'Token {token}'}
    response = requests.post(
        f'{BASE_URL}/bookings/bookings/',
        json=booking_data,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print_result(data)
    
    if response.status_code == 201:
        print_success("Booking created successfully")
        return data.get('id')
    else:
        print_error("Failed to create booking")
        return None


def test_confirm_booking(token, booking_id):
    """Test 4: Confirm booking (change status to 'confirmed')"""
    print_header("TEST 4: Confirm Booking")
    
    headers = {'Authorization': f'Token {token}'}
    response = requests.patch(
        f'{BASE_URL}/bookings/bookings/{booking_id}/',
        json={'status': 'confirmed'},
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print_result(data)
    
    if response.status_code == 200:
        print_success("Booking confirmed")
        return True
    else:
        print_error("Failed to confirm booking")
        return False


def test_create_payment_order(token, booking_id):
    """Test 5: Create Razorpay payment order"""
    print_header("TEST 5: Create Razorpay Payment Order")
    
    headers = {'Authorization': f'Token {token}'}
    response = requests.post(
        f'{BASE_URL}/payments/create-order/',
        json={'booking_id': booking_id},
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response Text: {response.text}")
    
    try:
        data = response.json()
    except:
        data = {'error': response.text}
    
    print_result(data)
    
    if response.status_code == 201:
        print_success("Razorpay order created")
        return data.get('order_id'), data.get('amount')
    else:
        print_error("Failed to create payment order")
        return None, None


def generate_razorpay_signature(order_id, payment_id):
    """Generate test Razorpay signature"""
    data_to_sign = f"{order_id}|{payment_id}"
    signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        data_to_sign.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def test_verify_payment(token, order_id, amount):
    """Test 6: Verify Razorpay payment"""
    print_header("TEST 6: Verify Razorpay Payment")
    
    # For testing, we'll create a simulated payment ID
    payment_id = f"pay_test_{random.randint(100000, 999999)}"
    signature = generate_razorpay_signature(order_id, payment_id)
    
    headers = {'Authorization': f'Token {token}'}
    response = requests.post(
        f'{BASE_URL}/payments/verify-payment/',
        json={
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        },
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Simulated Payment ID: {payment_id}")
    print(f"Simulated Signature: {signature}")
    data = response.json()
    print_result(data)
    
    if response.status_code == 200:
        print_success("Payment verified successfully")
        return True
    else:
        print_error("Failed to verify payment")
        return False


def test_get_payment_history(token):
    """Test 7: Get payment history"""
    print_header("TEST 7: Get Payment History")
    
    headers = {'Authorization': f'Token {token}'}
    response = requests.get(
        f'{BASE_URL}/payments/history/',
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print_result(data)
    
    if response.status_code == 200:
        count = data.get('count', 0)
        print_success(f"Retrieved payment history ({count} payments)")
        return True
    else:
        print_error("Failed to retrieve payment history")
        return False


def test_get_payment_details(token):
    """Test 8: Get payment details from viewset"""
    print_header("TEST 8: Get Payment Details from Viewset")
    
    headers = {'Authorization': f'Token {token}'}
    response = requests.get(
        f'{BASE_URL}/payments/payments/',
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print_result(data)
    
    if response.status_code == 200:
        count = data.get('count', 0)
        print_success(f"Retrieved payment list ({count} payments)")
        return True
    else:
        print_error("Failed to retrieve payment list")
        return False


def run_all_tests():
    """Run all tests in sequence"""
    print(f"\n{BOLD}{'#'*60}")
    print(f"# PHASE 4 - RAZORPAY PAYMENT INTEGRATION TEST")
    print(f"{'#'*60}{RESET}")
    
    tests_passed = 0
    tests_failed = 0
    
    # Setup: Create service if needed
    print_header("SETUP: Create Test Service If Needed")
    service_id = test_create_service_if_needed()
    if not service_id:
        print_error("Could not create or find test service")
        return 0, 7
    
    # Test 1: Phone login
    otp = test_phone_login()
    if otp:
        tests_passed += 1
    else:
        tests_failed += 1
        return tests_passed, tests_failed
    
    # Test 2: Verify OTP
    token, user_id = test_verify_otp(otp)
    if token:
        tests_passed += 1
    else:
        tests_failed += 1
        return tests_passed, tests_failed
    
    # Test 3: Create booking
    booking_id = test_create_booking(token)
    if booking_id:
        tests_passed += 1
    else:
        tests_failed += 1
        return tests_passed, tests_failed
    
    # Test 4: Create payment order (removed separate confirm step)
    order_id, amount = test_create_payment_order(token, booking_id)
    if order_id:
        tests_passed += 1
    else:
        tests_failed += 1
        return tests_passed, tests_failed
    
    # Test 5: Verify payment
    if test_verify_payment(token, order_id, amount):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 6: Get payment history
    if test_get_payment_history(token):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 7: Get payment details
    if test_get_payment_details(token):
        tests_passed += 1
    else:
        tests_failed += 1
    
    return tests_passed, tests_failed


def print_summary(passed, failed):
    """Print test summary"""
    total = passed + failed
    print(f"\n{BOLD}{'#'*60}")
    print(f"# TEST SUMMARY")
    print(f"{'#'*60}{RESET}")
    print(f"Total Tests: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")
    
    if failed == 0:
        print(f"\n{GREEN}{BOLD}ALL TESTS PASSED!{RESET}")
    else:
        print(f"\n{RED}{BOLD}SOME TESTS FAILED!{RESET}")
    
    print(f"{BOLD}{'#'*60}{RESET}\n")


if __name__ == '__main__':
    try:
        passed, failed = run_all_tests()
        print_summary(passed, failed)
    except Exception as e:
        print_error(f"Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
