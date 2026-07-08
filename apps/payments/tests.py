from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.accounts.models import CustomUser
from apps.bookings.models import Booking, BookingGroup
from apps.payments.models import Payment
from apps.payments.views import create_precheck_order, verify_combined_payment
from apps.services.models import Service, ServiceCategory


class PrecheckPaymentFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(phone='9999999999', name='Test User', password='secret123')
        self.category = ServiceCategory.objects.create(name='Hair', description='Hair services')
        self.service = Service.objects.create(
            category=self.category,
            name='Hair Cut',
            description='Trim',
            price=100,
            duration_minutes=30,
        )

    def test_create_precheck_order_stores_payload_without_creating_bookings(self):
        factory = APIRequestFactory()
        request = factory.post('/payments/create-precheck-order/', {
            'service_ids': [self.service.id],
            'booking_date': '2030-01-15',
            'booking_time': '10:00:00',
            'booking_type': 'salon',
            'name': 'Test User',
            'email': 'test@example.com',
        })
        request.user = self.user

        response = create_precheck_order(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Payment.objects.count(), 1)
        payment = Payment.objects.get()
        self.assertIsNone(payment.booking_group_id)
        self.assertEqual(payment.pending_payload['service_ids'], [self.service.id])
        self.assertEqual(BookingGroup.objects.count(), 0)
        self.assertEqual(Booking.objects.count(), 0)

    @patch('apps.payments.views.verify_razorpay_signature', return_value=True)
    def test_verify_combined_payment_creates_booking_group_on_success(self, _mock_signature):
        payment = Payment.objects.create(
            amount=100,
            status='initiated',
            payment_method='razorpay',
            transaction_id='TXN-TEST-1',
            razorpay_order_id='order_123',
            pending_payload={
                'service_ids': [self.service.id],
                'booking_date': '2030-01-15',
                'booking_time': '10:00:00',
                'booking_type': 'salon',
                'name': 'Test User',
                'email': 'test@example.com',
            },
        )

        factory = APIRequestFactory()
        request = factory.post('/payments/verify-combined-payment/', {
            'razorpay_order_id': 'order_123',
            'razorpay_payment_id': 'pay_123',
            'razorpay_signature': 'signature',
        })
        request.user = self.user

        response = verify_combined_payment(request)

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'completed')
        self.assertIsNotNone(payment.booking_group_id)
        self.assertEqual(BookingGroup.objects.count(), 1)
        self.assertEqual(Booking.objects.count(), 1)
