from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SalonInfoViewSet, WorkingHoursViewSet, SalonSettingsViewSet

app_name = 'core'

router = DefaultRouter()
router.register(r'', SalonInfoViewSet, basename='salon-info')
router.register(r'working-hours', WorkingHoursViewSet, basename='working-hours')
router.register(r'salon-settings', SalonSettingsViewSet, basename='salon-settings')

urlpatterns = router.urls
