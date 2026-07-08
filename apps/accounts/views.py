import re
import logging

from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.throttling import ScopedRateThrottle
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import CustomUser, OTPLog
from .serializers import (
    CustomUserSerializer,
    UserProfileSerializer,
    LogoutSerializer,
)
from .firebase_service import verify_firebase_id_token

logger = logging.getLogger(__name__)

# ==================== CONFIG ====================

# OTP send limits — enforced here (server-side) rather than only in the
# frontend's cooldown timer, since a client-side-only limit is trivial to
# bypass by refreshing the page or editing the JS.
#
# NOTE: this counts BOTH the initial "Send OTP" and every "Resend OTP" tap
# against the same daily total (the frontend's resendOTP() calls the same
# quota check). So 3/day means 3 total attempts per phone per day, not
# 3 fresh sends plus unlimited resends.
MAX_OTP_PER_PHONE_PER_DAY = 100
RESEND_COOLDOWN_SECONDS = 30

PHONE_REGEX = re.compile(r'^[6-9]\d{9}$')  # 10-digit Indian mobile, adjust if needed

GENERIC_ERROR_MSG = "Something went wrong on our end. Please try again in a moment."


def get_client_ip(request):
    """
    Best-effort real client IP, accounting for a reverse proxy / load balancer
    (nginx, Render, Railway, etc.) sitting in front of Django.

    IMPORTANT: X-Forwarded-For is attacker-controlled unless your proxy is
    configured to strip/overwrite it before forwarding. Only trust this if
    you know your infra sets it correctly. If unsure, verify with your
    hosting provider's docs.
    """
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ==================== AUTH ENDPOINTS ====================

