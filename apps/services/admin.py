from django.contrib import admin
from .models import ServiceCategory, Service


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active', 'created_at')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'duration_minutes', 'is_active', 'created_at')
    search_fields = ('name', 'category__name')
    list_filter = ('category', 'is_active', 'price', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
