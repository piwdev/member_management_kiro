"""
Django settings for asset_management project.
Base settings shared across all environments.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
]

LOCAL_APPS = [
    'apps.authentication',
    'apps.employees',
    'apps.devices',
    'apps.licenses',
    'apps.permissions',
    'apps.reports',
    'apps.dashboard',
]

# Install authentication app first to override default User model
INSTALLED_APPS = [
    'apps.authentication',  # Must be first to override default User
] + DJANGO_APPS + THIRD_PARTY_APPS + [
    'apps.employees',
    'apps.devices',
    'apps.licenses',
    'apps.permissions',
    'apps.reports',
    'apps.dashboard',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'apps.authentication.middleware.SecurityLoggingMiddleware',
    'apps.authentication.middleware.RateLimitMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.authentication.middleware.SessionSecurityMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'asset_management.urls'

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

WSGI_APPLICATION = 'asset_management.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='asset_management'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Password validation
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
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'



# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'apps.authentication.serializers.CustomTokenObtainPairSerializer',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

CORS_ALLOW_CREDENTIALS = True

# LDAP Configuration
LDAP_SERVER_URI = config('LDAP_SERVER_URI', default='')
LDAP_BIND_DN = config('LDAP_BIND_DN', default='')
LDAP_BIND_PASSWORD = config('LDAP_BIND_PASSWORD', default='')
LDAP_USER_SEARCH_BASE = config('LDAP_USER_SEARCH_BASE', default='')

# Configure LDAP authentication if LDAP server is specified
if LDAP_SERVER_URI:
    import ldap
    from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
    
    # LDAP Server Configuration
    AUTH_LDAP_SERVER_URI = LDAP_SERVER_URI
    AUTH_LDAP_BIND_DN = LDAP_BIND_DN
    AUTH_LDAP_BIND_PASSWORD = LDAP_BIND_PASSWORD
    
    # LDAP User Search
    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        LDAP_USER_SEARCH_BASE or 'ou=users,dc=company,dc=com',
        ldap.SCOPE_SUBTREE,
        "(uid=%(user)s)"
    )
    
    # LDAP User Attribute Mapping
    AUTH_LDAP_USER_ATTR_MAP = {
        "first_name": "givenName",
        "last_name": "sn",
        "email": "mail",
        "employee_id": "employeeNumber",
        "department": "department",
        "position": "title",
        "phone_number": "telephoneNumber",
    }
    
    # LDAP Group Search (Optional)
    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
        config('LDAP_GROUP_SEARCH_BASE', default='ou=groups,dc=company,dc=com'),
        ldap.SCOPE_SUBTREE,
        "(objectClass=groupOfNames)"
    )
    AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()
    
    # LDAP User Flags
    AUTH_LDAP_USER_FLAGS_BY_GROUP = {
        "is_active": config('LDAP_ACTIVE_GROUP', default='cn=active,ou=groups,dc=company,dc=com'),
        "is_staff": config('LDAP_STAFF_GROUP', default='cn=staff,ou=groups,dc=company,dc=com'),
        "is_superuser": config('LDAP_ADMIN_GROUP', default='cn=admin,ou=groups,dc=company,dc=com'),
    }
    
    # LDAP Connection Options
    AUTH_LDAP_CONNECTION_OPTIONS = {
        ldap.OPT_DEBUG_LEVEL: 0,  # Set to 1 for debugging
        ldap.OPT_REFERRALS: 0,
        ldap.OPT_TIMEOUT: 30,
    }
    
    # Always update user from LDAP
    AUTH_LDAP_ALWAYS_UPDATE_USER = True
    
    # Cache LDAP groups for performance
    AUTH_LDAP_CACHE_TIMEOUT = 3600
    
    # Find group permissions
    AUTH_LDAP_FIND_GROUP_PERMS = True
    
    # Authentication Backends (LDAP first, then Django)
    AUTHENTICATION_BACKENDS = [
        'apps.authentication.backends.CustomLDAPBackend',
        'apps.authentication.backends.CustomModelBackend',
    ]
else:
    # Use only Django's default authentication backend
    AUTHENTICATION_BACKENDS = [
        'apps.authentication.backends.CustomModelBackend',
    ]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'