from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, OTPLogViewSet

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'otp-logs', OTPLogViewSet, basename='otp-logs')

urlpatterns = router.urls
