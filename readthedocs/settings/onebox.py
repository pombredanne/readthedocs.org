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
CELERY_ALWAYS_EAGER = False

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(SITE_ROOT, 'whoosh_index'),
    },
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.cache.RedisCache',
        'LOCATION': 'localhost:6379',
        'PREFIX': 'docs',
        'OPTIONS': {
            'DB': 1,
            'CLIENT_CLASS': 'redis_cache.client.DefaultClient',
        },
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

SLUMBER_API_HOST = 'http://localhost:8000'
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTOCOL", "https")
SESSION_COOKIE_DOMAIN = None

SLUMBER_USERNAME = 'test'
SLUMBER_PASSWORD = 'test'  # noqa
SLUMBER_API_HOST = 'http://localhost:8000'

WEBSOCKET_HOST = 'localhost:8088'

DONT_HIT_DB = False
# PRODUCTION_DOMAIN = 'readthedocs.org'
# USE_SUBDOMAIN = True


if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        from local_settings import *  # noqa
    except ImportError:
        pass
