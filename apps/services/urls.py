from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ServiceCategoryViewSet, ServiceViewSet, ServiceStepViewSet, PackageViewSet

app_name = 'services'

router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet, basename='service-categories')
router.register(r'services', ServiceViewSet, basename='services')
router.register(r'steps', ServiceStepViewSet, basename='service-steps')
router.register(r'packages', PackageViewSet, basename='packages')

urlpatterns = router.urls
