from django.contrib import admin
from .models import SalonInfo, WorkingHours, SalonSettings, ServiceablePincode


@admin.register(SalonInfo)
class SalonInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'phone', 'email', 'is_active')
    search_fields = ('name', 'city', 'phone', 'email')
    list_filter = ('is_active', 'city', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'latitude', 'longitude')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'tagline', 'description')
        }),
        ('Contact & Location', {
            'fields': ('phone', 'email', 'address', 'city', 'state', 'zip_code', 'latitude', 'longitude')
        }),
        ('Media', {
            'fields': ('logo', 'banner_image')
        }),
        ('Social & Web', {
            'fields': ('website', 'instagram', 'facebook')
        }),
        ('Details', {
            'fields': ('total_employees', 'established_year', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ('day', 'opening_time', 'closing_time', 'is_closed')
    list_filter = ('is_closed',)
    ordering = ('day',)


@admin.register(SalonSettings)
class SalonSettingsAdmin(admin.ModelAdmin):
    list_display = ('advance_booking_days', 'min_booking_notice_hours', 'currency', 'timezone')
    readonly_fields = ('updated_at',)


@admin.register(ServiceablePincode)
class ServiceablePincodeAdmin(admin.ModelAdmin):
    list_display = ('pincode', 'area_name', 'city', 'delivery_charge', 'is_active')
    list_editable = ('delivery_charge', 'is_active')
    search_fields = ('pincode', 'area_name', 'city')
    list_filter = ('is_active', 'city')
