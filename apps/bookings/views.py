from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action 

from apps.core.models import SalonSettings, WorkingHours
from .serializers import TimeSlotSerializer, BookingSerializer, BookingCancelSerializer, BookingGroupSerializer, BookingGroupCreateSerializer
from .models import TimeSlot, Booking, BookingGroup


class TimeSlotViewSet(viewsets.ModelViewSet):
	queryset = TimeSlot.objects.select_related('service').all().order_by('date', 'time')
	serializer_class = TimeSlotSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	search_fields = ['service__name']
	ordering_fields = ['date', 'time', 'created_at']

	def list(self, request, *args, **kwargs):
		query_params = request.query_params
		service_id = query_params.get('service')
		requested_date = query_params.get('date')

		if requested_date:
			if not service_id:
				return Response([])

			try:
				selected_date = datetime.strptime(requested_date, '%Y-%m-%d').date()
			except ValueError:
				return Response([])

			today = timezone.localdate()
			settings = SalonSettings.objects.first()
			advance_days = settings.advance_booking_days if settings else 3
			if advance_days is None:
				advance_days = 3

			if selected_date < today or selected_date > today + timedelta(days=advance_days):
				return Response([])

			try:
				working_hours = WorkingHours.objects.get(day=selected_date.weekday())
			except WorkingHours.DoesNotExist:
				return Response([])

			if working_hours.is_closed:
				return Response([])

			opening_time = working_hours.opening_time
			closing_time = working_hours.closing_time
			if opening_time >= closing_time:
				return Response([])

			max_bookings = settings.max_bookings_per_slot if settings else 1
			current_datetime = timezone.localtime()
			min_notice = timedelta(hours=settings.min_booking_notice_hours) if settings else timedelta(hours=0)
			min_allowed = current_datetime + min_notice
			slots = []
			start_datetime = timezone.make_aware(datetime.combine(selected_date, opening_time), timezone.get_current_timezone())
			end_datetime = timezone.make_aware(datetime.combine(selected_date, closing_time), timezone.get_current_timezone())

			while start_datetime + timedelta(hours=1) <= end_datetime:
				if start_datetime < min_allowed:
					start_datetime += timedelta(hours=1)
					continue

				booking_count = Booking.objects.filter(
					service_id=service_id,
					booking_date=selected_date,
					booking_time=start_datetime.time(),
				).exclude(status__in=['cancelled']).count()

				if booking_count < max_bookings:
					slot = TimeSlot(
						service_id=service_id,
						date=selected_date,
						time=start_datetime.time(),
						is_available=True,
					)
					slots.append(slot)

				start_datetime += timedelta(hours=1)

			serializer = self.get_serializer(slots, many=True)
			return Response(serializer.data)

		return super().list(request, *args, **kwargs)

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
	
	@action(detail=True, methods=['post'])
	def cancel(self, request, pk=None):
		booking = self.get_object()

		if booking.status != 'confirmed':
			return Response(
				{'detail': 'Only confirmed bookings can be cancelled.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

		serializer = BookingCancelSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		booking.status = 'cancelled'
		booking.cancellation_reason = serializer.validated_data['reason']
		booking.cancellation_note = serializer.validated_data.get('note', '')
		booking.cancelled_at = timezone.now()
		booking.save(update_fields=['status', 'cancellation_reason', 'cancellation_note', 'cancelled_at', 'updated_at'])

		return Response(BookingSerializer(booking, context={'request': request}).data)
	


class BookingGroupViewSet(viewsets.ModelViewSet):
    serializer_class = BookingGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ['booking_date', 'created_at']

    def get_queryset(self):
        queryset = BookingGroup.objects.prefetch_related('bookings__service').select_related('user', 'payment').all().order_by('-created_at')
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = BookingGroupCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(BookingGroupSerializer(group).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        group = self.get_object()
        if group.status != 'confirmed':
            return Response({'detail': 'Only confirmed bookings can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = BookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group.status = 'cancelled'
        group.cancellation_reason = serializer.validated_data['reason']
        group.cancellation_note = serializer.validated_data.get('note', '')
        group.cancelled_at = timezone.now()
        group.save()
        group.bookings.update(status='cancelled')

        return Response(BookingGroupSerializer(group).data)