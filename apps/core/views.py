from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import SalonInfo, WorkingHours, SalonSettings, ServiceablePincode
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
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	ordering_fields = ['updated_at']


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_pincode(request):
	pincode = request.query_params.get('pincode', '').strip()
	if not pincode:
		return Response({'serviceable': False})

	serviceable = ServiceablePincode.objects.filter(pincode=pincode, is_active=True).first()
	if not serviceable:
		return Response({'serviceable': False})

	return Response({
		'serviceable': True,
		'delivery_charge': f"{serviceable.delivery_charge:.2f}",
		'area_name': serviceable.area_name,
		'city': serviceable.city,
	})
