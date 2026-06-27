from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, verify_firebase_token, profile, logout

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = [
    # Firebase Phone Authentication endpoint
    path('verify-firebase-token/', verify_firebase_token, name='verify-firebase-token'),
    # User endpoints
    path('profile/', profile, name='profile'),
    path('logout/', logout, name='logout'),
    # Router endpoints
    *router.urls,
]
