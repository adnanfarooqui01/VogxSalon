from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import logging

from .models import CustomUser, OTPLog
from .serializers import (
    CustomUserSerializer,
    UserProfileSerializer,
    LogoutSerializer,
)
from .firebase_service import verify_firebase_id_token

logger = logging.getLogger(__name__)

# OTP send limits — enforced here (server-side) rather than only in the
# frontend's cooldown timer, since a client-side-only limit is trivial to
# bypass by refreshing the page or editing the JS.
MAX_OTP_PER_PHONE_PER_DAY = 50
RESEND_COOLDOWN_SECONDS = 30


# ==================== AUTH ENDPOINTS ====================

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def request_otp(request):
    """
    Gate-keeper called by the frontend right BEFORE it asks Firebase to send
    an OTP. Firebase itself has no per-app daily cap we control, so we track
    usage ourselves via OTPLog and refuse once a phone number has:
      - sent more than MAX_OTP_PER_PHONE_PER_DAY OTPs today, or
      - requested another OTP less than RESEND_COOLDOWN_SECONDS after the
        last one.

    Request body:  { "phone": "9876543210" }   (10-digit, no country code)
    Success (200): { "allowed": true, "remaining": 3, "cooldown_seconds": 30 }
    Blocked (429): { "detail": "...", "retry_after": 17 }
    """
    phone = (request.data.get('phone') or '').strip()
    if not phone:
        return Response({'detail': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

    today = timezone.localdate()
    log, created = OTPLog.objects.get_or_create(phone=phone, date=today, defaults={'count': 0})

    if not created:
        elapsed = (timezone.now() - log.last_sent).total_seconds()
        if elapsed < RESEND_COOLDOWN_SECONDS:
            retry_after = int(RESEND_COOLDOWN_SECONDS - elapsed) + 1
            return Response(
                {'detail': f'Please wait {retry_after}s before requesting another OTP.', 'retry_after': retry_after},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

    if log.count >= MAX_OTP_PER_PHONE_PER_DAY:
        return Response(
            {'detail': f"You've reached today's OTP limit ({MAX_OTP_PER_PHONE_PER_DAY}). Please try again tomorrow."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    log.count += 1
    log.save(update_fields=['count', 'last_sent'])  # last_sent has auto_now=True

    return Response({
        'allowed': True,
        'remaining': max(MAX_OTP_PER_PHONE_PER_DAY - log.count, 0),
        'cooldown_seconds': RESEND_COOLDOWN_SECONDS,
    })


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
        
        # Get or create Django user.
        # NOTE: `defaults` only applies when a NEW row is being created —
        # it is never used to update an existing user. So the update logic
        # below is what keeps `name` in sync on every login, not this call.
        user, created = CustomUser.objects.get_or_create(
            phone=phone,
            defaults={
                'name': name or '',
                'firebase_uid': firebase_uid,
            }
        )

        # Keep the profile in sync with whatever was typed in the login
        # popup this time — this also self-heals any older account that
        # got stuck with name == phone from before this fix.
        update_fields = []
        if not created and name and name != user.name:
            user.name = name
            update_fields.append('name')
        if not user.firebase_uid:
            user.firebase_uid = firebase_uid
            update_fields.append('firebase_uid')
        if update_fields:
            user.save(update_fields=update_fields)
        
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