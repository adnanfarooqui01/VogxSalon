from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import logging

from .models import CustomUser
from .serializers import (
    CustomUserSerializer,
    UserProfileSerializer,
    LogoutSerializer,
)
from .firebase_service import verify_firebase_id_token

logger = logging.getLogger(__name__)


# ==================== AUTH ENDPOINTS ====================

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_firebase_token(request):
    """
    Verify Firebase ID token and create/get Django user.
    
    This endpoint expects a Firebase ID token from the frontend after successful
    OTP verification. It verifies the token, extracts the phone number, and creates
    or retrieves the corresponding Django user.
    
    Request body:
    {
        "idToken": "firebase_id_token_from_client",
        "name": "optional_user_name"
    }
    
    Response:
    {
        "token": "django_auth_token",
        "user": {...user_data...},
        "message": "Login successful" or "Account created and logged in"
    }
    """
    try:
        id_token = request.data.get('idToken')
        name = request.data.get('name', '')
        
        if not id_token:
            return Response(
                {'detail': 'idToken is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify Firebase ID token
        claims = verify_firebase_id_token(id_token)
        
        # Extract phone number from Firebase claims
        firebase_phone = claims.get('phone_number')
        firebase_uid = claims.get('uid')
        
        if not firebase_phone:
            return Response(
                {'detail': 'No phone number in Firebase token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Normalize phone number to E.164 format
        phone = firebase_phone
        if not phone.startswith('+'):
            phone = '+91' + phone.lstrip('0')
        
        # Get or create Django user
        user, created = CustomUser.objects.get_or_create(
            phone=phone,
            defaults={
                'name': name or phone,
                'firebase_uid': firebase_uid,  # Store Firebase UID for reference
            }
        )
        
        # Update Firebase UID if not already set
        if not user.firebase_uid:
            user.firebase_uid = firebase_uid
            user.save()
        
        # Create or get Django auth token
        token, _ = Token.objects.get_or_create(user=user)
        
        logger.info(f"✓ User authenticated: {phone}")
        
        return Response(
            {
                'token': token.key,
                'user': UserProfileSerializer(user).data,
                'message': 'Login successful' if not created else 'Account created and logged in',
                'firebase_uid': firebase_uid,
            },
            status=status.HTTP_200_OK
        )
        
    except ValueError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        return Response(
            {'detail': str(e)},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    except Exception as e:
        logger.error(f"Error in token verification: {str(e)}")
        return Response(
            {'detail': 'Authentication failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
