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
            if booking.status != 'confirmed':
                raise serializers.ValidationError("Booking must be in confirmed status")
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found")
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer to verify Razorpay payment"""
    razorpay_order_id = serializers.CharField(max_length=100)
    razorpay_payment_id = serializers.CharField(max_length=100)
    razorpay_signature = serializers.CharField(max_length=255)


class PaymentSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source='booking_group.id', read_only=True)
    booking_customer = serializers.CharField(source='booking_group.user.name', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'booking_group',
            'booking_reference',
            'booking_customer',
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
            'amount',
            'transaction_id',
            'created_at',
            'updated_at',
            'paid_at',
        ]

    def create(self, validated_data):
        group = validated_data['booking_group']
        validated_data['amount'] = group.total_price
        validated_data.setdefault('transaction_id', f"TXN-{uuid.uuid4().hex[:20].upper()}")
        return super().create(validated_data)