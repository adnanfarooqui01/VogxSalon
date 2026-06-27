#!/usr/bin/env python
"""
Quick setup script for Firebase Phone Authentication.
Run this after pulling the code to set up the local development environment.

Usage:
    python setup_firebase.py
"""

import os
import sys
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def check_requirements():
    """Check if all required files exist"""
    print_header("CHECKING REQUIREMENTS")
    
    base_dir = Path(__file__).resolve().parent
    
    checks = {
        'firebase-adminsdk.json': base_dir / 'firebase-adminsdk.json',
        '.env': base_dir / '.env',
        'requirements.txt': base_dir / 'requirements.txt',
        'venv': base_dir / 'venv',
    }
    
    all_good = True
    for name, path in checks.items():
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {name}: {path}")
        if not exists and name in ['firebase-adminsdk.json', '.env']:
            all_good = False
    
    return all_good

def setup_environment():
    """Guide through environment setup"""
    print_header("ENVIRONMENT SETUP")
    
    base_dir = Path(__file__).resolve().parent
    env_file = base_dir / '.env'
    creds_file = base_dir / 'firebase-adminsdk.json'
    
    if not creds_file.exists():
        print("⚠️  firebase-adminsdk.json NOT FOUND")
        print("\nTo fix this:")
        print("1. Go to https://console.firebase.google.com")
        print("2. Select your project (vogxsalon)")
        print("3. Go to Settings → Service Accounts")
        print("4. Click 'Generate New Private Key'")
        print("5. Save the downloaded JSON file as:")
        print(f"   {creds_file}")
        return False
    
    if not env_file.exists():
        print("⚠️  .env NOT FOUND")
        print("\nTo fix this:")
        print("1. Copy .env.example to .env:")
        print(f"   cp .env.example .env")
        print("2. Fill in your Firebase configuration values")
        print("3. Get values from Firebase Console → Project Settings")
        return False
    
    print("✓ Both firebase-adminsdk.json and .env found")
    return True

def run_migrations():
    """Run Django migrations"""
    print_header("RUNNING MIGRATIONS")
    
    os.system('python manage.py migrate')
    print("\n✓ Migrations completed")

def test_firebase():
    """Test Firebase connection"""
    print_header("TESTING FIREBASE CONNECTION")
    
    print("Attempting to initialize Firebase...\n")
    
    try:
        from apps.accounts.firebase_service import initialize_firebase
        initialize_firebase()
        print("✓ Firebase initialization successful!")
        return True
    except Exception as e:
        print(f"✗ Firebase initialization failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure firebase-adminsdk.json is in project root")
        print("2. Check FIREBASE_CREDENTIALS_PATH in .env")
        print("3. Verify Firebase project ID matches")
        return False

def print_next_steps():
    """Print next steps"""
    print_header("NEXT STEPS")
    
    print("1. Start the development server:")
    print("   python manage.py runserver")
    print()
    print("2. Visit http://localhost:8000/login in your browser")
    print()
    print("3. For testing with a Firebase test phone number:")
    print("   - Phone: +919876543210 (or any test number you configured)")
    print("   - OTP: Check Firebase Console → Auth → Sign-in → Test Numbers")
    print()
    print("4. For real SMS testing:")
    print("   - Use any valid Indian phone number")
    print("   - Firebase will send real SMS")
    print()
    print("For full setup guide, see: FIREBASE_SMS_SETUP.md")

def main():
    """Main setup function"""
    print("\n")
    print("╔════════════════════════════════════════════════════╗")
    print("║   Firebase Phone Authentication Setup Helper      ║")
    print("║   VOGX Salon Project                              ║")
    print("╚════════════════════════════════════════════════════╝")
    
    # Check requirements
    if not check_requirements():
        print("\n⚠️  Missing required files! Check the notes above.")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("\n⚠️  Environment setup incomplete!")
        sys.exit(1)
    
    # Run migrations
    run_migrations()
    
    # Test Firebase
    if not test_firebase():
        print("\n⚠️  Firebase test failed. Check configuration.")
        sys.exit(1)
    
    # Print next steps
    print_next_steps()
    
    print("\n✓ Setup completed successfully!\n")

if __name__ == '__main__':
    main()
