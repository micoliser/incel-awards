from pathlib import Path
import os
import sys
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# ------------------------------------------------------------------------------
# 1. CORE DJANGO SETTINGS
# ------------------------------------------------------------------------------
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

DEFAULT_DEV_SECRET = 'django-insecure-incel-awards-dev-only-change-me-in-production'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', DEFAULT_DEV_SECRET)

raw_allowed_hosts = os.getenv('DJANGO_ALLOWED_HOSTS', '*' if DEBUG else '')
if raw_allowed_hosts:
    ALLOWED_HOSTS = [h.strip() for h in raw_allowed_hosts.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['*'] if DEBUG else []

DJANGO_ADMIN_URL = os.getenv('DJANGO_ADMIN_URL', 'admin/').strip('/') + '/'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'corsheaders',
    'rest_framework',
    # Local
    'people',
    'awards',
    'voting',
    'emails',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ------------------------------------------------------------------------------
# 2. DATABASE — PostgreSQL preferred; SQLite for local/tests when requested
# ------------------------------------------------------------------------------
TESTING = 'test' in sys.argv
# Tests stay on SQLite unless USE_SQLITE is explicitly forced off.
# Empty DB_HOST is valid for PostgreSQL Unix-socket / peer auth.
_use_sqlite_env = os.getenv('USE_SQLITE', '').lower()
USE_SQLITE = TESTING or _use_sqlite_env in ('true', '1', 'yes')

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / ('test_db.sqlite3' if TESTING else 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'incel_awards'),
            'USER': os.getenv('DB_USER', 'micoliser'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            # Blank HOST → Unix socket (peer auth). Set 127.0.0.1 for TCP + password.
            'HOST': os.getenv('DB_HOST', ''),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if (DEBUG or TESTING)
            else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------------------------------------------------------
# 3. DRF / FRONTEND / ORG SYNC
# ------------------------------------------------------------------------------
FRONTEND_BASE_URL = os.getenv(
    'FRONTEND_BASE_URL',
    'http://localhost:3000' if DEBUG else '',
)

ORG_USERS_API_BASE_URL = os.getenv('ORG_USERS_API_BASE_URL', '')
ORG_USERS_API_TOKEN = os.getenv('ORG_USERS_API_TOKEN', '')
# Authorization scheme for org roster API: "Bearer" (production) or "Token".
ORG_USERS_API_AUTH_SCHEME = (
    os.getenv('ORG_USERS_API_AUTH_SCHEME', 'Bearer').strip() or 'Bearer'
)
# Local fake directory at GET /api/v1/external/users (same path as production).
DEV_ORG_USERS_ENABLED = os.getenv(
    'DEV_ORG_USERS_ENABLED',
    'True' if DEBUG else 'False',
).lower() in ('true', '1', 'yes')

# ------------------------------------------------------------------------------
# CELERY (season tick: sync → tokens → invites → status)
# ------------------------------------------------------------------------------
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ALWAYS_EAGER = os.getenv(
    'CELERY_TASK_ALWAYS_EAGER',
    'True' if TESTING else 'False',
).lower() in ('true', '1', 'yes')
CELERY_TASK_EAGER_PROPAGATES = True

# How often beat runs season automation (seconds). Local default 60; prod can be 300+.
_season_tick_seconds = int(os.getenv('SEASON_TICK_SECONDS', '60' if DEBUG else '300'))
CELERY_BEAT_SCHEDULE = {
    'season-tick': {
        'task': 'emails.season_tick',
        'schedule': float(max(15, _season_tick_seconds)),
        'options': {'expires': float(max(15, _season_tick_seconds))},
    },
}

# Ballot throttle rates (token-hash or IP scoped). Format: "<num>/<period>"
# e.g. 60/min, 30/hour. Documented in .env.example and docs/ops.md.
BALLOT_THROTTLE_RESOLVE = os.getenv('BALLOT_THROTTLE_RESOLVE', '60/min')
BALLOT_THROTTLE_VOTE = os.getenv('BALLOT_THROTTLE_VOTE', '30/min')
BALLOT_THROTTLE_DIRECTORY = os.getenv('BALLOT_THROTTLE_DIRECTORY', '60/min')

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ] + (['rest_framework.renderers.BrowsableAPIRenderer'] if DEBUG else []),
    'DEFAULT_THROTTLE_RATES': {
        'ballot_resolve': BALLOT_THROTTLE_RESOLVE,
        'ballot_vote': BALLOT_THROTTLE_VOTE,
        'ballot_directory': BALLOT_THROTTLE_DIRECTORY,
    },
}

