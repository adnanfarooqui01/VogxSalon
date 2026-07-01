from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SalonInfoViewSet, WorkingHoursViewSet, SalonSettingsViewSet, check_pincode

app_name = 'core'

router = DefaultRouter()
router.register(r'salon-info', SalonInfoViewSet, basename='salon-info')
router.register(r'working-hours', WorkingHoursViewSet, basename='working-hours')
router.register(r'salon-settings', SalonSettingsViewSet, basename='salon-settings')

urlpatterns = router.urls + [
    path('check-pincode/', check_pincode, name='check-pincode'),
]
