from rest_framework import serializers

from .models import SalonInfo, WorkingHours, SalonSettings


class SalonInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalonInfo
        fields = [
            'id',
            'name',
            'tagline',
            'description',
            'logo',
            'banner_image',
            'phone',
            'email',
            'address',
            'city',
            'state',
            'zip_code',
            'latitude',
            'longitude',
            'website',
            'instagram',
            'facebook',
            'total_employees',
            'established_year',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkingHoursSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = WorkingHours
        fields = ['id', 'day', 'day_name', 'opening_time', 'closing_time', 'is_closed']
        read_only_fields = ['id', 'day_name']


class SalonSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalonSettings
        fields = [
            'id',
            'advance_booking_days',
            'min_booking_notice_hours',
            'cancellation_deadline_hours',
            'max_bookings_per_slot',
            'currency',
            'timezone',
            'enable_notifications',
            'enable_online_payment',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']
