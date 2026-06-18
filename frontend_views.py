"""
Frontend views for serving HTML templates
"""
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def index(request):
    """Home page"""
    return render(request, 'index.html')


@require_http_methods(["GET"])
def login(request):
    """Login page"""
    return render(request, 'login.html')


@require_http_methods(["GET"])
def services(request):
    """Services listing page"""
    return render(request, 'services.html')


@require_http_methods(["GET"])
def bookings(request):
    """User bookings page"""
    return render(request, 'bookings.html')


@require_http_methods(["GET"])
def profile(request):
    """User profile page"""
    return render(request, 'profile.html')