# ------------------------------------------------------------------------------
# 4. CORS & CSRF
# ------------------------------------------------------------------------------
# Ballot submit sends X-Ballot-Token; must be allowed on preflight or browsers
# surface a generic network failure on the frontend.
from corsheaders.defaults import default_headers as _CORS_DEFAULT_HEADERS

CORS_ALLOW_HEADERS = list(_CORS_DEFAULT_HEADERS) + [
    'x-ballot-token',
]

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOW_CREDENTIALS = True
    raw_cors = os.getenv('CORS_ALLOWED_ORIGINS', '')
    allowed_cors = [origin.strip() for origin in raw_cors.split(',') if origin.strip()]
    if FRONTEND_BASE_URL and FRONTEND_BASE_URL not in allowed_cors:
        allowed_cors.append(FRONTEND_BASE_URL)
    CORS_ALLOWED_ORIGINS = allowed_cors

    csrf_origins = []
    if FRONTEND_BASE_URL:
        csrf_origins.append(FRONTEND_BASE_URL)
    for host in ALLOWED_HOSTS:
        if host and host != '*':
            csrf_origins.append(f'https://{host}')
    CSRF_TRUSTED_ORIGINS = csrf_origins

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'

if not DEBUG and not TESTING:
    SECURE_SSL_REDIRECT = os.getenv('DJANGO_SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1')
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ------------------------------------------------------------------------------
# 5. EMAIL (prospiz-compatible; console in DEBUG, SMTP in production)
# ------------------------------------------------------------------------------
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
    if DEBUG
    else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp-relay.gmail.com' if not DEBUG else '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587' if not DEBUG else '0') or 0) or None
EMAIL_USE_TLS = os.getenv(
    'EMAIL_USE_TLS',
    'True' if not DEBUG else '',
).lower() in ('true', '1', 'yes')
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', '').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv(
    'DEFAULT_FROM_EMAIL',
    'awards@incelgroup.com' if DEBUG else '',
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL or 'awards@incelgroup.com'
EMAIL_ENABLED = os.getenv(
    'EMAIL_ENABLED',
    'False' if DEBUG else 'True',
).lower() in ('true', '1', 'yes')
EMAIL_DEBUG = os.getenv(
    'EMAIL_DEBUG',
    'True' if DEBUG else 'False',
).lower() in ('true', '1', 'yes')
EMAIL_SENDER_NAME = os.getenv('EMAIL_SENDER_NAME', 'Incel Group Awards')

# ------------------------------------------------------------------------------
# 6. PRODUCTION SAFETY
# ------------------------------------------------------------------------------
def validate_production_settings():
    errors = []
    if not SECRET_KEY or SECRET_KEY == DEFAULT_DEV_SECRET or SECRET_KEY.startswith('django-insecure-') or len(SECRET_KEY) < 32:
        errors.append('DJANGO_SECRET_KEY must be a unique 32+ character secret in production.')
    if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
        errors.append('DJANGO_ALLOWED_HOSTS must be set explicitly (no wildcard) in production.')
    if not USE_SQLITE and not os.getenv('DB_PASSWORD'):
        errors.append('DB_PASSWORD must be set for PostgreSQL in production.')
    if not FRONTEND_BASE_URL or not FRONTEND_BASE_URL.startswith('https://') or 'localhost' in FRONTEND_BASE_URL:
        errors.append('FRONTEND_BASE_URL must be a production HTTPS URL.')
    if errors:
        raise ImproperlyConfigured(
            '\n' + '=' * 80 + '\n'
            'CRITICAL PRODUCTION CONFIGURATION ERROR\n'
            + '\n'.join(f'  - {e}' for e in errors)
            + '\n' + '=' * 80 + '\n'
        )


if not DEBUG and not TESTING:
    validate_production_settings()
