"""
Production settings for salon_project.
Deployed on Hostinger VPS.
"""

from .base import *

# Production never DEBUG
DEBUG = False

# Strict HTTPS settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Static files - WhiteNoise compressed
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CORS - production domain only
CORS_ALLOWED_ORIGINS = [
    config('SITE_URL'),
]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {'class': 'logging.FileHandler', 'filename': BASE_DIR / 'logs' / 'django.log'},
    },
    'root': {'handlers': ['file'], 'level': 'WARNING'},
}

print("✓ Production settings loaded - HTTPS enforced")
