# Firebase Phone Authentication SMS Setup Guide

## Overview

This guide walks you through setting up Firebase Phone Authentication with real SMS delivery for your VOGX Salon application. The system will:

1. ✅ Send real SMS OTPs to users via Firebase
2. ✅ Handle OTP verification on the frontend
3. ✅ Create/authenticate users on the backend with ID tokens
4. ✅ Work on localhost for development
5. ✅ Deploy to production (Hostinger, AWS, etc.)

## Prerequisites

- Active Firebase project (create at https://console.firebase.google.com)
- Firebase project with Realtime Database enabled
- Firebase Authentication with Phone enabled
- Firebase Admin SDK credentials downloaded
- Python 3.8+ with venv
- PostgreSQL database (production recommended)

## Step 1: Firebase Console Configuration

### 1.1 Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Add project" or use existing project
3. Project ID: `vogxsalon`
4. Enable Google Analytics (optional)
5. Click "Create project"

### 1.2 Enable Phone Authentication

1. Go to **Authentication** section
2. Click **Sign-in method** tab
3. Click **Phone** from the list
4. Enable the toggle for "Phone"
5. Under "Phone numbers for testing", add your test phone number:
   - Format: +919876543210
   - Test OTP code: 123456 (remember this)
6. Click "Save"

### 1.3 Download Service Account Key

1. Go to **Project Settings** (gear icon)
2. Click **Service Accounts** tab
3. Click **Generate New Private Key**
4. Save the JSON file as `firebase-adminsdk.json` in your project root
5. **IMPORTANT**: Add to `.gitignore`!

### 1.4 Get Firebase Web Config

1. Go to **Project Settings**
2. Find **Your apps** section
3. Copy the Web API credentials:
   - apiKey
   - authDomain
   - projectId
   - storageBucket
   - messagingSenderId
   - appId

## Step 2: Local Development Setup

### 2.1 Copy Environment Configuration

```bash
# Navigate to project root
cd c:\Users\ADMIN\VOGX_Salon\VogxSalon

# Copy the example .env file
copy .env.example .env
```

### 2.2 Update .env with Firebase Config

Open `.env` and fill in:

```env
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=firebase-adminsdk.json
FIREBASE_PROJECT_ID=vogxsalon
FIREBASE_DATABASE_URL=https://vogxsalon.firebaseio.com
FIREBASE_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FIREBASE_AUTH_DOMAIN=vogxsalon.firebaseapp.com
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:abcdefghijklmnop
FIREBASE_STORAGE_BUCKET=vogxsalon.appspot.com
```

### 2.3 Place Firebase Credentials

1. Download `firebase-adminsdk.json` from Firebase Console
2. Place it in project root: `c:\Users\ADMIN\VOGX_Salon\VogxSalon\firebase-adminsdk.json`
3. Add to `.gitignore`:

```bash
# In .gitignore
firebase-adminsdk.json
.env
.env.local
```

### 2.4 Install Dependencies

```bash
# Activate virtual environment
cd c:\Users\ADMIN\VOGX_Salon\VogxSalon
.\venv\Scripts\activate

# Install/update requirements
pip install -r requirements.txt

# Or install firebase-admin specifically
pip install firebase-admin==6.4.0
```

### 2.5 Run Migrations

```bash
# Create migration for firebase_uid field
python manage.py makemigrations accounts

# Apply migration
python manage.py migrate
```

### 2.6 Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 2.7 Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000/login` to test the authentication.

## Step 3: Testing the OTP Flow

### 3.1 Local Testing with Firebase Test Phone

1. Open browser to `http://localhost:8000/login`
2. Enter test phone number: `+919876543210`
3. Click "Send OTP"
4. Firebase will NOT send SMS for test numbers
5. Instead, go to Firebase Console → Authentication → Sign-in method → Phone
6. In the "Phone numbers for testing" section, you'll see the test code (default: `123456`)
7. Enter the 6-digit code on the login form
8. Click "Verify & Continue"
9. You should be logged in!

### 3.2 Real Phone Testing

For real phone testing:
1. Enter any valid Indian phone number: `+919XXXXXXXXX`
2. Firebase will send real SMS with OTP
3. Enter the OTP you receive
4. You should be logged in!

**Note**: Firebase allows up to 50 SMS/day for new projects in test mode.

## Step 4: Backend API Documentation

### Endpoint: `/api/auth/verify-firebase-token/`

**Method**: POST

**Request**:
```json
{
    "idToken": "firebase_id_token_from_client",
    "name": "optional_user_name"
}
```

**Response (Success)**:
```json
{
    "token": "django_auth_token_abc123def456",
    "user": {
        "id": 1,
        "phone": "+919876543210",
        "name": "User Name",
        "email": "user@example.com",
        "firebase_uid": "firebase_user_id_xyz"
    },
    "message": "Login successful",
    "firebase_uid": "firebase_user_id_xyz"
}
```

**Response (Error)**:
```json
{
    "detail": "Invalid token. Authentication failed."
}
```

## Step 5: Frontend Integration Details

### How It Works

1. **User enters phone number**
   - Frontend calls Firebase: `signInWithPhoneNumber(phone, recaptchaVerifier)`
   - Firebase sends SMS with OTP
   - Frontend receives `verificationId`

2. **User enters OTP**
   - Frontend calls Firebase: `signInWithCredential(credential)`
   - Firebase verifies OTP matches what was sent
   - Firebase returns `user` with auth state

3. **Get ID Token**
   - Frontend calls: `user.getIdToken()`
   - Returns JWT token signed by Firebase

4. **Send to Django Backend**
   - POST `/api/auth/verify-firebase-token/` with `idToken`
   - Backend verifies token using Firebase Admin SDK
   - Backend creates Django user and returns `authToken`

5. **Store Token**
   - Frontend stores Django `authToken` in localStorage
   - Uses this for all subsequent API calls

## Step 6: Production Deployment (Hostinger)

### 6.1 Prepare Production Environment

Create `.env.production`:

```env
DEBUG=False
SECRET_KEY=your-production-secret-key-change-this
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_ENGINE=postgresql
DB_NAME=vogx_salon_prod
DB_USER=vogx_prod_user
DB_PASSWORD=very-strong-password
DB_HOST=your-db-host.hostinger.com
DB_PORT=5432

# Firebase (same as development)
FIREBASE_CREDENTIALS_PATH=/home/your-user/vogxsalon/firebase-adminsdk.json
FIREBASE_PROJECT_ID=vogxsalon
FIREBASE_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ... rest of Firebase config

# HTTPS
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 6.2 Upload to Hostinger

1. SSH into your Hostinger account
2. Create project directory: `/home/username/vogxsalon/`
3. Upload files (excluding `.env`, `firebase-adminsdk.json`, `venv/`)
4. Upload `firebase-adminsdk.json` to: `/home/username/vogxsalon/firebase-adminsdk.json`
5. Create `.env` with production values

### 6.3 Setup Python Environment

```bash
# SSH into Hostinger
ssh username@your-host

# Navigate to project
cd /home/username/vogxsalon

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput
```

### 6.4 Configure Gunicorn

Create `/home/username/vogxsalon/gunicorn_config.py`:

```python
import multiprocessing

bind = "127.0.0.1:8001"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 60
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
```

Start Gunicorn:

```bash
gunicorn salon_project.wsgi:application --config gunicorn_config.py
```

### 6.5 Configure Nginx (On Hostinger)

Most Hostinger plans use Apache. Check their documentation or contact support for Django deployment.

### 6.6 Firebase URLs Configuration

Update Firebase Console:

1. Go to **Authentication** → **Settings**
2. Add Authorized domains:
   - `yourdomain.com`
   - `www.yourdomain.com`

## Step 7: Troubleshooting

### Issue: "Firebase Admin SDK not installed"

**Solution**:
```bash
pip install firebase-admin==6.4.0
```

### Issue: "firebase-adminsdk.json not found"

**Solution**:
1. Verify file exists: `c:\Users\ADMIN\VOGX_Salon\VogxSalon\firebase-adminsdk.json`
2. Check FIREBASE_CREDENTIALS_PATH in `.env` is correct
3. Check file is readable and not corrupted

### Issue: "OTP not received"

**For test numbers**:
- Use the test code shown in Firebase Console
- Test numbers are for development only

**For real numbers**:
- Ensure Firebase project is not in restricted mode
- Check Firebase billing quota
- Verify phone number format is E.164 (+country code + number)
- Check Firebase Realtime Database has CORS enabled

### Issue: "CORS error on login"

**Solution**:
1. Django is blocking requests from frontend
2. Check CORS_ALLOWED_ORIGINS in settings
3. Ensure frontend URL is in the list:

```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://yourdomain.com',
]
```

### Issue: "Invalid token" error

**Solution**:
1. Token may have expired (expires in 1 hour)
2. Firebase credentials file may be invalid
3. Check FIREBASE_PROJECT_ID matches between config and credentials file

## Step 8: Security Checklist

Before production deployment:

- [ ] Add `firebase-adminsdk.json` to `.gitignore`
- [ ] Remove test phone numbers from Firebase Console
- [ ] Set `DEBUG=False` in production
- [ ] Use strong SECRET_KEY in production
- [ ] Enable HTTPS/SSL
- [ ] Set `SECURE_SSL_REDIRECT=True`
- [ ] Use environment-specific `.env` files
- [ ] Rotate credentials regularly
- [ ] Enable Firebase API key restrictions
- [ ] Use PostgreSQL instead of SQLite in production
- [ ] Set up proper logging and monitoring
- [ ] Configure Firebase rate limiting
- [ ] Enable Cloud Audit Logs on Firebase

## Step 9: Next Steps

### After Getting SMS OTP Working

1. **Test all pages**: Ensure home, services, cart pages work
2. **Test bookings**: Create, modify, cancel bookings
3. **Setup payments**: Integrate Razorpay for payments
4. **Add reviews**: Implement review submission
5. **Deploy to production**: Follow production deployment steps

### Optional Enhancements

1. **Social Login**: Add Google/Facebook authentication
2. **Email Verification**: Add email verification for better UX
3. **Multi-Language**: Support Hindi, regional languages
4. **Push Notifications**: Send appointment reminders via FCM
5. **Analytics**: Track user behavior with Firebase Analytics

## Support & Resources

- Firebase Documentation: https://firebase.google.com/docs
- Django Documentation: https://docs.djangoproject.com/
- DRF Documentation: https://www.django-rest-framework.org/
- Firebase Admin SDK: https://firebase.google.com/docs/admin/setup

---

**Last Updated**: June 2026
**Version**: 1.0
