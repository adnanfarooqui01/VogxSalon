from rest_framework import permissions, viewsets

from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
	serializer_class = PaymentSerializer
	permission_classes = [permissions.IsAuthenticated]
	search_fields = ['transaction_id', 'razorpay_payment_id', 'razorpay_order_id', 'booking__user__name', 'booking__user__phone']
	ordering_fields = ['created_at', 'paid_at', 'amount', 'status']

	def get_queryset(self):
		queryset = Payment.objects.select_related('booking', 'booking__user', 'booking__service').all().order_by('-created_at')

		if not self.request.user.is_staff:
			queryset = queryset.filter(booking__user=self.request.user)

		status = self.request.query_params.get('status')
		payment_method = self.request.query_params.get('payment_method')

		if status:
			queryset = queryset.filter(status=status)
		if payment_method:
			queryset = queryset.filter(payment_method=payment_method)
		return queryset
