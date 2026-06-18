from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.utils import timezone
from datetime import timedelta
import random

from .models import CustomUser, OTPLog
from .serializers import (
    CustomUserSerializer,
    OTPLogSerializer,
    PhoneLoginSerializer,
    VerifyOTPSerializer,
    UserProfileSerializer,
    LogoutSerializer,
)

# Temporary in-memory OTP storage for development
# In production, use Redis or Celery
OTP_STORAGE = {}


# ==================== AUTH ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def phone_login(request):
    """Request OTP for phone login"""
    serializer = PhoneLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    phone = serializer.validated_data['phone']
    
    # Check OTP limit (max 3 per day)
    today = timezone.now().date()
    otp_log, created = OTPLog.objects.get_or_create(phone=phone, date=today)
    
    if otp_log.count >= 3:
        return Response(
            {'detail': 'Maximum OTP requests exceeded. Try again tomorrow.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Generate random 6-digit OTP
    otp = str(random.randint(100000, 999999))
    
    # Store OTP in memory (with 5-minute expiry)
    OTP_STORAGE[phone] = {
        'otp': otp,
        'expires_at': timezone.now() + timedelta(minutes=5)
    }
    
    # Increment OTP request count
    otp_log.count += 1
    otp_log.save()
    
    # TODO: Send OTP via SMS (Firebase/Twilio)
    # For now, return in response for testing
    return Response(
        {
            'phone': phone,
            'message': 'OTP sent successfully',
            'otp': otp,  # REMOVE IN PRODUCTION
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp(request):
    """Verify OTP and login user"""
    serializer = VerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    phone = serializer.validated_data['phone']
    otp = serializer.validated_data['otp']
    name = serializer.validated_data.get('name', '')
    
    # Verify OTP from storage
    otp_data = OTP_STORAGE.get(phone)
    
    if not otp_data:
        return Response(
            {'detail': 'OTP expired or not found. Request a new OTP.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if OTP is expired
    if timezone.now() > otp_data['expires_at']:
        del OTP_STORAGE[phone]
        return Response(
            {'detail': 'OTP expired. Request a new OTP.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify OTP matches
    if otp_data['otp'] != otp:
        return Response(
            {'detail': 'Invalid OTP'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Clear OTP from storage
    del OTP_STORAGE[phone]
    
    # Get or create user
    user, created = CustomUser.objects.get_or_create(
        phone=phone,
        defaults={'name': name or phone}
    )
    
    # Create or get token
    token, _ = Token.objects.get_or_create(user=user)
    
    return Response(
        {
            'token': token.key,
            'user': UserProfileSerializer(user).data,
            'message': 'Login successful' if not created else 'Account created and logged in'
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    """Get or update user profile"""
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    """Logout user by deleting token"""
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )
    except Token.DoesNotExist:
        return Response(
            {'detail': 'No token found'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ==================== VIEWSETS ====================

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('-date_joined')
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAdminUser]
    search_fields = ['phone', 'name', 'email']
    ordering_fields = ['date_joined', 'updated_at', 'name', 'phone']


class OTPLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OTPLog.objects.all().order_by('-last_sent')
    serializer_class = OTPLogSerializer
    permission_classes = [permissions.IsAdminUser]
    search_fields = ['phone']
    ordering_fields = ['date', 'count', 'last_sent']
