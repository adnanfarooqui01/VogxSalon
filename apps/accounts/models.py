from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class CustomUserManager(BaseUserManager):
    """Custom user manager for phone-based authentication"""
    
    def create_user(self, phone, password=None, **extra_fields):
        """Create and save a regular user"""
        if not phone:
            raise ValueError('Phone number is required')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model using phone number as primary identifier"""
    
    phone = models.CharField(max_length=15, unique=True)
    firebase_uid = models.CharField(max_length=128, blank=True, null=True, unique=True, help_text="Firebase user UID for phone authentication")
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.name} ({self.phone})"


class OTPLog(models.Model):
    """Track OTP requests per phone number per day"""
    
    phone = models.CharField(max_length=15)
    date = models.DateField(auto_now_add=True)
    count = models.IntegerField(default=0)  # Max 3 per day
    last_sent = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['phone', 'date']
        verbose_name = 'OTP Log'
        verbose_name_plural = 'OTP Logs'
    
    def __str__(self):
        return f"{self.phone} - {self.date} ({self.count} requests)"
