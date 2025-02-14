# -*- coding: utf-8 -*-
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from django.views.generic import RedirectView
from . import views  # импортируйте ваши представления
from .views import calculate_price, CustomLoginView, CustomLogoutView, login_form, google_login
from allauth.socialaccount.providers.google.views import oauth2_login

urlpatterns = [
    # Пример маршрута
    # path('some-path/', views.some_view, name='some_name'),
    path('', views.home, name='home'),
    path('apartments/', views.apartments_list, name='apartments_list'),
    path('booking/<int:apartment_id>/', views.booking_form, name='booking_form'),
    path('booking/calculate-price/<int:apartment_id>/', views.calculate_price, name='calculate_price'),
    path('booking/create/', views.create_booking, name='create_booking'),
    path('booking/confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),  # Перенаправляем на страницу подтверждения
    path('booking/<int:booking_id>/', views.booking_details, name='booking_details'),
    path('booking/calculate-price/<int:apartment_id>/', calculate_price, name='calculate-price'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('payment/<int:booking_id>/', views.payment_page, name='payment_page'),
    path('reviews/', views.reviews, name='reviews'),
    path('reviews/create/', views.create_review, name='create_review'),
    path('blog/', views.blog_home, name='blog_home'),
    path('profile/', views.profile, name='profile'),
    path('accounts/', include('allauth.urls')),  # Подключение allauth
    path('login-form/', login_form, name='login_form'),
    #path('accounts/google/login/', oauth2_login, name='google_login'),  # Кастомный маршрут
    path('accounts/google/login/', google_login, name='google_login'),  # Кастомный маршрут

    # path('accounts/profile/', RedirectView.as_view(url='/', permanent=False)),
    # path('accounts/login/', CustomLoginView.as_view(),name="account_login"),
    # path('accounts/logout/', LogoutView.as_view(), name='account_logout'),
]
