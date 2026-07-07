from django.contrib import admin
from .models import BookingGroup, TimeSlot, Booking

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('service', 'date', 'time', 'is_available')
    search_fields = ('service__name', 'date')
    list_filter = ('is_available', 'date', 'service')
    readonly_fields = ('created_at',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'package', 'booking_date', 'booking_time', 'status', 'booking_type', 'is_paid', 'total_price')
    search_fields = ('user__phone', 'user__name', 'service__name', 'package__name', 'id')
    list_filter = ('status', 'booking_type', 'is_paid', 'booking_date', 'created_at', 'package')
    list_editable = ('status', 'is_paid')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    fieldsets = (
        ('Booking Details', {
            'fields': ('user', 'service', 'package', 'booking_date', 'booking_time', 'duration_minutes', 'booking_type')
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
            'fields': ('status', 'notes', 'completed_at', 'cancellation_reason', 'cancellation_note', 'cancelled_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    fields = ('service', 'package', 'total_price', 'status')
    readonly_fields = ('service', 'package', 'total_price', 'status')
    can_delete = False

@admin.register(BookingGroup)
class BookingGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'booking_date', 'booking_time', 'status', 'booking_type', 'is_paid', 'total_price')
    search_fields = ('user__phone', 'user__name', 'id')
    list_filter = ('status', 'booking_type', 'is_paid', 'booking_date')
    list_editable = ('status', 'is_paid')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [BookingInline]
    fieldsets = (
        ('Order Details', {'fields': ('user', 'booking_date', 'booking_time', 'booking_type')}),
        ('Home Visit Address', {'fields': ('pincode', 'house_number', 'street_area', 'landmark'), 'classes': ('collapse',)}),
        ('Billing', {'fields': ('subtotal', 'service_charge', 'convenience_fee', 'total_price', 'is_paid')}),
        ('Status', {'fields': ('status', 'notes', 'cancellation_reason', 'cancellation_note', 'cancelled_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )