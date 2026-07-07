from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.services.models import Service, Package

User = get_user_model()

BOOKING_TYPE_CHOICES = [
    ('salon', 'In Salon'),
    ('home', 'Home Visit'),
]

CANCELLATION_REASON_CHOICES = [
    ('change_of_plans', 'Change of plans'),
    ('booked_wrong_slot', 'Booked wrong date/time'),
    ('found_better_price', 'Found a better price elsewhere'),
    ('professional_unavailable', 'Professional/slot unavailable'),
    ('other', 'Other'),
]


class TimeSlot(models.Model):
    """Available time slots for services"""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['service', 'date', 'time']
        verbose_name = 'Time Slot'
        verbose_name_plural = 'Time Slots'
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.service.name} - {self.date} {self.time}"


class BookingGroup(models.Model):
    """Represents one checkout — groups multiple service bookings into one bill"""
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booking_groups')
    booking_date = models.DateField()
    booking_time = models.TimeField()
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE_CHOICES, default='salon')

    pincode = models.CharField(max_length=10, blank=True, null=True)
    house_number = models.CharField(max_length=50, blank=True, null=True)
    street_area = models.CharField(max_length=255, blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    convenience_fee = models.DecimalField(max_digits=10, decimal_places=2, default=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    is_paid = models.BooleanField(default=False)

    cancellation_reason = models.CharField(max_length=30, choices=CANCELLATION_REASON_CHOICES, blank=True, null=True)
    cancellation_note = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Booking Group'
        verbose_name_plural = 'Booking Groups'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.user.name} ({self.booking_date})"


class Booking(models.Model):
    """Customer service bookings"""
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    BOOKING_TYPE_CHOICES = BOOKING_TYPE_CHOICES
    CANCELLATION_REASON_CHOICES = CANCELLATION_REASON_CHOICES

    group = models.ForeignKey(BookingGroup, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='bookings')
    booking_date = models.DateField()
    booking_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE_CHOICES, default='salon')

    group = models.ForeignKey(BookingGroup, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='bookings')
    package = models.ForeignKey(
        Package, on_delete=models.SET_NULL, related_name='bookings',
        null=True, blank=True,
        help_text='Set when this service-booking came from a Package rather than being booked standalone.'
    )

    pincode = models.CharField(max_length=10, blank=True, null=True)
    house_number = models.CharField(max_length=50, blank=True, null=True)
    street_area = models.CharField(max_length=255, blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)

    notes = models.TextField(blank=True)
    is_paid = models.BooleanField(default=False)

    cancellation_reason = models.CharField(max_length=30, choices=CANCELLATION_REASON_CHOICES, blank=True, null=True)
    cancellation_note = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-booking_date', '-booking_time']

    def __str__(self):
        return f"{self.user.name} - {self.service.name} ({self.booking_date})"
    
