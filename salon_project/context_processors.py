"""
Context processors for making settings available in templates.
"""

from django.conf import settings


def firebase_context(request):
    """
    Add Firebase configuration to template context.
    This makes Firebase credentials available in HTML templates for the JavaScript SDK.
    """
    return {
        'FIREBASE_API_KEY': settings.FIREBASE_API_KEY,
        'FIREBASE_AUTH_DOMAIN': settings.FIREBASE_AUTH_DOMAIN,
        'FIREBASE_PROJECT_ID': settings.FIREBASE_PROJECT_ID,
        'FIREBASE_MESSAGING_SENDER_ID': settings.FIREBASE_MESSAGING_SENDER_ID,
        'FIREBASE_APP_ID': settings.FIREBASE_APP_ID,
        'FIREBASE_STORAGE_BUCKET': settings.FIREBASE_STORAGE_BUCKET,
    }
