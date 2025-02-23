# C:\Mail.ru\CodeIt\Django\BalkanPearl\BalkanPearlProject\BalkanPearlProject\urls.py
"""
URL configuration for BalkanPearlProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# -*- coding: utf-8 -*-
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include
from django.views.i18n import set_language
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # URL для переключения языка
    path('set_language/', set_language, name='set_language'),
    path('i18n/', include('django.conf.urls.i18n')),
]

# Основные маршруты приложения с поддержкой i18n
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('BalkanPearlApp.urls')),  # Ваше приложение

)
urlpatterns += [
    path('accounts/', include('allauth.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)