"""
DEVELOPMENT-ONLY mock OTP service.

This module has the exact same function signatures as a real OTP provider
(send_otp, verify_otp, resend_otp) so that swapping in a real provider later
(WhatsApp OTP, Twilio Verify, MSG91, etc.) requires changing ONLY this file -
nothing in views.py, serializers.py, or urls.py needs to change.

How it works in development:
- send_otp() always "succeeds" and logs the OTP to the console instead of
  actually sending an SMS/WhatsApp message.
- The OTP is always the fixed test code below, UNLESS DEV_OTP_RANDOM is
  turned on, in which case a random 6-digit code is generated and printed
  to the console/terminal for you to read and enter manually.
- verify_otp() checks against that same fixed/random code.

⚠️ IMPORTANT: This file must NEVER be used in production. It does not send
real messages and accepts a hardcoded code. Switch to a real provider
(see PRODUCTION_NOTES.md or the WhatsApp/Twilio version of this file)
before going live.
"""

import logging
import random

logger = logging.getLogger(__name__)

# Fixed OTP used in development when DEV_OTP_RANDOM is False (default).
# Anyone testing the app just types this code to "log in" instantly.
DEV_FIXED_OTP = "123456"

# Set to True if you'd rather see a different random OTP each time in the
# console (closer to real behaviour, useful for testing the resend flow).
DEV_OTP_RANDOM = False

# In-memory store of the "sent" OTP per phone number, for this dev server's
# lifetime only. Resets every time you restart `runserver`.
_otp_store = {}


def send_otp(phone):
    """
    DEV MODE: Pretend to send an OTP. Actually just logs it to the console.

    Args:
        phone (str): Phone number (any format works in dev mode)

    Returns:
        dict: {"success": bool, "message": str, "request_id": str|None}
    """
    otp = (
        f"{random.randint(100000, 999999)}"
        if DEV_OTP_RANDOM
        else DEV_FIXED_OTP
    )
    _otp_store[phone] = otp

    # This print is intentional and important in dev mode - it's how you
    # "receive" the OTP without a real SMS/WhatsApp provider connected.
    print(f"\n{'='*50}\n[DEV OTP] Phone: {phone}  ->  OTP: {otp}\n{'='*50}\n")
    logger.info("[DEV MODE] OTP for %s is %s", phone, otp)

    return {"success": True, "message": "OTP sent successfully (dev mode)", "request_id": "dev-request"}


def verify_otp(phone, otp):
    """
    DEV MODE: Verify the OTP against what we "sent" (or the fixed code).

    Args:
        phone (str): Phone number used when sending the OTP
        otp (str): The OTP code entered by the user

    Returns:
        dict: {"success": bool, "message": str}
    """
    expected = _otp_store.get(phone, DEV_FIXED_OTP)

    if otp == expected or otp == DEV_FIXED_OTP:
        logger.info("[DEV MODE] OTP verified for %s", phone)
        return {"success": True, "message": "OTP verified successfully (dev mode)"}

    logger.warning("[DEV MODE] OTP mismatch for %s (got %s, expected %s)", phone, otp, expected)
    return {"success": False, "message": "Invalid OTP"}


def resend_otp(phone, retry_type="text"):
    """
    DEV MODE: Pretend to resend an OTP. Just calls send_otp again.

    Args:
        phone (str): Phone number
        retry_type (str): Ignored in dev mode, kept for signature compatibility

    Returns:
        dict: {"success": bool, "message": str}
    """
    result = send_otp(phone)
    return {"success": result["success"], "message": "OTP resent successfully (dev mode)"}