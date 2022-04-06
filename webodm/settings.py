"""
Django settings for webodm project.

Generated by 'django-admin startproject' using Django 1.10.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os, sys, json

import datetime

import tzlocal
from django.contrib.messages import constants as messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

try:
    from .secret_key import SECRET_KEY
except ImportError:
    # This will be executed the first time Django runs
    # It generates a secret_key.py file that contains the SECRET_KEY
    from django.utils.crypto import get_random_string

    current_dir = os.path.abspath(os.path.dirname(__file__))
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    secret = get_random_string(50, chars)
    with open(os.path.join(current_dir, 'secret_key.py'), 'w') as f:
        f.write("SECRET_KEY='{}'".format(secret))
    SECRET_KEY = secret

    print("Generated secret key")

with open(os.path.join(BASE_DIR, 'package.json')) as package_file:
    data = json.load(package_file)
    VERSION = data['version']

TESTING = sys.argv[1:2] == ['test']
FLUSHING = sys.argv[1:2] == ['flush']
MIGRATING = sys.argv[1:2] == ['migrate']
WORKER_RUNNING = sys.argv[2:3] == ["worker"]

# SECURITY WARNING: don't run with debug turned on a public facing server!
DEBUG = os.environ.get('WO_DEBUG', 'YES') == 'YES' or TESTING
DEV = os.environ.get('WO_DEV', 'NO') == 'YES' and not TESTING
DEV_WATCH_PLUGINS = DEV and os.environ.get('WO_DEV_WATCH_PLUGINS', 'NO') == 'YES'
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = os.environ.get('WO_SSL', 'NO') == 'YES'
INTERNAL_IPS = ['127.0.0.1']

ALLOWED_HOSTS = ['*']

# Branding
APP_NAME = "WebODM"
APP_DEFAULT_LOGO = os.path.join('app', 'static', 'app', 'img', 'logo512.png')

# In single user mode, a default admin account is created and automatically
# used so that no login windows are displayed
SINGLE_USER_MODE = False

# URL to redirect to if there are no processing nodes when visiting the dashboard
PROCESSING_NODES_ONBOARDING = None

# Enable the /api/users endpoint which is used for autocompleting
# usernames when handling project permissions. This can be disabled
# for security reasons if you don't want to let authenticated users
# retrieve the user list. 
ENABLE_USERS_API = True

# Enable desktop mode. In desktop mode some styling changes
# are applied to make the application look nicer on desktop
# as well as disabling certain features (e.g. sharing)
DESKTOP_MODE = False

# Default CSS to add to theme
DEFAULT_THEME_CSS = ''

# Plugins never to load
PLUGINS_BLACKLIST = [
    #'measure',
]

# Serve media static files URLs even in production
FORCE_MEDIA_STATICFILES = False

# AUTH0 Settings
SOCIAL_AUTH_TRAILING_SLASH = False  # Remove trailing slash from routes
SOCIAL_AUTH_AUTH0_DOMAIN = os.environ.get("WO_AUTH0_DOMAIN", "au-scalable-drone-cloud.au.auth0.com")
SOCIAL_AUTH_AUTH0_KEY = os.environ.get("WO_AUTH0_KEY", "be8iHLsWn2t6ZsyZh0UofW1oaWScfsfC")
SOCIAL_AUTH_AUTH0_SECRET = os.environ.get("WO_AUTH0_SECRET", "")
SOCIAL_AUTH_AUTH0_SCOPE = [
    'openid',
    'profile',
    'email'
]

SOCIAL_AUTH_PIPELINE = (
  'social_core.pipeline.social_auth.social_details',
  'social_core.pipeline.social_auth.social_uid',
  'social_core.pipeline.social_auth.social_user',
  'social_core.pipeline.user.get_username',
  'social_core.pipeline.social_auth.associate_by_email',
  'social_core.pipeline.user.create_user',
  'auth0.pipeline.cleanup_social_account', #Custom cleanup
  'social_core.pipeline.social_auth.associate_user',
  'social_core.pipeline.social_auth.load_extra_data',
  'social_core.pipeline.user.user_details',
)

# Shared encryption key - for encrypting stored strings shared between webapp and worker
# If not defined, will use the app secret key, but this is not reliable
# (eg: webapp and worker will have different secret keys unless they use the same filesystem volume)
ENCRYPTION_KEY = os.environ.get("WO_ENCRYPTION_KEY", SECRET_KEY)


# Application definition

INSTALLED_APPS = [
    'social_django',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django_filters',
    'guardian',
    'rest_framework',
    'rest_framework_nested',
    'drf_yasg',
    'webpack_loader',
    'corsheaders',
    'colorfield',
    'imagekit',
    'codemirror2',
    'compressor',
    'app',
    'nodeodm',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'auth0.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'webodm.urls'

WSGI_APPLICATION = 'webodm.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('WO_DATABASE_ENGINE', 'django.contrib.gis.db.backends.postgis'),
        'NAME': os.environ.get('WO_DATABASE_NAME', 'webodm_dev'),
        'USER': os.environ.get('WO_DATABASE_USER', 'postgres'),
        'PASSWORD': os.environ.get('WO_DATABASE_PASSWORD', 'postgres'),
        'HOST': os.environ.get('WO_DATABASE_HOST', 'db'),
        'PORT': os.environ.get('WO_DATABASE_PORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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

# Hook guardian
AUTHENTICATION_BACKENDS = (
    'social_core.backends.auth0.Auth0OAuth2',
    'django.contrib.auth.backends.ModelBackend', # this is default
    'guardian.backends.ObjectPermissionBackend',
    'django.contrib.auth.backends.RemoteUserBackend',
)

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = tzlocal.get_localzone().zone
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale')
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'build', 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'app', 'static'),
]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

# File Uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = 4718592 # 4.5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760 # 10 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'app.uploadhandler.TemporaryFileUploadHandler', # Ours doesn't keep file descriptors open by default
]

# Webpack
WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'app/bundles/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack-stats.json'),
    }
}


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            # 'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'WARNING',
        },
        'app.logger': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apscheduler.executors.default': {
            'handlers': ['console'],
            'level': 'WARNING',
        }
    }
}


# Auth
LOGIN_REDIRECT_URL = '/dashboard'
#LOGIN_URL = '/login/'
LOGIN_URL = '/login/auth0'

# CORS (very relaxed settings, users might want to change this in production)
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
SESSION_COOKIE_SAMESITE = None

# File uploads
MEDIA_ROOT = os.path.join(BASE_DIR, 'app', 'media')
if TESTING:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'app', 'media_test')
MEDIA_TMP = os.path.join(MEDIA_ROOT, 'tmp')

FILE_UPLOAD_TEMP_DIR = MEDIA_TMP

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'app', 'templates'),
            os.path.join(BASE_DIR, 'app', 'templates', 'app'),
            BASE_DIR,
            MEDIA_ROOT,
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app.contexts.settings.load',
                'social_django.context_processors.backends',
            ],
        },
    },
]

# Store flash messages in cookies
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
MESSAGE_TAGS = {
    messages.ERROR: 'danger' # Bootstrap 3 compatibility
}

# REST setup
# Use Django's standard django.contrib.auth permissions (no anonymous usage)
REST_FRAMEWORK = {
  'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.DjangoObjectPermissions',
  ],
  'DEFAULT_FILTER_BACKENDS': [
    'rest_framework_guardian.filters.ObjectPermissionsFilter',
    'django_filters.rest_framework.DjangoFilterBackend',
    'rest_framework.filters.OrderingFilter',
  ],
  'DEFAULT_AUTHENTICATION_CLASSES': (
    'rest_framework.authentication.SessionAuthentication',
    'rest_framework.authentication.BasicAuthentication',
    'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    'app.api.authentication.JSONWebTokenAuthenticationQS',
  ),
  'PAGE_SIZE': 10,
  'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
}

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(hours=6),
    'JWT_PAYLOAD_GET_USERNAME_HANDLER':
        'auth0.utils.jwt_get_username_from_payload_handler',
    'JWT_DECODE_HANDLER':
        'auth0.utils.jwt_decode_token',
    'JWT_ALGORITHM': 'RS256',
    'JWT_AUDIENCE': os.environ.get('WO_HOST') + 'api',
    'JWT_ISSUER': SOCIAL_AUTH_AUTH0_DOMAIN,
    'JWT_AUTH_HEADER_PREFIX': 'JWT',
}

# Compressor
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

# Sass
def theme(color):
    from app.contexts.settings import theme as f
    return f(color)


def complementary(color):
    from app.contexts.settings import complementary as f
    return f(color)


def scaleby(color, n):
    from app.contexts.settings import scaleby as f
    return f(color, n)


def scalebyiv(color, n):
    from app.contexts.settings import scaleby as f
    return f(color, n, True)


LIBSASS_CUSTOM_FUNCTIONS = {
    'theme': theme,
    'complementary': complementary,
    'scaleby': scaleby,
    'scalebyiv': scalebyiv
}

# Celery
CELERY_BROKER_URL = os.environ.get('WO_BROKER', 'redis://localhost')
CELERY_RESULT_BACKEND = os.environ.get('WO_BROKER', 'redis://localhost')

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_INCLUDE=['worker.tasks', 'app.plugins.worker']
CELERY_WORKER_REDIRECT_STDOUTS = False
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# Number of minutes a processing node hasn't been seen 
# before it should be considered offline
NODE_OFFLINE_MINUTES = 5 

if TESTING or FLUSHING:
    CELERY_TASK_ALWAYS_EAGER = True

try:
    from .local_settings import *
except ImportError:
    pass
