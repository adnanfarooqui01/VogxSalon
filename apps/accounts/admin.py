from django.contrib import admin
from .models import CustomUser, OTPLog


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('phone', 'name', 'email', 'is_staff', 'is_employee', 'is_active', 'date_joined')
    search_fields = ('phone', 'name', 'email')
    list_filter = ('is_active', 'is_staff', 'is_employee', 'date_joined')
    ordering = ('-date_joined',)


@admin.register(OTPLog)
class OTPLogAdmin(admin.ModelAdmin):
    list_display = ('phone', 'date', 'count', 'last_sent')
    search_fields = ('phone',)
    list_filter = ('date',)
