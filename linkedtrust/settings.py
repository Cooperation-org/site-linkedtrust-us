import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = config('SECRET_KEY', default='django-insecure-h-sr3w1qhe3pbbgl34lz)_au%yt^5gw^8+^jo!^x9lkb-cj+ls')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['linkedtrust.us', 'www.linkedtrust.us', 'demos.linkedtrust.us', '127.0.0.1', 'localhost']

CSRF_TRUSTED_ORIGINS = ['https://linkedtrust.us', 'https://demos.linkedtrust.us']

# When proxied under a subdir (e.g. demos.linkedtrust.us/site-dev/)
# set SCRIPT_NAME=/site-dev to fix URL generation
FORCE_SCRIPT_NAME = config('SCRIPT_NAME', default=None)
if FORCE_SCRIPT_NAME == '':
    FORCE_SCRIPT_NAME = None

# Scope cookies to the subpath so multiple Django apps on the same domain
# (e.g. alonovo, newsite) don't clobber each other's sessions
if FORCE_SCRIPT_NAME:
    SESSION_COOKIE_PATH = FORCE_SCRIPT_NAME + '/'
    CSRF_COOKIE_PATH = FORCE_SCRIPT_NAME + '/'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'website',
]

# Only use whitenoise.runserver_nostatic in production
if not DEBUG:
    INSTALLED_APPS.insert(6, 'whitenoise.runserver_nostatic')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'linkedtrust.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'website/templates')],
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

WSGI_APPLICATION = 'linkedtrust.wsgi.application'

# Database — shared PostgreSQL instance
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'linkedtrust_site',
        'USER': config('PG_USER', default='cobox'),
        'PASSWORD': config('PG_PASSWORD', default=''),
        'HOST': config('PG_HOST', default='10.0.0.100'),
        'PORT': config('PG_PORT', default='5432'),
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# Static URL — prefixed when behind subdir proxy
_script = FORCE_SCRIPT_NAME or ''
STATIC_URL = f'{_script}/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = f'{_script}/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# WhiteNoise Configuration (only for production)
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    # WhiteNoise Compression and Caching Settings
    WHITENOISE_AUTOREFRESH = True
    WHITENOISE_USE_FINDERS = False
    WHITENOISE_MANIFEST_STRICT = False
    WHITENOISE_ALLOW_ALL_ORIGINS = True
    # Maximum age for static files (30 days )
    WHITENOISE_MAX_AGE = 30 * 24 * 60 * 60


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='emosmwangi@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'LinkedTrust <emosmwangi@gmail.com>'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)