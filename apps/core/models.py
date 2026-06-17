from django.db import models
from django.core.validators import RegexValidator


class SalonInfo(models.Model):
    """Salon information and settings"""
    
    name = models.CharField(max_length=200)
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    logo = models.ImageField(upload_to='salon/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='salon/', blank=True, null=True)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\d{10,15}$', 'Enter valid phone number')]
    )
    email = models.EmailField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    website = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    total_employees = models.PositiveIntegerField(default=0)
    established_year = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Salon Info'
        verbose_name_plural = 'Salon Info'
    
    def __str__(self):
        return self.name


class WorkingHours(models.Model):
    """Salon working hours"""
    
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    day = models.IntegerField(choices=DAY_CHOICES)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_closed = models.BooleanField(default=False)  # For holidays
    
    class Meta:
        verbose_name = 'Working Hours'
        verbose_name_plural = 'Working Hours'
        unique_together = ['day']
    
    def __str__(self):
        return f"{self.get_day_display()} - {self.opening_time} to {self.closing_time}"


class SalonSettings(models.Model):
    """Configurable salon settings"""
    
    advance_booking_days = models.PositiveIntegerField(default=30, help_text='How many days in advance customers can book')
    min_booking_notice_hours = models.PositiveIntegerField(default=24, help_text='Minimum hours notice required for booking')
    cancellation_deadline_hours = models.PositiveIntegerField(default=24, help_text='Hours before appointment to cancel')
    max_bookings_per_slot = models.PositiveIntegerField(default=1)
    currency = models.CharField(max_length=3, default='INR')
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    enable_notifications = models.BooleanField(default=True)
    enable_online_payment = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Salon Settings'
        verbose_name_plural = 'Salon Settings'
    
    def __str__(self):
        return 'Salon Settings'
