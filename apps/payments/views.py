from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from datetime import datetime

from apps.bookings.models import Booking
from .models import Payment
from .serializers import PaymentSerializer, CreateOrderSerializer, VerifyPaymentSerializer
from .razorpay_utils import create_razorpay_order, verify_razorpay_signature, fetch_payment_details


class PaymentViewSet(viewsets.ModelViewSet):
	serializer_class = PaymentSerializer
	permission_classes = [permissions.IsAuthenticated]
	search_fields = ['transaction_id', 'razorpay_payment_id', 'razorpay_order_id', 'booking__user__name', 'booking__user__phone']
	ordering_fields = ['created_at', 'paid_at', 'amount', 'status']

	def get_queryset(self):
		queryset = Payment.objects.select_related('booking', 'booking__user', 'booking__service').all().order_by('-created_at')

		if not self.request.user.is_staff:
			queryset = queryset.filter(booking__user=self.request.user)

		status_param = self.request.query_params.get('status')
		payment_method = self.request.query_params.get('payment_method')

		if status_param:
			queryset = queryset.filter(status=status_param)
		if payment_method:
			queryset = queryset.filter(payment_method=payment_method)
		return queryset


# ==================== CUSTOM PAYMENT ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment_order(request):
	"""
	Create a Razorpay order for a booking
	
	Request body: {
	    "booking_id": 1
	}
	
	Response: {
	    "order_id": "order_xxx",
	    "amount": 1000,
	    "currency": "INR",
	    "key": "rzp_test_xxx",
	    "transaction_id": "TXN-xxx"
	}
	"""
	serializer = CreateOrderSerializer(data=request.data)
	
	if not serializer.is_valid():
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	
	booking_id = serializer.validated_data['booking_id']
	
	try:
		booking = Booking.objects.get(id=booking_id, user=request.user)
	except Booking.DoesNotExist:
		return Response(
			{'detail': 'Booking not found or does not belong to you'},
			status=status.HTTP_404_NOT_FOUND
		)
	
	if booking.status not in ['pending', 'confirmed']:
		return Response(
			{'detail': 'Booking must be in pending or confirmed status for payment'},
			status=status.HTTP_400_BAD_REQUEST
		)
	
	# Check if payment already exists for this booking
	existing_payment = Payment.objects.filter(booking=booking).first()
	if existing_payment and existing_payment.status in ['completed', 'initiated']:
		return Response(
			{'detail': 'Payment already initiated or completed for this booking'},
			status=status.HTTP_400_BAD_REQUEST
		)
	
	# Create or update Payment record
	if existing_payment:
		payment = existing_payment
	else:
		payment = Payment.objects.create(
			booking=booking,
			amount=booking.total_price,
			status='pending',
			payment_method='razorpay'
		)
	
	# Create Razorpay order
	razorpay_order = create_razorpay_order(
		amount=float(booking.total_price),
		receipt=payment.transaction_id,
		notes={
			'booking_id': booking.id,
			'customer_name': booking.user.name,
			'customer_phone': booking.user.phone,
			'service': booking.service.name,
		}
	)
	
	if not razorpay_order:
		return Response(
			{'detail': 'Failed to create Razorpay order'},
			status=status.HTTP_500_INTERNAL_SERVER_ERROR
		)
	
	# Update Payment record with Razorpay order details
	payment.razorpay_order_id = razorpay_order['id']
	payment.status = 'initiated'
	payment.save()
	
	return Response({
		'order_id': razorpay_order['id'],
		'amount': razorpay_order['amount'] / 100,  # Convert back to rupees
		'currency': razorpay_order['currency'],
		'key': 'RAZORPAY_KEY_ID',  # Frontend will fetch from settings
		'transaction_id': payment.transaction_id,
		'payment_id': payment.id,
	}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_payment_order(request):
	"""
	Verify Razorpay payment and confirm booking
	
	Request body: {
	    "razorpay_order_id": "order_xxx",
	    "razorpay_payment_id": "pay_xxx",
	    "razorpay_signature": "signature_xxx"
	}
	
	Response: {
	    "status": "completed",
	    "message": "Payment verified successfully",
	    "booking": {...},
	    "payment": {...}
	}
	"""
	serializer = VerifyPaymentSerializer(data=request.data)
	
	if not serializer.is_valid():
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	
	razorpay_order_id = serializer.validated_data['razorpay_order_id']
	razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
	razorpay_signature = serializer.validated_data['razorpay_signature']
	
	# Verify signature
	if not verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
		return Response(
			{'detail': 'Invalid payment signature'},
			status=status.HTTP_400_BAD_REQUEST
		)
	
	# Find payment record
	try:
		payment = Payment.objects.get(
			razorpay_order_id=razorpay_order_id,
			booking__user=request.user
		)
	except Payment.DoesNotExist:
		return Response(
			{'detail': 'Payment record not found'},
			status=status.HTTP_404_NOT_FOUND
		)
	
	# Use transaction to ensure atomicity
	with transaction.atomic():
		# Update payment record
		payment.razorpay_payment_id = razorpay_payment_id
		payment.razorpay_signature = razorpay_signature
		payment.status = 'completed'
		payment.paid_at = timezone.now()
		payment.save()
		
		# Update booking status
		booking = payment.booking
		booking.status = 'payment_confirmed'
		booking.is_paid = True
		booking.updated_at = timezone.now()
		booking.save()
	
	return Response({
		'status': 'completed',
		'message': 'Payment verified successfully',
		'transaction_id': payment.transaction_id,
		'amount': float(payment.amount),
		'paid_at': payment.paid_at,
		'booking_id': booking.id,
	}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_history(request):
	"""
	Get payment history for current user
	
	Query parameters:
	    - status: Filter by payment status (pending, initiated, completed, failed, refunded)
	    - page: Page number (default: 1)
	    - page_size: Number of items per page (default: 20)
	
	Response: Paginated list of payments
	"""
	from rest_framework.pagination import PageNumberPagination
	
	# Get user's payments
	if request.user.is_staff:
		payments = Payment.objects.all().order_by('-created_at')
	else:
		payments = Payment.objects.filter(booking__user=request.user).order_by('-created_at')
	
	# Filter by status if provided
	status_param = request.query_params.get('status')
	if status_param:
		payments = payments.filter(status=status_param)
	
	# Paginate
	paginator = PageNumberPagination()
	paginator.page_size = int(request.query_params.get('page_size', 20))
	paginated_payments = paginator.paginate_queryset(payments, request)
	
	serializer = PaymentSerializer(paginated_payments, many=True)
	
	return paginator.get_paginated_response(serializer.data)

