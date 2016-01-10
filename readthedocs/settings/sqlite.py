import os

from .base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(SITE_ROOT, 'dev.db'),
    }
}

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
# CELERY_ALWAYS_EAGER = False


SESSION_COOKIE_DOMAIN = None
CACHE_BACKEND = 'dummy://'

SLUMBER_USERNAME = 'test'
SLUMBER_PASSWORD = 'test'  # noqa: ignore dodgy check
SLUMBER_API_HOST = 'http://localhost:8000'
# GROK_API_HOST = 'http://localhost:5555'
PRODUCTION_DOMAIN = 'localhost:8000'

WEBSOCKET_HOST = 'localhost:8088'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

DONT_HIT_DB = False
NGINX_X_ACCEL_REDIRECT = True

CELERY_ALWAYS_EAGER = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
FILE_SYNCER = 'readthedocs.privacy.backends.syncers.LocalSyncer'

# For testing locally. Put this in your /etc/hosts:
# 127.0.0.1 test
# and navigate to http://test:8000
CORS_ORIGIN_WHITELIST = (
    'test:8000',
)

if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        from local_settings import *  # noqa
    except ImportError:
        pass
