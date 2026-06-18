from rest_framework import permissions, viewsets

from .models import ServiceCategory, Service
from .serializers import ServiceCategorySerializer, ServiceSerializer


class ServiceCategoryViewSet(viewsets.ModelViewSet):
	queryset = ServiceCategory.objects.all().order_by('name')
	serializer_class = ServiceCategorySerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	search_fields = ['name', 'description']
	ordering_fields = ['name', 'created_at', 'updated_at']

	def get_queryset(self):
		queryset = super().get_queryset()
		is_active = self.request.query_params.get('is_active')
		if is_active is not None:
			queryset = queryset.filter(is_active=is_active.lower() == 'true')
		return queryset


class ServiceViewSet(viewsets.ModelViewSet):
	queryset = Service.objects.select_related('category').all().order_by('category__name', 'name')
	serializer_class = ServiceSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	search_fields = ['name', 'description', 'category__name']
	ordering_fields = ['name', 'price', 'duration_minutes', 'created_at', 'updated_at']

	def get_queryset(self):
		queryset = super().get_queryset()
		category_id = self.request.query_params.get('category')
		is_active = self.request.query_params.get('is_active')

		if category_id:
			queryset = queryset.filter(category_id=category_id)
		if is_active is not None:
			queryset = queryset.filter(is_active=is_active.lower() == 'true')
		return queryset
