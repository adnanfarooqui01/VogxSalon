from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BookingGroupViewSet, TimeSlotViewSet, BookingViewSet

app_name = 'bookings'

router = DefaultRouter()
router.register(r'time-slots', TimeSlotViewSet, basename='time-slots')
router.register(r'bookings', BookingViewSet, basename='bookings')
router.register(r'booking-groups', BookingGroupViewSet, basename='booking-groups')

urlpatterns = router.urls
