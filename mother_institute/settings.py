"""
Django settings for mother_institute project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

import os
from django.core.exceptions import ImproperlyConfigured

# simple env helper
def env(key, default=None, required=False):
    v = os.getenv(key, default)
    if required and (v is None or v == ''):
        raise ImproperlyConfigured(f"Missing required env var: {key}")
    return v

# NOTE: for quick local testing a default is provided; set DJANGO_SECRET_KEY in production
SECRET_KEY = env('DJANGO_SECRET_KEY', 'django-insecure-=-g9@hs+9m+yl+jwOb!j68i_@8l*v$3jwloqk4cfn$ggr8e6o7')
DEBUG = env('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'yes')
ALLOWED_HOSTS = [h.strip() for h in env('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third-party
    'rest_framework',
    'corsheaders',

    # local apps
    'institute',
    'crispy_forms',
    'crispy_bootstrap4',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'
# If you use WhiteNoise for static files in production, STATICFILES_STORAGE is set below.

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise should be directly after SecurityMiddleware when used
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mother_institute.urls' 

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'institute.views.organization_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'mother_institute.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'institute.CustomUser'

# Login/Logout URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# CORS / API / production helpers
# Allow Streamlit (local and Streamlit Cloud) to call the API — override via env in production
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8501',
    'http://127.0.0.1:8501',
    'https://share.streamlit.io',
]
# Example for CSRF trusted origins (enable/override in production):
# CSRF_TRUSTED_ORIGINS = ['https://yourdomain.com']

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly'
    ]
}

# WhiteNoise: compressed static files served directly by the Django app (good for simple deployments)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'