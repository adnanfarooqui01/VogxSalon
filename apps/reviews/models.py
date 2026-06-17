from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.bookings.models import Booking
from apps.services.models import Service

User = get_user_model()


class Review(models.Model):
    """Customer reviews for services"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='review')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 to 5'
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)  # Only verified purchasers
    
    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['user', 'service', 'booking']
    
    def __str__(self):
        return f"{self.user.name} - {self.service.name} ({self.rating}★)"
