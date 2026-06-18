from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, OTPLogViewSet, phone_login, verify_otp, profile, logout

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'otp-logs', OTPLogViewSet, basename='otp-logs')

urlpatterns = [
    # Auth endpoints
    path('phone-login/', phone_login, name='phone-login'),
    path('verify-otp/', verify_otp, name='verify-otp'),
    path('profile/', profile, name='profile'),
    path('logout/', logout, name='logout'),
    # Router endpoints
    *router.urls,
]
