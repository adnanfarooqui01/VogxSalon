"""
Firebase Admin SDK integration for phone authentication and ID token verification.

This module uses Firebase Admin SDK to:
1. Initialize Firebase with service account credentials
2. Verify Firebase ID tokens sent by authenticated clients
3. Extract user claims from tokens

The frontend handles OTP sending via Firebase Authentication's Phone Authentication.
This backend only verifies tokens returned by the frontend after successful OTP verification.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Firebase availability flag
FIREBASE_INITIALIZED = False

# Try to import Firebase
try:
    import firebase_admin
    from firebase_admin import credentials, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    logger.warning("Firebase Admin SDK not installed. Install with: pip install firebase-admin==6.4.0")
    firebase_admin = None
    credentials = None
    auth = None
    FIREBASE_AVAILABLE = False

from django.conf import settings


def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials.
    
    Reads credentials from:
    1. FIREBASE_CREDENTIALS_PATH environment variable
    2. FIREBASE_CREDENTIALS_PATH setting in Django settings
    3. firebase-adminsdk.json in project root (fallback)
    
    Raises:
        FileNotFoundError: If credentials file not found
        ValueError: If Firebase already initialized
        Exception: For Firebase initialization errors
    """
    global FIREBASE_INITIALIZED
    
    if not FIREBASE_AVAILABLE:
        logger.warning("Firebase Admin SDK not available")
        return False
    
    if FIREBASE_INITIALIZED:
        logger.debug("Firebase already initialized")
        return True
    
    try:
        # Try to get existing Firebase app
        firebase_admin.get_app()
        FIREBASE_INITIALIZED = True
        logger.info("✓ Firebase already initialized")
        return True
    except ValueError:
        # App not initialized yet, proceed with initialization
        pass
    
    # Get credentials path from environment or settings
    cred_path = (
        os.getenv('FIREBASE_CREDENTIALS_PATH') or
        getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None) or
        Path(settings.BASE_DIR) / 'firebase-adminsdk.json'
    )
    
    cred_path = Path(cred_path)
    
    if not cred_path.exists():
        logger.error(f"✗ Firebase credentials not found at {cred_path}")
        raise FileNotFoundError(
            f"Firebase credentials file not found at {cred_path}. "
            f"Set FIREBASE_CREDENTIALS_PATH environment variable or place firebase-adminsdk.json in project root."
        )
    
    try:
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv('FIREBASE_DATABASE_URL', 'https://vogxsalon.firebaseio.com'),
            'projectId': os.getenv('FIREBASE_PROJECT_ID', 'vogxsalon'),
        })
        
        FIREBASE_INITIALIZED = True
        logger.info("✓ Firebase Admin SDK initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error initializing Firebase Admin SDK: {str(e)}")
        raise Exception(f"Firebase initialization failed: {str(e)}")


def verify_firebase_id_token(id_token):
    """
    Verify Firebase ID token and extract user claims.
    
    This is called after the frontend successfully verifies an OTP with Firebase.
    The frontend sends us the ID token, and we verify it using Firebase Admin SDK.
    
    Args:
        id_token (str): Firebase ID token from client
    
    Returns:
        dict: User claims containing:
            - uid (str): Firebase user ID
            - phone_number (str): User's phone number
            - firebase_sign_in_provider (str): 'phone' for phone auth
            - iat (int): Token issued at timestamp
            - exp (int): Token expiration timestamp
    
    Raises:
        ValueError: If token is invalid or expired
        Exception: If Firebase not initialized
    
    Example:
        >>> try:
        ...     claims = verify_firebase_id_token(id_token)
        ...     phone = claims['phone_number']
        ...     firebase_uid = claims['uid']
        ... except ValueError as e:
        ...     print(f"Invalid token: {e}")
    """
    if not FIREBASE_AVAILABLE:
        raise Exception("Firebase Admin SDK not installed")

    try:
        # Ensure Firebase is initialized
        if not FIREBASE_INITIALIZED:
            initialize_firebase()

        # Verify the token using Firebase Admin SDK
        claims = auth.verify_id_token(id_token)

        logger.info(f"✓ Token verified for Firebase UID: {claims.get('uid')}")
        return claims

    except auth.InvalidIdTokenError as e:
        logger.warning(f"✗ Invalid Firebase ID token: {str(e)}")
        raise ValueError("Invalid token. Authentication failed.")

    except Exception as e:
        logger.error(f"✗ Error verifying Firebase token: {str(e)}")
        raise ValueError(f"Token verification failed: {str(e)}")

def get_user_by_phone(phone_number):
    """
    Get Firebase user by phone number.
    
    Args:
        phone_number (str): Phone number in E.164 format (e.g., +919876543210)
    
    Returns:
        firebase_admin.auth.UserRecord: Firebase user object or None
    """
    if not FIREBASE_AVAILABLE:
        return None
    
    try:
        if not FIREBASE_INITIALIZED:
            initialize_firebase()
        
        user = auth.get_user_by_phone_number(phone_number)
        logger.debug(f"Found Firebase user for {phone_number}")
        return user
        
    except auth.UserNotFoundError:
        logger.debug(f"No Firebase user found for {phone_number}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching user by phone: {str(e)}")
        return None


def create_custom_token(uid):
    """
    Create a custom Firebase token (rarely needed with ID tokens).
    
    Args:
        uid (str): Firebase user UID
    
    Returns:
        str: Custom token
    """
    if not FIREBASE_AVAILABLE:
        return None
    
    try:
        if not FIREBASE_INITIALIZED:
            initialize_firebase()
        
        token = auth.create_custom_token(uid)
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        logger.debug(f"Created custom token for UID: {uid}")
        return token
        
    except Exception as e:
        logger.error(f"Error creating custom token: {str(e)}")
        return None


# Try to initialize Firebase when module is loaded (Django startup)
# But don't fail if it's not available yet (e.g., during migrations)
if FIREBASE_AVAILABLE:
    try:
        initialize_firebase()
    except Exception as e:
        logger.warning(f"Firebase initialization deferred: {str(e)}")
        logger.info("Ensure FIREBASE_CREDENTIALS_PATH is set before using auth endpoints")
