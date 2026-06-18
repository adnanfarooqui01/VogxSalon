from rest_framework import permissions, viewsets

from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
	queryset = Review.objects.select_related('user', 'service', 'booking').all().order_by('-created_at')
	serializer_class = ReviewSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	search_fields = ['title', 'comment', 'service__name', 'user__name']
	ordering_fields = ['created_at', 'rating', 'helpful_count']

	def get_queryset(self):
		queryset = super().get_queryset()
		service_id = self.request.query_params.get('service')
		rating = self.request.query_params.get('rating')
		verified = self.request.query_params.get('verified')

		if service_id:
			queryset = queryset.filter(service_id=service_id)
		if rating:
			queryset = queryset.filter(rating=rating)
		if verified is not None:
			queryset = queryset.filter(is_verified=verified.lower() == 'true')
		return queryset
