from rest_framework import serializers

from apps.services.models import Service
from .models import TimeSlot, Booking


class TimeSlotSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = TimeSlot
        fields = ['id', 'service', 'service_name', 'date', 'time', 'is_available', 'created_at']
        read_only_fields = ['id', 'service_name', 'created_at']


class BookingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'user_name',
            'service',
            'service_name',
            'service_price',
            'booking_date',
            'booking_time',
            'duration_minutes',
            'total_price',
            'status',
            'notes',
            'is_paid',
            'payment_status',
            'created_at',
            'updated_at',
            'completed_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_name',
            'service_name',
            'service_price',
            'duration_minutes',
            'total_price',
            'status',
            'is_paid',
            'payment_status',
            'created_at',
            'updated_at',
            'completed_at',
        ]

    def get_payment_status(self, obj):
        payment = getattr(obj, 'payment', None)
        return payment.status if payment else None

    def create(self, validated_data):
        request = self.context.get('request')
        service = validated_data['service']
        validated_data['user'] = request.user
        validated_data['duration_minutes'] = service.duration_minutes
        validated_data['total_price'] = service.price
        validated_data.setdefault('status', 'pending')
        return super().create(validated_data)
