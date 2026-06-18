from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet, create_payment_order, verify_payment_order, payment_history

app_name = 'payments'

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payments')

urlpatterns = [
    path('create-order/', create_payment_order, name='create-order'),
    path('verify-payment/', verify_payment_order, name='verify-payment'),
    path('history/', payment_history, name='payment-history'),
    path('', include(router.urls)),
]
