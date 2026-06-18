import uuid

from rest_framework import serializers

from apps.bookings.models import Booking
from .models import Payment


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
