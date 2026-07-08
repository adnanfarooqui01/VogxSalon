

from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from datetime import datetime
from decouple import config
import uuid

from apps.bookings.models import Booking, BookingGroup
from apps.bookings.serializers import BookingGroupSerializer
from apps.bookings.services import compute_booking_totals, create_booking_group
from .models import Payment
from .serializers import PaymentSerializer, CreateOrderSerializer, VerifyPaymentSerializer, PrecheckOrderSerializer
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
	
	if booking.status != 'confirmed':
		return Response(
			{'detail': 'Booking must be in confirmed status for payment'},
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
	# Create or update Payment record
	if existing_payment:
		payment = existing_payment
	else:
		payment = Payment.objects.create(
			booking=booking,
			amount=booking.total_price,
			status='pending',
			payment_method='razorpay',
			transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}"
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
		'amount': razorpay_order['amount'] / 100,
		'currency': razorpay_order['currency'],
		'key': config('RAZORPAY_KEY_ID'),
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
		booking.status = 'confirmed'
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


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_precheck_order(request):
    serializer = PrecheckOrderSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    try:
        _, _, _, _, _, total_price = compute_booking_totals(
            data.get('service_ids', []) or [],
            data.get('package_ids', []) or [],
            data['booking_type'],
            data.get('pincode'),
        )
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    payload = dict(data)
    payload['booking_date'] = str(payload['booking_date'])
    payload['booking_time'] = str(payload['booking_time'])

    payment = Payment.objects.create(
        booking_group=None,
        amount=total_price,
        status='pending',
        payment_method='razorpay',
        transaction_id=f"TXN-{uuid.uuid4().hex[:20].upper()}",
        pending_payload=payload,
    )

    razorpay_order = create_razorpay_order(
        amount=float(total_price),
        receipt=payment.transaction_id,
        notes={'user_id': request.user.id}
    )
    if not razorpay_order:
        payment.delete()
        return Response({'detail': 'Failed to create Razorpay order'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    payment.razorpay_order_id = razorpay_order['id']
    payment.status = 'initiated'
    payment.save(update_fields=['razorpay_order_id', 'status', 'updated_at'])

    return Response({
        'order_id': razorpay_order['id'],
        'amount': razorpay_order['amount'] / 100,
        'currency': razorpay_order['currency'],
        'key': config('RAZORPAY_KEY_ID'),
        'transaction_id': payment.transaction_id,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_combined_payment(request):
    serializer = VerifyPaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    razorpay_order_id = serializer.validated_data['razorpay_order_id']
    razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
    razorpay_signature = serializer.validated_data['razorpay_signature']

    if not verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        return Response({'detail': 'Invalid payment signature'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
    except Payment.DoesNotExist:
        return Response({'detail': 'Payment record not found'}, status=status.HTTP_404_NOT_FOUND)

    if payment.booking_group_id:
        return Response({'status': 'completed', 'group_id': payment.booking_group_id, 'group': BookingGroupSerializer(payment.booking_group).data})

    payload = payment.pending_payload
    if not payload:
        return Response({'detail': 'Booking details missing for this payment'}, status=status.HTTP_400_BAD_REQUEST)

    from datetime import datetime as dt
    payload = dict(payload)
    payload['booking_date'] = dt.strptime(payload['booking_date'], '%Y-%m-%d').date()
    payload['booking_time'] = dt.strptime(payload['booking_time'], '%H:%M:%S').time()

    name = (payload.pop('name', '') or '').strip()
    email = (payload.pop('email', '') or '').strip()
    user = request.user
    update_fields = []
    if name and name != user.name:
        user.name = name
        update_fields.append('name')
    if email and email != user.email:
        user.email = email
        update_fields.append('email')
    if update_fields:
        user.save(update_fields=update_fields)

    with transaction.atomic():
        group = create_booking_group(user, payload, status='confirmed')
        payment.booking_group = group
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = 'completed'
        payment.paid_at = timezone.now()
        payment.pending_payload = None
        payment.save()
        group.is_paid = True
        group.save(update_fields=['is_paid', 'updated_at'])

    return Response({'status': 'completed', 'group_id': group.id, 'group': BookingGroupSerializer(group).data})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_pay_later(request):
    group_id = request.data.get('group_id')
    group = BookingGroup.objects.filter(id=group_id, user=request.user, status='confirmed').first()
    if not group:
        return Response({'detail': 'Invalid booking group'}, status=status.HTTP_400_BAD_REQUEST)

    Payment.objects.get_or_create(
        booking_group=group,
        defaults={'amount': group.total_price, 'status': 'pending', 'payment_method': 'pay_later',
                  'transaction_id': f"TXN-{uuid.uuid4().hex[:20].upper()}"}
    )
    return Response({'status': 'ok', 'group_id': group.id})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_history(request):
    from rest_framework.pagination import PageNumberPagination

    if request.user.is_staff:
        payments = Payment.objects.all().order_by('-created_at')
    else:
        payments = Payment.objects.filter(
            booking__user=request.user
        ).order_by('-created_at')

    paginator = PageNumberPagination()
    paginator.page_size = int(request.query_params.get('page_size', 20))

    paginated_payments = paginator.paginate_queryset(
        payments,
        request
    )

    serializer = PaymentSerializer(
        paginated_payments,
        many=True
    )

    return paginator.get_paginated_response(
        serializer.data
    )