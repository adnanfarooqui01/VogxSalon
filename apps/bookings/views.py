from rest_framework import permissions, viewsets

from .models import TimeSlot, Booking
from .serializers import TimeSlotSerializer, BookingSerializer


class TimeSlotViewSet(viewsets.ModelViewSet):
	queryset = TimeSlot.objects.select_related('service').all().order_by('date', 'time')
	serializer_class = TimeSlotSerializer
	permission_classes = [permissions.IsAuthenticated]
	search_fields = ['service__name']
	ordering_fields = ['date', 'time', 'created_at']

	def get_queryset(self):
		queryset = super().get_queryset()
		service_id = self.request.query_params.get('service')
		date = self.request.query_params.get('date')
		is_available = self.request.query_params.get('is_available')

		if service_id:
			queryset = queryset.filter(service_id=service_id)
		if date:
			queryset = queryset.filter(date=date)
		if is_available is not None:
			queryset = queryset.filter(is_available=is_available.lower() == 'true')
		return queryset


class BookingViewSet(viewsets.ModelViewSet):
	serializer_class = BookingSerializer
	permission_classes = [permissions.IsAuthenticated]
	search_fields = ['service__name', 'status', 'notes']
	ordering_fields = ['booking_date', 'booking_time', 'created_at', 'updated_at']

	def get_queryset(self):
		queryset = Booking.objects.select_related('user', 'service', 'service__category', 'payment').all().order_by('-booking_date', '-booking_time')

		if not self.request.user.is_staff:
			queryset = queryset.filter(user=self.request.user)

		service_id = self.request.query_params.get('service')
		status = self.request.query_params.get('status')

		if service_id:
			queryset = queryset.filter(service_id=service_id)
		if status:
			queryset = queryset.filter(status=status)
		return queryset
