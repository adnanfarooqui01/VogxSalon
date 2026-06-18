from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.services.models import Service

User = get_user_model()


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


class Booking(models.Model):
    """Customer service bookings"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='bookings')
    booking_date = models.DateField()
    booking_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-booking_date', '-booking_time']
    
    def __str__(self):
        return f"{self.user.name} - {self.service.name} ({self.booking_date})"
