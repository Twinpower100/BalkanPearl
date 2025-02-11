from django.urls import path, include
from django.views.generic import RedirectView

from . import views  # импортируйте ваши представления
from .views import calculate_price

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
    # Аутентификация
    # path('accounts/', include('allauth.urls')),
    path('reviews/', views.reviews, name='reviews'),
    path('reviews/create/', views.create_review, name='create_review'),
    path('blog/', views.blog_home, name='blog_home'),
    path('profile/', views.profile, name='profile'),
    path('accounts/profile/', RedirectView.as_view(url='/', permanent=False)),
]
