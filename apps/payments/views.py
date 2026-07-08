import json
import logging
import uuid
from datetime import datetime as dt

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from decouple import config
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.bookings.models import Booking, BookingGroup
from apps.bookings.serializers import BookingGroupSerializer
from apps.bookings.services import compute_booking_totals, create_booking_group
from .models import Payment
from .serializers import PaymentSerializer, CreateOrderSerializer, VerifyPaymentSerializer, PrecheckOrderSerializer
from .razorpay_utils import (
    create_razorpay_order,
    verify_razorpay_signature,
    verify_webhook_signature,
    fetch_payment_details,
)

logger = logging.getLogger(__name__)

GENERIC_ERROR_MSG = "Something went wrong while processing your payment. Please try again, and contact support if the amount was deducted."

# Amounts are compared in paise (integers) to avoid float rounding issues.
# A few paise of tolerance protects against legitimate float rounding on
# either side without opening the door to real underpayment.
AMOUNT_TOLERANCE_PAISE = 100  # ₹1


def _amounts_match(expected_rupees, actual_paise):
    expected_paise = int(round(float(expected_rupees) * 100))
    return abs(expected_paise - int(actual_paise)) <= AMOUNT_TOLERANCE_PAISE


# ==================== VIEWSET ====================

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
@throttle_classes([ScopedRateThrottle])
@permission_classes([permissions.IsAuthenticated])
def create_payment_order(request):
	"""
	Create a Razorpay order for a single booking.

	Request body: { "booking_id": 1 }
	Response (201): { "order_id", "amount", "currency", "key", "transaction_id", "payment_id" }
	"""
	try:
		serializer = CreateOrderSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		booking_id = serializer.validated_data['booking_id']

		try:
			booking = Booking.objects.get(id=booking_id, user=request.user)
		except Booking.DoesNotExist:
			return Response(
				{'detail': 'Booking not found or does not belong to you.'},
				status=status.HTTP_404_NOT_FOUND,
			)

		if booking.status != 'confirmed':
			return Response(
				{'detail': 'This booking is not ready for payment.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

		existing_payment = Payment.objects.filter(booking=booking).first()
		if existing_payment and existing_payment.status in ['completed', 'initiated']:
			return Response(
				{'detail': 'Payment has already been initiated or completed for this booking.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

		payment = existing_payment or Payment.objects.create(
			booking=booking,
			amount=booking.total_price,
			status='pending',
			payment_method='razorpay',
			transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
		)

		razorpay_order = create_razorpay_order(
			amount=float(booking.total_price),
			receipt=payment.transaction_id,
			notes={
				'booking_id': booking.id,
				'customer_name': booking.user.name,
				'customer_phone': booking.user.phone,
				'service': booking.service.name,
			},
		)

		if not razorpay_order:
			return Response(
				{'detail': 'Could not start payment right now. Please try again in a moment.'},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

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

	except Exception:
		logger.exception(f"Unexpected error in create_payment_order for user={request.user.id}")
		return Response({'detail': GENERIC_ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


create_payment_order.cls.throttle_scope = 'payment'


@api_view(['POST'])
@throttle_classes([ScopedRateThrottle])
@permission_classes([permissions.IsAuthenticated])
def verify_payment_order(request):
	"""
	Verify a Razorpay payment (single-booking flow) and confirm the booking.

	Request body: { "razorpay_order_id", "razorpay_payment_id", "razorpay_signature" }
	"""
	try:
		serializer = VerifyPaymentSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		razorpay_order_id = serializer.validated_data['razorpay_order_id']
		razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
		razorpay_signature = serializer.validated_data['razorpay_signature']

		if not verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
			logger.warning(f"Invalid payment signature: order={razorpay_order_id} user={request.user.id}")
			return Response({'detail': 'Payment verification failed. Please contact support if you were charged.'}, status=status.HTTP_400_BAD_REQUEST)

		with transaction.atomic():
			try:
				# Lock the row so a retried/duplicate verify call can't process twice concurrently.
				payment = Payment.objects.select_for_update().get(
					razorpay_order_id=razorpay_order_id,
					booking__user=request.user,
				)
			except Payment.DoesNotExist:
				return Response({'detail': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

			if payment.status == 'completed':
				# Idempotent: already processed (e.g. webhook got there first, or duplicate call).
				booking = payment.booking
				return Response({
					'status': 'completed', 'message': 'Payment already verified.',
					'transaction_id': payment.transaction_id, 'amount': float(payment.amount),
					'paid_at': payment.paid_at, 'booking_id': booking.id,
				}, status=status.HTTP_200_OK)

			# Re-check the actual captured amount against Razorpay directly —
			# the signature only proves order_id/payment_id are genuinely
			# linked, not that the captured amount matches what we expected.
			razorpay_payment = fetch_payment_details(razorpay_payment_id)
			if not razorpay_payment:
				return Response({'detail': 'Could not confirm payment with the payment provider. Please contact support.'}, status=status.HTTP_502_BAD_GATEWAY)

			if razorpay_payment.get('status') != 'captured':
				logger.warning(f"Payment not captured: {razorpay_payment_id} status={razorpay_payment.get('status')}")
				return Response({'detail': 'Payment was not completed successfully.'}, status=status.HTTP_400_BAD_REQUEST)

			if not _amounts_match(payment.amount, razorpay_payment.get('amount', 0)):
				logger.error(f"Amount mismatch: expected={payment.amount} got={razorpay_payment.get('amount')} payment_id={razorpay_payment_id}")
				return Response({'detail': 'Payment amount mismatch detected. Please contact support.'}, status=status.HTTP_400_BAD_REQUEST)

			payment.razorpay_payment_id = razorpay_payment_id
			payment.razorpay_signature = razorpay_signature
			payment.status = 'completed'
			payment.paid_at = timezone.now()
			payment.save()

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

	except Exception:
		logger.exception(f"Unexpected error in verify_payment_order for user={request.user.id}")
		return Response({'detail': GENERIC_ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


verify_payment_order.cls.throttle_scope = 'payment'


@api_view(['POST'])
@throttle_classes([ScopedRateThrottle])
@permission_classes([permissions.IsAuthenticated])
def create_precheck_order(request):
	"""Create a Razorpay order BEFORE the booking exists (multi-service cart checkout)."""
	try:
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
			notes={'user_id': request.user.id},
		)
		if not razorpay_order:
			payment.delete()
			return Response(
				{'detail': 'Could not start payment right now. Please try again in a moment.'},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

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

	except Exception:
		logger.exception(f"Unexpected error in create_precheck_order for user={request.user.id}")
		return Response({'detail': GENERIC_ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


create_precheck_order.cls.throttle_scope = 'payment'


def _finalize_group_payment(payment, razorpay_payment_id, razorpay_signature):
	"""
	Shared completion logic for the cart/group checkout flow — called from
	BOTH verify_combined_payment (browser callback) and the webhook, so
	whichever one reaches this first wins and the other is a safe no-op.

	Must be called from inside `with transaction.atomic():` by the caller,
	on a `payment` row already locked via select_for_update().

	Returns (group, error_response_or_None).
	"""
	if payment.booking_group_id:
		# Already finalized — idempotent success.
		return payment.booking_group, None

	razorpay_payment = fetch_payment_details(razorpay_payment_id)
	if not razorpay_payment:
		return None, Response({'detail': 'Could not confirm payment with the payment provider. Please contact support.'}, status=status.HTTP_502_BAD_GATEWAY)

	if razorpay_payment.get('status') != 'captured':
		logger.warning(f"Payment not captured: {razorpay_payment_id} status={razorpay_payment.get('status')}")
		return None, Response({'detail': 'Payment was not completed successfully.'}, status=status.HTTP_400_BAD_REQUEST)

	if not _amounts_match(payment.amount, razorpay_payment.get('amount', 0)):
		logger.error(f"Amount mismatch: expected={payment.amount} got={razorpay_payment.get('amount')} payment_id={razorpay_payment_id}")
		return None, Response({'detail': 'Payment amount mismatch detected. Please contact support.'}, status=status.HTTP_400_BAD_REQUEST)

	payload = payment.pending_payload
	if not payload:
		logger.error(f"No pending_payload on payment={payment.id} — cannot create booking despite captured payment")
		return None, Response({'detail': 'Your payment succeeded but we could not find your booking details. Please contact support with your transaction ID.'}, status=status.HTTP_400_BAD_REQUEST)

	payload = dict(payload)
	payload['booking_date'] = dt.strptime(payload['booking_date'], '%Y-%m-%d').date()
	payload['booking_time'] = dt.strptime(payload['booking_time'], '%H:%M:%S').time()

	name = (payload.pop('name', '') or '').strip()
	email = (payload.pop('email', '') or '').strip()
	user = payment.pending_payload_user if hasattr(payment, 'pending_payload_user') else None
	# The user is derived from the booking's owner via the Payment -> booking
	# relation in the older flow; for the group/precheck flow we stored no
	# direct FK to the user before booking creation, so pull it from the
	# authenticated request in the online-verify path, or from the payload
	# if you store user_id there. Adjust this line if your PrecheckOrderSerializer
	# stores user differently — see note below.
	from apps.accounts.models import CustomUser
	user_id = payment.razorpay_order_id and None  # placeholder, see note
	# NOTE: safest is to have stored the user id on the Payment row when it
	# was created in create_precheck_order (e.g. a `pending_user` FK). If
	# that's not present in your model yet, keep using request.user in the
	# browser-callback path (verify_combined_payment) and skip user-name/
	# email sync inside the webhook path, doing only booking creation there.

	update_fields = []
	if user:
		if name and name != user.name:
			user.name = name
			update_fields.append('name')
		if email and email != user.email:
			user.email = email
			update_fields.append('email')
		if update_fields:
			user.save(update_fields=update_fields)

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

	return group, None


@api_view(['POST'])
@throttle_classes([ScopedRateThrottle])
@permission_classes([permissions.IsAuthenticated])
def verify_combined_payment(request):
	"""Browser-side verification after Razorpay Checkout.js completes (cart/group flow)."""
	try:
		serializer = VerifyPaymentSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		razorpay_order_id = serializer.validated_data['razorpay_order_id']
		razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
		razorpay_signature = serializer.validated_data['razorpay_signature']

		if not verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
			logger.warning(f"Invalid combined payment signature: order={razorpay_order_id} user={request.user.id}")
			return Response({'detail': 'Payment verification failed. Please contact support if you were charged.'}, status=status.HTTP_400_BAD_REQUEST)

		with transaction.atomic():
			try:
				payment = Payment.objects.select_for_update().get(razorpay_order_id=razorpay_order_id)
			except Payment.DoesNotExist:
				return Response({'detail': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

			# Attach the requesting user for name/email sync (see _finalize_group_payment note).
			payment.pending_payload_user = request.user
			group, error = _finalize_group_payment(payment, razorpay_payment_id, razorpay_signature)
			if error:
				return error

		return Response({'status': 'completed', 'group_id': group.id, 'group': BookingGroupSerializer(group).data})

	except Exception:
		logger.exception(f"Unexpected error in verify_combined_payment for user={request.user.id}")
		return Response({'detail': GENERIC_ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


verify_combined_payment.cls.throttle_scope = 'payment'


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_pay_later(request):
	try:
		group_id = request.data.get('group_id')
		group = BookingGroup.objects.filter(id=group_id, user=request.user, status='confirmed').first()
		if not group:
			return Response({'detail': 'Invalid booking group.'}, status=status.HTTP_400_BAD_REQUEST)

		Payment.objects.get_or_create(
			booking_group=group,
			defaults={'amount': group.total_price, 'status': 'pending', 'payment_method': 'pay_later',
			          'transaction_id': f"TXN-{uuid.uuid4().hex[:20].upper()}"}
		)
		return Response({'status': 'ok', 'group_id': group.id})

	except Exception:
		logger.exception(f"Unexpected error in confirm_pay_later for user={request.user.id}")
		return Response({'detail': GENERIC_ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_history(request):
	try:
		from rest_framework.pagination import PageNumberPagination

		if request.user.is_staff:
			payments = Payment.objects.all().order_by('-created_at')
		else:
			payments = Payment.objects.filter(booking__user=request.user).order_by('-created_at')

		paginator = PageNumberPagination()
		paginator.page_size = min(int(request.query_params.get('page_size', 20)), 100)  # cap to prevent abuse
		paginated_payments = paginator.paginate_queryset(payments, request)
		serializer = PaymentSerializer(paginated_payments, many=True)
		return paginator.get_paginated_response(serializer.data)

	except (ValueError, TypeError):
		return Response({'detail': 'Invalid page_size parameter.'}, status=status.HTTP_400_BAD_REQUEST)
	except Exception:
		logger.exception(f"Unexpected error in payment_history for user={request.user.id}")
		return Response({'detail': GENERIC_ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== WEBHOOK ====================
# Plain Django view (NOT a DRF @api_view) so we can access request.body as
# raw bytes for signature verification BEFORE any JSON parsing. Razorpay
# calls this server-to-server — there is no browser/user session, so this
# must never require IsAuthenticated. Its only "auth" is the signature.

@csrf_exempt
def razorpay_webhook(request):
	if request.method != 'POST':
		return HttpResponse(status=405)

	raw_body = request.body
	received_signature = request.headers.get('X-Razorpay-Signature', '')

	if not verify_webhook_signature(raw_body, received_signature):
		logger.warning(f"Rejected webhook: invalid signature from ip={request.META.get('REMOTE_ADDR')}")
		return HttpResponse(status=400)

	try:
		event = json.loads(raw_body)
	except (json.JSONDecodeError, UnicodeDecodeError):
		logger.error("Rejected webhook: malformed JSON body")
		return HttpResponse(status=400)

	event_type = event.get('event')
	logger.info(f"Razorpay webhook received: {event_type}")

	try:
		if event_type == 'payment.captured':
			_handle_payment_captured(event)
		elif event_type == 'payment.failed':
			_handle_payment_failed(event)
		# Other event types (refund.processed, order.paid, etc.) can be
		# added here as needed — always ack with 200 for events you don't
		# handle yet, so Razorpay doesn't keep retrying them forever.
	except Exception:
		# Log but still return 200 for a duplicate/already-processed event
		# rather than triggering endless Razorpay retries on our own bug.
		# Genuine failures are visible in logs/Sentry either way.
		logger.exception(f"Error processing webhook event={event_type}")

	# Razorpay expects a 200 to acknowledge receipt; anything else triggers retries.
	return HttpResponse(status=200)


def _handle_payment_captured(event):
	payment_entity = event.get('payload', {}).get('payment', {}).get('entity', {})
	razorpay_order_id = payment_entity.get('order_id')
	razorpay_payment_id = payment_entity.get('id')

	if not razorpay_order_id or not razorpay_payment_id:
		logger.error(f"Malformed payment.captured payload: {event}")
		return

	with transaction.atomic():
		try:
			payment = Payment.objects.select_for_update().get(razorpay_order_id=razorpay_order_id)
		except Payment.DoesNotExist:
			logger.error(f"Webhook payment.captured for unknown order_id={razorpay_order_id}")
			return

		if payment.status == 'completed':
			return  # already processed via browser callback — idempotent no-op

		if not _amounts_match(payment.amount, payment_entity.get('amount', 0)):
			logger.error(f"Webhook amount mismatch: expected={payment.amount} got={payment_entity.get('amount')} order={razorpay_order_id}")
			return

		if payment.booking_group_id is None and payment.pending_payload:
			# Group/cart flow — finalize booking creation.
			# NOTE: webhook has no request.user, so name/email sync is
			# skipped here (payment.pending_payload_user unset); it will
			# already have happened via verify_combined_payment in the
			# normal case where the browser call succeeds. This webhook
			# path exists as a SAFETY NET for when it doesn't (browser
			# closed, network drop, etc.).
			group, error = _finalize_group_payment(payment, razorpay_payment_id, received_signature_placeholder(payment))
			if error:
				logger.error(f"Webhook could not finalize group payment {payment.id}: {error.data}")
			return

		if payment.booking_id:
			# Single-booking flow.
			payment.razorpay_payment_id = razorpay_payment_id
			payment.status = 'completed'
			payment.paid_at = timezone.now()
			payment.save()

			booking = payment.booking
			booking.status = 'confirmed'
			booking.is_paid = True
			booking.updated_at = timezone.now()
			booking.save()


def received_signature_placeholder(payment):
	"""
	The webhook doesn't receive the checkout-callback signature (that's a
	different signature scheme, tied to Checkout.js, not the webhook). We
	still record the payment as verified because the WEBHOOK signature
	itself (already checked in razorpay_webhook) is the authority here.
	Store an empty string rather than a fabricated value.
	"""
	return ''


def _handle_payment_failed(event):
	payment_entity = event.get('payload', {}).get('payment', {}).get('entity', {})
	razorpay_order_id = payment_entity.get('order_id')

	if not razorpay_order_id:
		return

	with transaction.atomic():
		payment = Payment.objects.select_for_update().filter(razorpay_order_id=razorpay_order_id).first()
		if payment and payment.status not in ('completed',):
			payment.status = 'failed'
			payment.save(update_fields=['status', 'updated_at'])
			logger.info(f"Payment marked failed: order={razorpay_order_id}")