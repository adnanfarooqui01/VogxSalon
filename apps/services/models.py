from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class ServiceCategory(models.Model):
    """Service categories for salon services"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Service Category'
        verbose_name_plural = 'Service Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Service(models.Model):
    """Individual salon services"""
    
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name='services')
    name = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    duration_minutes = models.PositiveIntegerField(help_text='Service duration in minutes')
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} (${self.price})"
