from django.contrib import admin
from .models import TimeSlot, Booking

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('service', 'date', 'time', 'is_available')
    search_fields = ('service__name', 'date')
    list_filter = ('is_available', 'date', 'service')
    readonly_fields = ('created_at',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'booking_date', 'booking_time', 'status', 'booking_type', 'is_paid', 'total_price')
    search_fields = ('user__phone', 'user__name', 'service__name', 'id')
    list_filter = ('status', 'booking_type', 'is_paid', 'booking_date', 'created_at')
    list_editable = ('status', 'is_paid')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    fieldsets = (
        ('Booking Details', {
            'fields': ('user', 'service', 'booking_date', 'booking_time', 'duration_minutes', 'booking_type')
        }),
        ('Home Visit Address', {
            'fields': ('pincode', 'house_number', 'street_area', 'landmark'),
            'classes': ('collapse',),
            'description': 'Only applicable for Home Visit bookings'
        }),
        ('Pricing & Payment', {
            'fields': ('total_price', 'is_paid')
        }),
        ('Status', {
            'fields': ('status', 'notes', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )