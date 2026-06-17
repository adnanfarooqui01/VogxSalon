from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'status', 'payment_method', 'created_at', 'paid_at')
    search_fields = ('booking__user__phone', 'transaction_id', 'razorpay_payment_id')
    list_filter = ('status', 'payment_method', 'created_at', 'paid_at')
    readonly_fields = ('created_at', 'updated_at', 'transaction_id')
    fieldsets = (
        ('Payment Info', {
            'fields': ('booking', 'amount', 'transaction_id')
        }),
        ('Payment Details', {
            'fields': ('status', 'payment_method')
        }),
        ('Razorpay', {
            'fields': ('razorpay_payment_id', 'razorpay_order_id', 'razorpay_signature'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
