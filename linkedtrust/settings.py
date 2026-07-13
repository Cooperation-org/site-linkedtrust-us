import os
import mimetypes
from pathlib import Path
from decouple import config

# Browsers only apply an XSL stylesheet if the .xsl is served with an XML-ish
# MIME type (octet-stream is rejected) — needed for the pretty sitemap.
mimetypes.add_type('text/xsl', '.xsl')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = config('SECRET_KEY', default='django-insecure-h-sr3w1qhe3pbbgl34lz)_au%yt^5gw^8+^jo!^x9lkb-cj+ls')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['linkedtrust.us', 'www.linkedtrust.us', 'demos.linkedtrust.us', '127.0.0.1', 'localhost']

CSRF_TRUSTED_ORIGINS = ['https://linkedtrust.us', 'https://demos.linkedtrust.us']

# Google Search Console site-verification token (public; rendered in <head>).
# Override or blank out per environment via the GSC_VERIFICATION env var.
GSC_VERIFICATION = config('GSC_VERIFICATION', default='FhyuK7HCSUVK1OVSTkzzzj__lXFG2Iec8-wOk3JgP_4')

# IndexNow key (public — served as a verification file at /<KEY>.txt).
# Used to push new/changed URLs to Bing/Yandex (and thus ChatGPT Search /
# Copilot, which ground on the Bing index). 32-char lowercase hex.
# Override per environment via the INDEXNOW_KEY env var.
INDEXNOW_KEY = config('INDEXNOW_KEY', default='cfbac5dcbf374555a73f256170b10951')

# When proxied under a subdir (e.g. demos.linkedtrust.us/site-dev/)
# set SCRIPT_NAME=/site-dev to fix URL generation
FORCE_SCRIPT_NAME = config('SCRIPT_NAME', default=None)

# LinkedTrust claims API used by the earnedgov commitment wall/invite pages.
# Point at https://dev.linkedtrust.us when testing so no claims hit live.
EARNEDGOV_LT_API = config('EARNEDGOV_LT_API', default='https://live.linkedtrust.us')

# GovKit (the accelerator dashboard) — base URL used to validate magic invite
# tokens and to hand committed invitees into the SSO accept flow. Point at the
# cohort VM's govkit when it exists; demo meanwhile.
GOVKIT_BASE_URL = config('GOVKIT_BASE_URL', default='https://demos.linkedtrust.us/govkit')
# Where the post-commit dashboard button on the wall banner points (optional).
EARNEDGOV_DASHBOARD_URL = config('EARNEDGOV_DASHBOARD_URL', default='')
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
    'django.contrib.sitemaps',
    'website',
]

# Only use whitenoise.runserver_nostatic in production
if not DEBUG:
    INSTALLED_APPS.insert(6, 'whitenoise.runserver_nostatic')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Runs last on the response path → stamps CSP / Link / nosniff headers on
    # every response, including static files served by WhiteNoise below.
    'website.middleware.SecurityHeadersMiddleware',
    'website.middleware.MarkdownNegotiationMiddleware',
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
                'website.context_processors.site_meta',
            ],
        },
    },
]

WSGI_APPLICATION = 'linkedtrust.wsgi.application'

# --- Security headers ---------------------------------------------------------
# Native headers handled by Django (SecurityMiddleware / XFrameOptionsMiddleware).
# CSP, Permissions-Policy and Link headers are added by website.middleware.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'SAMEORIGIN'

# SSL terminates at Caddy/nginx; trust the forwarded-proto header so
# request.is_secure() is correct (drives HSTS + canonical https URLs).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS + secure cookies only in production (HTTPS). Never in local dev.
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

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
    # CompressedStaticFilesStorage serves from static/ without collectstatic
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    # WhiteNoise Compression and Caching Settings
    WHITENOISE_AUTOREFRESH = True
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_ALLOW_ALL_ORIGINS = True
    # Maximum age for static files (30 days)
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