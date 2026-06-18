from rest_framework import permissions, viewsets

from .models import ServiceCategory, Service, ServiceStep, Package
from .serializers import ServiceCategorySerializer, ServiceSerializer, ServiceStepSerializer, PackageSerializer


class ServiceCategoryViewSet(viewsets.ModelViewSet):
	queryset = ServiceCategory.objects.all().order_by('order', 'name')
	serializer_class = ServiceCategorySerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	search_fields = ['name', 'description']
	ordering_fields = ['order', 'name', 'created_at', 'updated_at']

	def get_queryset(self):
		queryset = super().get_queryset()
		is_active = self.request.query_params.get('is_active')
		show_on_home = self.request.query_params.get('show_on_home')
		gender = self.request.query_params.get('gender')
		
		if is_active is not None:
			queryset = queryset.filter(is_active=is_active.lower() == 'true')
		if show_on_home is not None:
			queryset = queryset.filter(show_on_home=show_on_home.lower() == 'true')
		if gender:
			queryset = queryset.filter(gender__in=[gender, 'both'])
		
		return queryset


class ServiceViewSet(viewsets.ModelViewSet):
	queryset = Service.objects.select_related('category').prefetch_related('steps').all().order_by('category__name', 'name')
	serializer_class = ServiceSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	search_fields = ['name', 'description', 'category__name']
	ordering_fields = ['name', 'price', 'duration_minutes', 'created_at', 'updated_at']

	def get_queryset(self):
		queryset = super().get_queryset()
		category_id = self.request.query_params.get('category')
		is_available = self.request.query_params.get('is_available')
		service_type = self.request.query_params.get('service_type')
		gender = self.request.query_params.get('gender')

		if category_id:
			queryset = queryset.filter(category_id=category_id)
		if is_available is not None:
			queryset = queryset.filter(is_available=is_available.lower() == 'true')
		if service_type:
			queryset = queryset.filter(service_type__in=[service_type, 'both'])
		if gender:
			queryset = queryset.filter(category__gender__in=[gender, 'both'])
		
		return queryset


class ServiceStepViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = ServiceStep.objects.all().order_by('service', 'step_number')
	serializer_class = ServiceStepSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filterset_fields = ['service']


class PackageViewSet(viewsets.ModelViewSet):
	queryset = Package.objects.prefetch_related('services').all().order_by('-created_at')
	serializer_class = PackageSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	search_fields = ['name', 'description']
	ordering_fields = ['package_price', 'created_at', 'updated_at']

	def get_queryset(self):
		queryset = super().get_queryset()
		is_available = self.request.query_params.get('is_available')
		gender = self.request.query_params.get('gender')

		if is_available is not None:
			queryset = queryset.filter(is_available=is_available.lower() == 'true')
		if gender:
			queryset = queryset.filter(gender__in=[gender, 'both'])
		
		return queryset
