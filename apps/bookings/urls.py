from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TimeSlotViewSet, BookingViewSet

app_name = 'bookings'

router = DefaultRouter()
router.register(r'time-slots', TimeSlotViewSet, basename='time-slots')
router.register(r'bookings', BookingViewSet, basename='bookings')

urlpatterns = router.urls
