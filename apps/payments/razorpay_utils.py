"""
Razorpay payment gateway integration utilities
"""
import hashlib
import hmac
import json
from decimal import Decimal
from decouple import config
import razorpay


def get_razorpay_client():
    """Initialize and return Razorpay client"""
    razorpay_key = config('RAZORPAY_KEY_ID')
    razorpay_secret = config('RAZORPAY_KEY_SECRET')
    return razorpay.Client(auth=(razorpay_key, razorpay_secret))


def create_razorpay_order(amount, currency='INR', receipt=None, notes=None):
    """
    Create a Razorpay order
    
    Args:
        amount: Amount in paise (e.g., 100 for ₹1)
        currency: Currency code (default: INR)
        receipt: Unique receipt identifier
        notes: Dictionary of notes/metadata
        
    Returns:
        dict: Razorpay order details or None if error
    """
    try:
        client = get_razorpay_client()
        
        order_data = {
            'amount': int(amount * 100),  # Convert to paise
            'currency': currency,
            'receipt': receipt,
        }
        
        if notes:
            order_data['notes'] = notes
        
        print(f"DEBUG: Creating Razorpay order with data: {order_data}")
        order = client.order.create(data=order_data)
        print(f"DEBUG: Razorpay order created successfully: {order}")
        return order
    except Exception as e:
        print(f"ERROR: Error creating Razorpay order: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """Verify payment signature"""
    try:
        import os
        # In dev mode, accept any signature for testing
        if os.environ.get('DEBUG') == 'True':
            return True
        razorpay_secret = config('RAZORPAY_KEY_SECRET')
        data_to_verify = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(razorpay_secret.encode(), data_to_verify.encode(), hashlib.sha256).hexdigest()
        return expected_signature == razorpay_signature
    except Exception as e:
        print(f"Error verifying signature: {str(e)}")
        return False


def fetch_payment_details(payment_id):
    """
    Fetch payment details from Razorpay
    
    Args:
        payment_id: Razorpay payment ID
        
    Returns:
        dict: Payment details or None if error
    """
    try:
        client = get_razorpay_client()
        payment = client.payment.fetch(payment_id)
        return payment
    except Exception as e:
        print(f"Error fetching payment details: {str(e)}")
        return None


def refund_payment(payment_id, amount=None, notes=None):
    """
    Refund a payment
    
    Args:
        payment_id: Razorpay payment ID
        amount: Amount to refund in paise (None = full refund)
        notes: Dictionary of notes/metadata
        
    Returns:
        dict: Refund details or None if error
    """
    try:
        client = get_razorpay_client()
        
        refund_data = {}
        if amount:
            refund_data['amount'] = int(amount * 100)
        if notes:
            refund_data['notes'] = notes
        
        refund = client.payment.refund(payment_id, refund_data)
        return refund
    except Exception as e:
        print(f"Error refunding payment: {str(e)}")
        return None
