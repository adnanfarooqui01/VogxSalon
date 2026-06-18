import uuid
import hashlib
import hmac

from rest_framework import serializers
from django.utils import timezone

from apps.bookings.models import Booking
from .models import Payment


class CreateOrderSerializer(serializers.Serializer):
    """Serializer to create Razorpay order for a booking"""
    booking_id = serializers.IntegerField()
    
    def validate_booking_id(self, value):
        try:
            booking = Booking.objects.get(id=value)
            if booking.status not in ['pending', 'confirmed']:
                raise serializers.ValidationError("Booking must be in pending or confirmed status")
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found")
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer to verify Razorpay payment"""
    razorpay_order_id = serializers.CharField(max_length=100)
    razorpay_payment_id = serializers.CharField(max_length=100)
    razorpay_signature = serializers.CharField(max_length=255)


class PaymentSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source='booking.id', read_only=True)
    booking_customer = serializers.CharField(source='booking.user.name', read_only=True)
    booking_service = serializers.CharField(source='booking.service.name', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'booking',
            'booking_reference',
            'booking_customer',
            'booking_service',
            'amount',
            'status',
            'payment_method',
            'razorpay_payment_id',
            'razorpay_order_id',
            'razorpay_signature',
            'transaction_id',
            'notes',
            'created_at',
            'updated_at',
            'paid_at',
        ]
        read_only_fields = [
            'id',
            'booking_reference',
            'booking_customer',
            'booking_service',
            'amount',
            'transaction_id',
            'created_at',
            'updated_at',
            'paid_at',
        ]

    def create(self, validated_data):
        booking = validated_data['booking']
        validated_data['amount'] = booking.total_price
        validated_data.setdefault('transaction_id', f"TXN-{uuid.uuid4().hex[:20].upper()}")
        return super().create(validated_data)
