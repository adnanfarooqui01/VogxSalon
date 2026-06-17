"""
URL Configuration for salon_project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.core.urls', namespace='core')),
    path('api/auth/', include('apps.accounts.urls', namespace='accounts')),
    path('api/services/', include('apps.services.urls', namespace='services')),
    path('api/bookings/', include('apps.bookings.urls', namespace='bookings')),
    path('api/payments/', include('apps.payments.urls', namespace='payments')),
    path('api/reviews/', include('apps.reviews.urls', namespace='reviews')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
