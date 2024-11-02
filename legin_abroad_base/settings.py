"""
Django settings for legin_abroad_base project.

Generated by 'django-admin startproject' using Django 5.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os
from .env_handler import var_getter

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = var_getter("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['leginabroad.com']

X_FRAME_OPTIONS = 'SAMEORIGIN'
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap4',
    'imagekit',
    'storages',  #aws
    'taggit',
    'ckeditor',
    'ckeditor_uploader',
    'legin_abroad.apps.LeginAbroadConfig',
    'en_legin_abroad.apps.EnLeginAbroadConfig'
]

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"
CKEDITOR_IMAGE_BACKEND = "pillow"
CKEDITOR_BROWSE_SHOW_DIRS = True
# SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
CKEDITOR_CONFIGS = {
    'default': {
        'width': 'auto',
        'height': 600,
        'toolbar': 'Custom',
        # 'extraAllowedContent': 'iframe[*]{*}(*);',
        'allowedContent': True,
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['Font', 'FontSize', 'TextColor', 'BGColor'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-',
             'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink', 'Anchor'],
            ['Table', 'HorizontalRule'],
            ['Smiley', 'SpecialChar'],
            ['RemoveFormat', 'Source', 'CodeSnippet', 'Image', 'Youtube'],
            ['Maximize']
        ],
        'extraPlugins': ','.join(['codesnippet', 'youtube'])
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware'
]

ROOT_URLCONF = 'legin_abroad_base.urls'

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

WSGI_APPLICATION = 'legin_abroad_base.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': var_getter('POSTGRESQL_NAME'),
        'USER': var_getter('POSTGRESQL_USER'),
        'PASSWORD': var_getter('POSTGRESQL_PASSWORD'),
        'HOST': var_getter('HOST_NAME'),
        'PORT': var_getter('PORT')
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/


# STATICFILES_DIRS = [BASE_DIR / 'static']
# MEDIA_URL = '/media/'
# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# settings for django-bootstrap4
BOOTSTRAP4 = {
    'include_jquery': True
}
# TODO get this in order after migrations and before deployment

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

AWS_ACCESS_KEY_ID = var_getter('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = var_getter('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = var_getter('AWS_STORAGE_BUCKET_NAME')
AWS_S3_SIGNATURE_NAME = var_getter("AWS_S3_SIGNATURE_NAME")
AWS_S3_REGION_NAME = var_getter("AWS_S3_REGION_NAME")
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False  # this removes authentication query parameter from generated URLs for images from s3
# AWS_DEFAULT_ACL =  None
# AWS_S3_VERIFY = True


STORAGES = {
    # Media file (image) management
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',  # Log all messages at DEBUG level and above
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'ERROR',  # Log errors to a file
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django_error.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],  # Output logs to console and file
            'level': 'DEBUG',  # Set log level to DEBUG for detailed information
            'propagate': True,
        },
    },
}

