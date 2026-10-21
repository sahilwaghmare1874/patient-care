import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'healthcare-production-secret-key-super-secure-2026-xyz')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Applications
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
    'rest_framework_simplejwt',

    # Healthcare System Apps
    'accounts',
    'patients',
    'doctors',
    'pathology',
    'pharmacy',
    'government',
    'insurance',
    'funds',
    'payments',
    'reports',
    'notifications',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # Disabled: API uses JWT Bearer tokens, not session cookies
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
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database Configuration (Environment-based: DATABASE_URL, PostgreSQL with SQLite fallback)
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
elif os.environ.get('DB_ENGINE') == 'postgresql' or os.environ.get('POSTGRES_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'patientcare_db'),
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static and Media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework & JWT Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:.*$",
    r"^http://127\.0\.0\.1:.*$",
    r"^null$",
]

# CSRF Trusted Origins (needed for Cloudflare tunnel / any public tunnel)
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://*.trycloudflare.com',
    'https://*.loca.lt',
    'https://*.ngrok.io',
    'https://*.ngrok-free.app',
    'https://*.onrender.com',
    'https://*.vercel.app',
]

# AI Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
AI_PROVIDER = os.environ.get('AI_PROVIDER', 'gemini')  # 'gemini' or 'openai'
AI_TIMEOUT_SECONDS = int(os.environ.get('AI_TIMEOUT_SECONDS', 30))

# Reserve Account Configuration
RESERVE_CREDIT_PERCENTAGE = float(os.environ.get('RESERVE_CREDIT_PERCENTAGE', 90.0))

# Payment Gateway & YouPI-PG Configuration
PAYMENT_GATEWAY_MODE = os.environ.get('PAYMENT_GATEWAY_MODE', 'sandbox')  # 'live' or 'sandbox'
YOUPI_PG_API_URL = os.environ.get('YOUPI_PG_API_URL', 'http://127.0.0.1:6100')
YOUPI_PG_CHECKOUT_URL = os.environ.get('YOUPI_PG_CHECKOUT_URL', 'http://127.0.0.1:7000')
YOUPI_PG_MERCHANT_ID = os.environ.get('YOUPI_PG_MERCHANT_ID', 'mer_patientcare_default')
YOUPI_PG_WEBHOOK_SECRET = os.environ.get('YOUPI_PG_WEBHOOK_SECRET', 'whsec_patientcare_super_secure_secret_2026')
YOUPI_PG_CURRENCY = 'INR'

# Healthcare Contribution Rules (Configurable: Doctor 10%, Pathology 10%, Pharmacy 5%)
CONTRIBUTION_RULES = {
    'DOCTOR': {
        'rate': 10.00,
        'category': 'Doctor Consultation',
        'service_name': 'Doctor Payment',
    },
    'PATHOLOGY': {
        'rate': 10.00,
        'category': 'Pathology Diagnostic',
        'service_name': 'Pathology Payment',
    },
    'PHARMACY': {
        'rate': 5.00,
        'category': 'Pharmacy Purchase',
        'service_name': 'Pharmacy Payment',
    },
}
