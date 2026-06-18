from rest_framework import permissions, viewsets

from .models import CustomUser, OTPLog
from .serializers import CustomUserSerializer, OTPLogSerializer


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
