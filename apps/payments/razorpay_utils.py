"""
Razorpay payment gateway integration utilities.

SECURITY NOTES:
- verify_razorpay_signature and verify_webhook_signature use hmac.compare_digest
  (constant-time comparison) to avoid timing attacks.
- There is NO "DEBUG mode bypass" here on purpose. A bypass like
  `if DEBUG: return True` is a critical vulnerability if DEBUG is ever left
  True in any reachable environment (staging, misconfigured prod) — it lets
  anyone mark any payment as verified without actually paying. Test payments
  in Razorpay's TEST MODE go through the exact same signature verification
  as live payments; that's what test mode is for.
"""
import hashlib
import hmac
import logging

from decouple import config
import razorpay

logger = logging.getLogger(__name__)


def get_razorpay_client():
    """Initialize and return Razorpay client."""
    razorpay_key = config('RAZORPAY_KEY_ID')
    razorpay_secret = config('RAZORPAY_KEY_SECRET')
    return razorpay.Client(auth=(razorpay_key, razorpay_secret))


def create_razorpay_order(amount, currency='INR', receipt=None, notes=None):
    """
    Create a Razorpay order.

    Args:
        amount: Amount in rupees (will be converted to paise internally)
        currency: Currency code (default: INR)
        receipt: Unique receipt identifier
        notes: Dictionary of metadata (keep small — Razorpay limits notes size)

    Returns:
        dict: Razorpay order details, or None if creation failed
    """
    try:
        client = get_razorpay_client()

        order_data = {
            'amount': int(round(amount * 100)),  # convert to paise, avoid float rounding issues
            'currency': currency,
            'receipt': receipt,
        }
        if notes:
            order_data['notes'] = notes

        order = client.order.create(data=order_data)
        logger.info(f"Razorpay order created: {order.get('id')} amount={order_data['amount']}")
        return order

    except Exception:
        logger.exception(f"Failed to create Razorpay order for receipt={receipt}")
        return None


def verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Verify the signature returned to the FRONTEND after checkout completes
    (Razorpay Checkout.js callback). This confirms the payment_id/order_id
    pair genuinely came from Razorpay and wasn't forged by the client.

    Returns True only if the signature is valid. No bypasses.
    """
    try:
        razorpay_secret = config('RAZORPAY_KEY_SECRET')
        data_to_verify = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(
            razorpay_secret.encode(), data_to_verify.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, razorpay_signature)
    except Exception:
        logger.exception("Error verifying Razorpay checkout signature")
        return False


def verify_webhook_signature(request_body: bytes, received_signature: str) -> bool:
    """
    Verify a Razorpay WEBHOOK payload signature.

    This uses a SEPARATE secret from your API key/secret — the "Webhook
    Secret" you set when configuring the webhook URL in the Razorpay
    Dashboard (Settings > Webhooks). Never reuse RAZORPAY_KEY_SECRET here.

    Args:
        request_body: the raw request body bytes (must be unparsed/unmodified —
                       hashing a re-serialized JSON dict will not match)
        received_signature: value of the 'X-Razorpay-Signature' header

    Returns:
        bool: True if signature is valid
    """
    try:
        webhook_secret = config('RAZORPAY_WEBHOOK_SECRET')
        expected_signature = hmac.new(
            webhook_secret.encode(), request_body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, received_signature or '')
    except Exception:
        logger.exception("Error verifying Razorpay webhook signature")
        return False


def fetch_payment_details(payment_id):
    """
    Fetch payment details directly from Razorpay's API (source of truth).

    Use this to double-check the actual captured amount/status server-side
    rather than trusting only the signature + client-supplied data — the
    signature proves the payment_id/order_id pairing is genuine, but you
    should still confirm what was actually captured.

    Returns:
        dict: Payment details, or None if fetch failed
    """
    try:
        client = get_razorpay_client()
        return client.payment.fetch(payment_id)
    except Exception:
        logger.exception(f"Failed to fetch payment details for payment_id={payment_id}")
        return None


def refund_payment(payment_id, amount=None, notes=None):
    """
    Refund a payment.

    Args:
        payment_id: Razorpay payment ID
        amount: Amount to refund in RUPEES (None = full refund). Converted
                to paise internally, consistent with create_razorpay_order.
        notes: Dictionary of metadata

    Returns:
        dict: Refund details, or None if refund failed
    """
    try:
        client = get_razorpay_client()

        refund_data = {}
        if amount is not None:
            refund_data['amount'] = int(round(amount * 100))
        if notes:
            refund_data['notes'] = notes

        refund = client.payment.refund(payment_id, refund_data)
        logger.info(f"Refund created for payment_id={payment_id}: {refund.get('id')}")
        return refund
    except Exception:
        logger.exception(f"Failed to refund payment_id={payment_id}")
        return None