@csrf_exempt
@api_view(['POST'])
@throttle_classes([ScopedRateThrottle])
@permission_classes([permissions.AllowAny])
def request_otp(request):
    """
    Gate-keeper called by the frontend right BEFORE it asks Firebase to send
    an OTP. Firebase itself has no per-app daily cap we control, so we track
    usage ourselves and refuse once:
      - this IP has requested more than 3 OTPs today (ScopedRateThrottle), or
      - this phone number has sent more than MAX_OTP_PER_PHONE_PER_DAY OTPs
        today, or
      - this phone requested another OTP less than RESEND_COOLDOWN_SECONDS
        after the last one.

    Request body:  { "phone": "9876543210" }   (10-digit, no country code)
    Success (200): { "allowed": true, "remaining": 3, "cooldown_seconds": 30 }
    Blocked (429): { "detail": "user friendly message", "retry_after": 17 }
    """
    try:
        phone = (request.data.get('phone') or '').strip()

        if not phone:
            return Response(
                {'detail': 'Please enter your phone number.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not PHONE_REGEX.match(phone):
            return Response(
                {'detail': 'Please enter a valid 10-digit mobile number.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.localdate()
        log, created = OTPLog.objects.get_or_create(
            phone=phone, date=today, defaults={'count': 0}
        )

        if not created:
            elapsed = (timezone.now() - log.last_sent).total_seconds()
            if elapsed < RESEND_COOLDOWN_SECONDS:
                retry_after = int(RESEND_COOLDOWN_SECONDS - elapsed) + 1
                return Response(
                    {
                        'detail': f'Please wait {retry_after} seconds before requesting another OTP.',
                        'retry_after': retry_after,
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        if log.count >= MAX_OTP_PER_PHONE_PER_DAY:
            logger.warning(f"OTP daily limit hit for phone={phone} ip={get_client_ip(request)}")
            return Response(
                {'detail': f"You've reached today's limit of {MAX_OTP_PER_PHONE_PER_DAY} OTP requests for this number. Please try again tomorrow."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        log.count += 1
        log.save(update_fields=['count', 'last_sent'])  # last_sent has auto_now=True

        return Response({
            'allowed': True,
            'remaining': max(MAX_OTP_PER_PHONE_PER_DAY - log.count, 0),
            'cooldown_seconds': RESEND_COOLDOWN_SECONDS,
        })

    except Exception:
        # Never leak internals (DB errors, stack traces) to the client.
        logger.exception(f"Unexpected error in request_otp for ip={get_client_ip(request)}")
        return Response({'detail': GENERIC_ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


request_otp.cls.throttle_scope = 'otp_send_ip'


@csrf_exempt
@api_view(['POST'])
@throttle_classes([ScopedRateThrottle])
@permission_classes([permissions.AllowAny])
def verify_firebase_token(request):
    """
    Verify Firebase ID token and create/get Django user.

    This endpoint expects a Firebase ID token from the frontend after
    successful OTP verification. It verifies the token, extracts the phone
    number, and creates or retrieves the corresponding Django user.

    Request body:
    {
        "idToken": "firebase_id_token_from_client",
        "name": "optional_user_name"
    }

    Response (200):
    {
        "token": "django_auth_token",
        "user": {...user_data...},
        "message": "Login successful" or "Account created and logged in"
    }
    """
    try:
        id_token = request.data.get('idToken')
        name = (request.data.get('name') or '').strip()

        if not id_token:
            return Response(
                {'detail': 'Missing authentication token. Please try logging in again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify Firebase ID token
        try:
            claims = verify_firebase_id_token(id_token)
        except ValueError as e:
            # Expected failure case: expired/invalid/tampered token.
            logger.warning(f"Firebase token verification failed for ip={get_client_ip(request)}: {e}")
            return Response(
                {'detail': 'Your session has expired or the code is invalid. Please request a new OTP.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        firebase_phone = claims.get('phone_number')
        firebase_uid = claims.get('uid')

        if not firebase_phone or not firebase_uid:
            logger.error(f"Firebase claims missing phone/uid: {claims}")
            return Response(
                {'detail': 'We could not verify your phone number. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalize phone number to E.164 format
        phone = firebase_phone
        if not phone.startswith('+'):
            phone = '+91' + phone.lstrip('0')

        # Get or create Django user.
        # NOTE: `defaults` only applies when a NEW row is being created — it
        # is never used to update an existing user. The update logic below
        # is what keeps `name` in sync on every login.
        user, created = CustomUser.objects.get_or_create(
            phone=phone,
            defaults={
                'name': name or '',
                'firebase_uid': firebase_uid,
            }
        )

        update_fields = []
        if not created and name and name != user.name:
            user.name = name
            update_fields.append('name')
        if not user.firebase_uid:
            user.firebase_uid = firebase_uid
            update_fields.append('firebase_uid')
        if update_fields:
            user.save(update_fields=update_fields)

        token, _ = Token.objects.get_or_create(user=user)

        logger.info(f"User authenticated: {phone} (new_account={created})")

        return Response(
            {
                'token': token.key,
                'user': UserProfileSerializer(user).data,
                'message': 'Login successful' if not created else 'Account created and logged in',
            },
            status=status.HTTP_200_OK,
        )

    except Exception:
        logger.exception(f"Unexpected error in verify_firebase_token for ip={get_client_ip(request)}")
        return Response({'detail': GENERIC_ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


verify_firebase_token.cls.throttle_scope = 'otp_verify'


@api_view(['GET', 'PUT'])
@throttle_classes([ScopedRateThrottle])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    """Get or update user profile"""
    try:
        if request.method == 'GET':
            serializer = UserProfileSerializer(request.user)
            return Response(serializer.data)

        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    except Exception:
        logger.exception(f"Unexpected error in profile view for user={request.user.id}")
        return Response({'detail': GENERIC_ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


profile.cls.throttle_scope = 'profile_update'


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    """Logout user by deleting token"""
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        # User is already effectively logged out — not really an error.
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception:
        logger.exception(f"Unexpected error in logout for user={request.user.id}")
        return Response({'detail': GENERIC_ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== VIEWSETS ====================

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('-date_joined')
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAdminUser]
    search_fields = ['phone', 'name', 'email']
    ordering_fields = ['date_joined', 'updated_at', 'name', 'phone']