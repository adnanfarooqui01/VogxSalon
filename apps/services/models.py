from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class ServiceCategory(models.Model):
    """Service categories for salon services"""
    
    GENDER_CHOICES = [
        ('men', 'Men'),
        ('women', 'Women'),
        ('both', 'Both'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='categories/', blank=True, null=True, help_text='Category icon')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='both')
    order = models.IntegerField(default=0, help_text='Order for display on home page')
    is_active = models.BooleanField(default=True)
    show_on_home = models.BooleanField(default=True, help_text='Show this category on home page')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Service Category'
        verbose_name_plural = 'Service Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_gender_display()})"


class Service(models.Model):
    """Individual salon services"""
    
    SERVICE_TYPE_CHOICES = [
        ('home', 'Home Visit'),
        ('salon', 'In Salon'),
        ('both', 'Both'),
    ]
    
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name='services')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    duration_minutes = models.PositiveIntegerField(help_text='Service duration in minutes')
    preview_image = models.ImageField(upload_to='services/preview/', blank=True, null=True, help_text='Used in cards and listing')
    detail_image = models.ImageField(upload_to='services/detail/', blank=True, null=True, help_text='Used in detail page only')
    service_type = models.CharField(max_length=10, choices=SERVICE_TYPE_CHOICES, default='both')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class ServiceStep(models.Model):
    """Steps/Process for a service"""
    
    service = models.ForeignKey(Service, related_name='steps', on_delete=models.CASCADE)
    step_number = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['service', 'step_number']
        verbose_name = 'Service Step'
        verbose_name_plural = 'Service Steps'
    
    def __str__(self):
        return f"{self.service.name} - Step {self.step_number}"


class Package(models.Model):
    """Package of services (bundle deals)"""
    
    GENDER_CHOICES = [
        ('men', 'Men'),
        ('women', 'Women'),
        ('both', 'Both'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    services = models.ManyToManyField(Service, help_text='Services included in this package')
    package_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='both')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'
    
    def __str__(self):
        return f"{self.name} - ₹{self.package_price}"
