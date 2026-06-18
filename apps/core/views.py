from rest_framework import permissions, viewsets

from .models import SalonInfo, WorkingHours, SalonSettings
from .serializers import SalonInfoSerializer, WorkingHoursSerializer, SalonSettingsSerializer


class SalonInfoViewSet(viewsets.ModelViewSet):
	queryset = SalonInfo.objects.all().order_by('-created_at')
	serializer_class = SalonInfoSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	search_fields = ['name', 'city', 'state']
	ordering_fields = ['name', 'created_at', 'updated_at']

	def get_queryset(self):
		queryset = super().get_queryset()
		is_active = self.request.query_params.get('is_active')
		if is_active is not None:
			queryset = queryset.filter(is_active=is_active.lower() == 'true')
		return queryset


class WorkingHoursViewSet(viewsets.ModelViewSet):
	queryset = WorkingHours.objects.all().order_by('day')
	serializer_class = WorkingHoursSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	ordering_fields = ['day']


class SalonSettingsViewSet(viewsets.ModelViewSet):
	queryset = SalonSettings.objects.all().order_by('-updated_at')
	serializer_class = SalonSettingsSerializer
	permission_classes = [permissions.IsAdminUser]
	ordering_fields = ['updated_at']
