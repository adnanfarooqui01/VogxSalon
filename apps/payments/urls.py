from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PaymentViewSet, create_payment_order, verify_payment_order, payment_history,
    create_combined_order, verify_combined_payment, confirm_pay_later,
)


app_name = 'payments'

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payments')

urlpatterns = [
    path('create-order/', create_payment_order, name='create-order'),
    path('verify-payment/', verify_payment_order, name='verify-payment'),
    path('create-combined-order/', create_combined_order, name='create-combined-order'),
    path('verify-combined-payment/', verify_combined_payment, name='verify-combined-payment'),
    path('confirm-pay-later/', confirm_pay_later, name='confirm-pay-later'),
    path('history/', payment_history, name='payment-history'),
    path('', include(router.urls)),
]

