# Firebase Phone Authentication Testing Guide

## Quick Test (5 minutes)

### Prerequisites
- Server running: `python manage.py runserver`
- Browser open to: `http://localhost:8000/login`

### Test 1: Firebase Test Phone Number

**Setup**:
1. Go to Firebase Console → Authentication → Sign-in method
2. Under "Phone numbers for testing", add/verify:
   - Phone: `+919876543210`
   - OTP Code: `123456` (default)

**Steps**:
1. On login page, enter: `+919876543210`
2. Click "Send OTP"
3. Enter OTP: `123456`
4. Click "Verify & Continue"
5. Should redirect to home page (logged in)

**Expected Result**: ✅ Login successful, redirected to home

---

## Test 2: Real Phone Number Testing

⚠️ **Warning**: Uses Firebase SMS quota. Firebase gives 50 SMS/day for free.

**Setup**:
1. Ensure you have real phone number: `+919876543210` (example)
2. Have phone nearby to receive SMS

**Steps**:
1. On login page, enter your real phone
2. Click "Send OTP"
3. You'll receive SMS with 6-digit code
4. Enter the code
5. Click "Verify & Continue"
6. Should redirect to home page

**Expected Result**: ✅ Login successful, SMS received

---

## Test 3: Error Handling

### Wrong OTP
1. Enter phone: `+919876543210`
2. Click "Send OTP"
3. Enter wrong OTP: `000000`
4. Click "Verify & Continue"
5. Should show error: "Invalid OTP"

**Expected Result**: ✅ Error message displayed

### Invalid Phone Format
1. Enter phone: `9876543210` (no +91)
2. Click "Send OTP"
3. Should convert to `+919876543210`
4. Proceed with OTP

**Expected Result**: ✅ Phone format auto-corrected

### Expired OTP
1. Enter phone: `+919876543210`
2. Click "Send OTP"
3. Wait for 10 minutes (default Firebase timeout is 5 mins)
4. Enter OTP
5. Click "Verify & Continue"
6. Should show error: "Session expired"

**Expected Result**: ✅ Expired session handled

---

## Test 4: User Creation vs Login

### First Login (New User)
1. Enter new phone: `+919111111111`
2. Complete OTP flow
3. Should show: "Account created and logged in"
4. Check Django admin: User created with this phone

**Expected Result**: ✅ New user created

### Second Login (Existing User)
1. Use same phone: `+919111111111`
2. Complete OTP flow
3. Should show: "Login successful"
4. Check Django admin: Same user, `last_login` updated

**Expected Result**: ✅ Existing user logged in

---

## Test 5: Frontend Integration

### Check LocalStorage
1. Login successfully
2. Open browser DevTools (F12)
3. Go to Application → LocalStorage → `http://localhost:8000`
4. Check for `authToken` key
5. Value should be Django token

**Expected Result**: ✅ Token stored in localStorage

### Check API Calls
1. Login successfully
2. Open DevTools → Network tab
3. Look for request to `/api/auth/verify-firebase-token/`
4. Check Request:
   - Method: POST
   - Headers: Content-Type: application/json
   - Body: `{idToken: "...", name: "..."}`
5. Check Response:
   - Status: 200 OK
   - Contains: `token`, `user`, `firebase_uid`

**Expected Result**: ✅ API call successful with correct payload

---

## Test 6: Protected Endpoints

### Test Profile Endpoint
1. Login successfully
2. Copy token from localStorage
3. Open Terminal/Postman
4. Send request:
```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

**Expected Result**: ✅ Returns user profile data (200 OK)

### Without Token (Should Fail)
```bash
curl -X GET http://localhost:8000/api/auth/profile/
```

**Expected Result**: ✅ 401 Unauthorized error

---

## Test 7: reCAPTCHA Integration

### reCAPTCHA Display
1. Go to login page
2. Look for reCAPTCHA badge in bottom right
3. Text: "This site is protected by reCAPTCHA"

**For Development**:
- reCAPTCHA can be set to "invisible" mode
- No user interaction needed
- Still validated by Firebase

**Expected Result**: ✅ reCAPTCHA displays correctly

---

## Debugging Tips

### Enable Verbose Logging
1. Edit `salon_project/settings/development.py`
2. Set logging level to DEBUG:
```python
LOGGING = {
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    }
}
```
3. Restart server
4. Check terminal for detailed logs

### Check Firebase Credentials
```python
# In Django shell
python manage.py shell

>>> from apps.accounts.firebase_service import FIREBASE_INITIALIZED
>>> print(FIREBASE_INITIALIZED)
True  # Should be True
```

### Monitor Network Requests
1. Open DevTools → Network tab
2. Check:
   - OTP send request (should POST to Firebase via client SDK)
   - OTP verify request (should POST to `/api/auth/verify-firebase-token/`)
3. Look for CORS errors (red requests)

### Check Browser Console
1. Open DevTools → Console
2. Watch for Firebase-related errors
3. Common errors:
   - "Auth not initialized" → Check Firebase config in .env
   - "reCAPTCHA error" → Check Firebase reCAPTCHA site keys
   - "CORS error" → Check CORS_ALLOWED_ORIGINS in Django settings

---

## Common Issues & Fixes

### Issue: "OTP not received"
- **For test numbers**: Check Firebase Console for test OTP code
- **For real numbers**: Check SMS quota (50/day limit)
- **Fix**: Enable Firebase Cloud Messaging or check carrier blocking

### Issue: "Invalid token error"
- **Token expired**: OTP verification timeout
- **Wrong credentials**: Check firebase-adminsdk.json path
- **Fix**: Restart server, re-verify with fresh OTP

### Issue: "CORS error on login"
- **Frontend blocked by Django**: Update CORS_ALLOWED_ORIGINS
- **Firebase config missing**: Check .env and context processor
- **Fix**: Run `python manage.py shell` and test import

### Issue: "reCAPTCHA always fails"
- **Wrong Firebase config**: Double-check API key and auth domain
- **Development mode**: Set to invisible reCAPTCHA in Firebase Console
- **Fix**: Clear browser cache and cookies

---

## Performance Testing

### Load Testing OTP Endpoint
```bash
# Using Apache Bench (ab command)
ab -n 100 -c 10 http://localhost:8000/api/auth/verify-firebase-token/
```

**Expected Result**: Response time < 500ms per request

### Database Query Optimization
```python
# Check queries
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as queries:
    # Your code here
    pass

print(f"Total queries: {len(queries)}")
```

**Expected Result**: Login flow uses 2-3 queries max

---

## Production Testing Checklist

Before deploying to production:

- [ ] Test with real phone numbers and SMS
- [ ] Verify error handling for all edge cases
- [ ] Test with high load (multiple concurrent logins)
- [ ] Check database performance with 1000+ users
- [ ] Verify Firebase rate limiting
- [ ] Test with different carriers/regions
- [ ] Check SSL/TLS on production domain
- [ ] Monitor Firebase usage and costs
- [ ] Setup Firebase authentication rules
- [ ] Enable Firebase audit logging

---

## Automated Testing

Create `apps/accounts/tests/test_firebase_auth.py`:

```python
from django.test import TestCase
from rest_framework.test import APIClient
from apps.accounts.models import CustomUser
import json

class FirebaseAuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_user_creation_on_login(self):
        # Test that user is created on first login
        pass
    
    def test_token_generation(self):
        # Test that auth token is returned
        pass
    
    def test_existing_user_login(self):
        # Test that existing user can login
        pass
```

Run tests:
```bash
python manage.py test apps.accounts
```

---

**Last Updated**: June 2026
**Firebase Version**: 10.7.0
**Django Version**: 5.0.6
