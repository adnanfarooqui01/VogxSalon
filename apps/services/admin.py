from django.contrib import admin
from .models import ServiceCategory, Service, ServiceStep, Package


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'order', 'show_on_home', 'is_active', 'created_at')
    list_filter = ('gender', 'show_on_home', 'is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Category Info', {
            'fields': ('name', 'description', 'icon', 'gender', 'order')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'show_on_home')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'duration_minutes', 'service_type', 'is_available', 'created_at')
    list_filter = ('category', 'service_type', 'is_available', 'created_at')
    search_fields = ('name', 'category__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Service Details', {
            'fields': ('name', 'category', 'description', 'price', 'duration_minutes')
        }),
        ('Images', {
            'fields': ('preview_image', 'detail_image'),
            'description': 'Preview image: used in listings. Detail image: used in detail page.'
        }),
        ('Service Type & Availability', {
            'fields': ('service_type', 'is_available')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ServiceStepInline(admin.TabularInline):
    model = ServiceStep
    extra = 1
    fields = ('step_number', 'title', 'description')
    ordering = ('step_number',)


@admin.register(ServiceStep)
class ServiceStepAdmin(admin.ModelAdmin):
    list_display = ('service', 'step_number', 'title')
    list_filter = ('service',)
    search_fields = ('service__name', 'title')
    ordering = ('service', 'step_number')


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'package_price', 'gender', 'is_available', 'created_at')
    list_filter = ('gender', 'is_available', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('services',)
    fieldsets = (
        ('Package Details', {
            'fields': ('name', 'description', 'image', 'package_price', 'gender')
        }),
        ('Services', {
            'fields': ('services',),
            'description': 'Select services included in this package'
        }),
        ('Availability', {
            'fields': ('is_available',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
