"""
Django settings for vinverse project.
"""

from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import dj_database_url
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS configuration
# For Railway: Automatically includes Railway domains
default_hosts = ['localhost', '127.0.0.1']

# Check for Railway environment variables
railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
if railway_domain:
    default_hosts.append(railway_domain)

# Also check for Railway's service domain pattern
railway_service_domain = os.getenv('RAILWAY_SERVICE_DOMAIN')
if railway_service_domain:
    default_hosts.append(railway_service_domain)

# Add your specific Railway domain (update if it changes)
default_hosts.append('web-production-725a.up.railway.app')

# If ALLOWED_HOSTS is explicitly set via environment variable, merge it with defaults
# This ensures Railway domain is always included even if env var is set
allowed_hosts_env = os.getenv('ALLOWED_HOSTS')
if allowed_hosts_env:
    env_hosts = config('ALLOWED_HOSTS', cast=Csv())
    # Merge environment hosts with defaults, avoiding duplicates
    ALLOWED_HOSTS = list(set(default_hosts + list(env_hosts)))
else:
    ALLOWED_HOSTS = default_hosts


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',  # Django Channels for WebSockets
    # Local apps
    'accounts',
    'tournaments',
    'gamerlink',
    'chat',
    'ai_engine',
    'notifications',
]

# Redis cache (for Phase 2 - ready to use when Redis is installed)
# For Phase 1, we use database-backed sessions instead
USE_REDIS = config('USE_REDIS', default=False, cast=bool)

if USE_REDIS:
    # Redis cache configuration (Phase 2)
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'vinverse',
            'TIMEOUT': 300,  # 5 minutes default timeout
        }
    }
    # Session backend using Redis (Phase 2)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    # Fallback cache for Phase 1 (database-backed)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'cache_table',
        }
    }
    # Session backend using database (Phase 1)
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Media files (for user uploads like post images)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Django Channels Configuration
ASGI_APPLICATION = 'vinverse.asgi.application'

# Channel Layers (Redis for WebSocket support)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vinverse.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'vinverse.wsgi.application'


# Database Configuration
# Priority: DATABASE_URL (Railway/Production) > Individual DB settings > SQLite fallback
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL') or os.getenv('PGDATABASE')

DATABASES = None

if DATABASE_URL:
    # Use dj_database_url for Railway/Heroku-style DATABASE_URL
    try:
        DATABASES = {
            'default': dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
    except Exception as e:
        # If DATABASE_URL parsing fails, fall through to other options
        print(f"Warning: Failed to parse DATABASE_URL: {e}")
        DATABASES = None

# If DATABASE_URL wasn't set or failed, try individual settings
if not DATABASES:
    DATABASE_ENGINE = config('DATABASE_ENGINE', default='postgresql')
    
    if DATABASE_ENGINE == 'postgresql':
        # Check if we're on Railway (Railway provides PGHOST, PGPORT, etc.)
        pg_host = os.getenv('PGHOST') or config('DB_HOST', default=None)
        pg_port = os.getenv('PGPORT') or config('DB_PORT', default=None)
        pg_user = os.getenv('PGUSER') or config('DB_USER', default=None)
        pg_password = os.getenv('PGPASSWORD') or config('DB_PASSWORD', default=None)
        pg_database = os.getenv('PGDATABASE') or config('DB_NAME', default=None)
        
        # Only use PostgreSQL if we have proper credentials
        if pg_host and pg_user and pg_password and pg_database:
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': pg_database,
                    'USER': pg_user,
                    'PASSWORD': pg_password,
                    'HOST': pg_host,
                    'PORT': pg_port or '5432',
                    'OPTIONS': {
                        'connect_timeout': 10,
                    },
                }
            }
        else:
            # Fallback to SQLite if PostgreSQL credentials are missing
            print("Warning: PostgreSQL credentials not found. Falling back to SQLite.")
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / 'db.sqlite3',
                }
            }
    else:
        # Fallback to SQLite for development
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }


# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Disable pagination for tournaments (return all as array)
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 20,
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Settings - Allow React frontend to access API
# For development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite default port
    "http://127.0.0.1:5173",
]

# For production on Railway - allow Railway domains
# Check if we're in production (Railway sets RAILWAY_ENVIRONMENT)
if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_DEPLOYMENT_ID'):
    # Add specific Railway domain
    CORS_ALLOWED_ORIGINS.append("https://web-production-725a.up.railway.app")
    # For Railway, you can also allow all origins (less secure but flexible)
    # Uncomment the line below if you need to allow requests from any origin
    # CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

# Allow common headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

