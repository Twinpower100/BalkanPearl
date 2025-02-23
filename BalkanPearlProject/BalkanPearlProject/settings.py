# C:\Mail.ru\CodeIt\Django\BalkanPearl\BalkanPearlProject\BalkanPearlProject\settings.py
"""
Django settings for BalkanPearlProject project.

Generated by 'django-admin startproject' using Django 5.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
# -*- coding: utf-8 -*-

from pathlib import Path
from decouple import config
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')
GOOGLE_MAPS_KEY = config('GOOGLE_MAPS_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
SITE_ID = 1
LOGIN_URL = 'account_login'  # Путь на страницу входа
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'  # Перенаправление после выхода

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'BalkanPearlApp',
    'phonenumber_field',
    'phonenumbers',
    #'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # 'allauth.socialaccount.providers.facebook',
    # 'allauth.socialaccount.providers.microsoft',
    # 'allauth.socialaccount.providers.instagram',
    # 'allauth.socialaccount.providers.apple',

]
INSTALLED_APPS += ['modeltranslation']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # для мультиязычности
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

LANGUAGES = [
    ('en', _('English')),
    ('ru', _('Russian')),
    ('me', _('Montenegrian')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]



ROOT_URLCONF = 'BalkanPearlProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Используем Path вместо os.path.join
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',  # Это важно для мультиязычности
                'BalkanPearlApp.context_processors.site_image', # Это важно для отображения загруженного рисунка на всех страницах

            ],
        },
    },
]

WSGI_APPLICATION = 'BalkanPearlProject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

#LANGUAGE_CODE = 'en'
LANGUAGE_CODE = 'ru-ru'
USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
DECIMAL_SEPARATOR = ','


TIME_ZONE = 'Europe/Podgorica'

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATICFILES_DIRS = [
    BASE_DIR / 'static',  # Используем Path вместо os.path.join
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Используем Path вместо os.path.join

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # Используем Path вместо os.path.join
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID'),
            'secret': config('GOOGLE_SECRET'),
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'}
    },
    # На фейсбук надо регистрировать фирму
    # 'facebook': {
    #     'APP': {
    #         'client_id': config('FACEBOOK_APP_ID'),
    #         'secret': config('FACEBOOK_SECRET'),
    #     }
    # },
    # 'instagram': {
    #     'APP': {
    #         'client_id': config('INSTAGRAM_CLIENT_ID'),
    #         'secret': config('INSTAGRAM_SECRET'),
    #     }
    # },
    # 'microsoft': {
    #     'APP': {
    #         'client_id': config('MICROSOFT_CLIENT_ID'),
    #         'secret': config('MICROSOFT_SECRET'),
    #     }
    # },

    # Apple - платно
    # 'apple': {
    #     'APP': {
    #         'client_id': config('APPLE_CLIENT_ID'),
    #         'secret': config('APPLE_SECRET'),
    #         'key': config('APPLE_KEY'),
    #         'certificate_key': config('APPLE_CERTIFICATE_KEY'),
    #     }
    # }
}
# Мы пользуемся кастомной формой аутентификации
ACCOUNT_FORMS = {"login": "BalkanPearlApp.forms.CustomLoginForm"}
ACCOUNT_ADAPTER = "BalkanPearlApp.adapter.CustomAccountAdapter"
