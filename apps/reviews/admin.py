from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'rating', 'is_verified', 'helpful_count', 'created_at')
    search_fields = ('user__phone', 'service__name', 'title')
    list_filter = ('rating', 'is_verified', 'created_at', 'service')
    readonly_fields = ('created_at', 'updated_at', 'helpful_count')
    fieldsets = (
        ('Review Info', {
            'fields': ('user', 'service', 'booking')
        }),
        ('Rating & Comment', {
            'fields': ('rating', 'title', 'comment')
        }),
        ('Verification', {
            'fields': ('is_verified', 'helpful_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
