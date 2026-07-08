from rest_framework import serializers
from apps.core.models import ServiceablePincode
from apps.services.models import Service, Package
from django.db import transaction 
from .models import TimeSlot, Booking, BookingGroup
from .services import create_booking_group

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
    package_name = serializers.CharField(source='package.name', read_only=True, default=None)
    package_price = serializers.DecimalField(source='package.package_price', max_digits=10, decimal_places=2, read_only=True, default=None)

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'user_name',
            'service',
            'service_name',
            'service_price',
            'package',
            'package_name',
            'package_price',
            'booking_date',
            'booking_time',
            'duration_minutes',
            'total_price',
            'status',
            'booking_type',
            'pincode',
            'house_number',
            'street_area',
            'landmark',
            'notes',
            'is_paid',
            'payment_status',
            'cancellation_reason',
            'cancellation_note',
            'cancelled_at',
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
            'package',
            'package_name',
            'package_price',
            'duration_minutes',
            'total_price',
            'status',
            'is_paid',
            'payment_status',
            'cancellation_reason',
            'cancellation_note',
            'cancelled_at',
            'created_at',
            'updated_at',
            'completed_at',
        ]

    def get_payment_status(self, obj):
        payment = getattr(obj, 'payment', None)
        return payment.status if payment else None

    def validate(self, attrs):
        booking_type = attrs.get('booking_type')
        pincode = attrs.get('pincode')

        if self.instance is not None:
            booking_type = booking_type or self.instance.booking_type
            pincode = pincode or self.instance.pincode

        if booking_type == 'home':
            if not pincode:
                raise serializers.ValidationError({'pincode': 'Please provide a pincode for home service.'})

            serviceable = ServiceablePincode.objects.filter(pincode=pincode, is_active=True).first()
            if not serviceable:
                raise serializers.ValidationError({'pincode': "Sorry, we don't currently service this pincode yet."})

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        service = validated_data['service']
        validated_data['user'] = request.user
        validated_data['duration_minutes'] = service.duration_minutes
        
        # Calculate total price (service price + fees handled in frontend/passed here)
        # Usually backend should re-calculate for security
        validated_data['total_price'] = service.price
        if validated_data.get('booking_type') == 'home':
            pincode = validated_data.get('pincode')
            serviceable = ServiceablePincode.objects.filter(pincode=pincode, is_active=True).first()
            delivery_charge = serviceable.delivery_charge if serviceable else 0
            validated_data['total_price'] += delivery_charge
        validated_data['total_price'] += 20  # Convenience fee
        
        validated_data.setdefault('status', 'confirmed')
        return super().create(validated_data)

class BookingCancelSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=Booking.CANCELLATION_REASON_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate(self, data):
        if data['reason'] == 'other' and not data.get('note', '').strip():
            raise serializers.ValidationError({'note': 'Please tell us a bit more about why you are cancelling.'})
        return data
    


class BookingGroupCreateSerializer(serializers.Serializer):
    # Relaxed from allow_empty=False — a checkout can now be packages-only,
    # with no standalone services at all. The combined "must have at least
    # one of service_ids/package_ids" check lives in validate() below.
    service_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    package_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    booking_date = serializers.DateField()
    booking_time = serializers.TimeField()
    booking_type = serializers.ChoiceField(choices=Booking.BOOKING_TYPE_CHOICES)
    pincode = serializers.CharField(required=False, allow_blank=True)
    house_number = serializers.CharField(required=False, allow_blank=True)
    street_area = serializers.CharField(required=False, allow_blank=True)
    landmark = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    # Cart page collects/edits these and keeps the user's profile in sync.
    # Phone is NEVER accepted here — it's the permanent, unique identifier
    # set at login and can't be changed from checkout.
    name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        # Cart must contain at least one service or package.
        if not attrs.get('service_ids') and not attrs.get('package_ids'):
            raise serializers.ValidationError(
                {'service_ids': 'Add at least one service or package before booking.'}
            )

        if attrs['booking_type'] == 'home':
            pincode = attrs.get('pincode')
            if not pincode:
                raise serializers.ValidationError({'pincode': 'Please provide a pincode for home service.'})
            serviceable = ServiceablePincode.objects.filter(pincode=pincode, is_active=True).first()
            if not serviceable:
                raise serializers.ValidationError({'pincode': "Sorry, we don't currently service this pincode yet."})

        # Email is mandatory at booking time — either it's already saved on
        # the profile (from a previous booking) or the cart page must send one.
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        effective_email = (attrs.get('email') or '').strip() or (getattr(user, 'email', '') or '')
        if not effective_email:
            raise serializers.ValidationError({'email': 'Email is required to complete your booking.'})

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        # Sync name/email back onto the profile — same pattern as the
        # login popup, phone is excluded/untouched on purpose.
        name = (validated_data.pop('name', '') or '').strip()
        email = (validated_data.pop('email', '') or '').strip()
        update_fields = []
        if name and name != user.name:
            user.name = name
            update_fields.append('name')
        if email and email != user.email:
            user.email = email
            update_fields.append('email')
        if update_fields:
            user.save(update_fields=update_fields)

        try:
            return create_booking_group(user, validated_data, status='confirmed')
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))


class BookingGroupSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    bookings = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = BookingGroup
        fields = [
            'id', 'user', 'user_name', 'booking_date', 'booking_time', 'booking_type',
            'pincode', 'house_number', 'street_area', 'landmark', 'notes',
            'subtotal', 'service_charge', 'convenience_fee', 'total_price',
            'status', 'is_paid', 'payment_status', 'bookings',
            'cancellation_reason', 'cancellation_note', 'cancelled_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_bookings(self, obj):
        return [
            {
                'id': b.id,
                'service_id': b.service.id,
                'service_name': b.service.name,
                'price': b.total_price,
                'package_id': b.package_id,
                'package_name': b.package.name if b.package_id else None,
                'package_price': b.package.package_price if b.package_id else None,
            }
            for b in obj.bookings.select_related('service', 'package').all()
        ]

    def get_payment_status(self, obj):
        payment = getattr(obj, 'payment', None)
        return payment.status if payment else None