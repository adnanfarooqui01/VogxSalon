"""
Frontend views for serving HTML templates
"""
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def index(request):
    """Home page with packages, categories, and gender toggle"""
    return render(request, 'index_new.html')


@require_http_methods(["GET"])
def services_listing(request):
    """Services listing page with category pills and sticky navigation"""
    return render(request, 'services_listing.html')


@require_http_methods(["GET"])
def service_detail(request, service_id):
    """Service detail page with steps and similar services"""
    return render(request, 'service_detail.html', {'service_id': service_id})


@require_http_methods(["GET"])
def login(request):
    """Login page with OTP authentication"""
    return render(request, 'login.html')


@require_http_methods(["GET"])
def cart(request):
    """Shopping cart page"""
    return render(request, 'cart.html')


@require_http_methods(["GET"])
def bookings(request):
    """User bookings page"""
    return render(request, 'bookings.html')


@require_http_methods(["GET"])
def profile(request):
    """User profile page"""
    return render(request, 'profile.html')
