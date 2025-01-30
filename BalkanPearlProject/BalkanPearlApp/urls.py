from django.urls import path, include
from . import views  # импортируйте ваши представления

urlpatterns = [
    # Пример маршрута
    # path('some-path/', views.some_view, name='some_name'),
    path('', views.home, name='home'),
    path('apartments/', views.apartments_list, name='apartments_list'),
    path('booking/<int:apartment_id>/', views.booking_form, name='booking_form'),
    path('booking/calculate-price/<int:apartment_id>/', views.calculate_price, name='calculate_price'),
    path('booking/create/', views.create_booking, name='create_booking'),
    path('payment/<int:booking_id>/', views.payment_page, name='payment_page'),

    # Аутентификация
    path('accounts/', include('allauth.urls')),
    path('reviews/', views.reviews, name='reviews'),
    path('blog/', views.blog_home, name='blog_home'),
]
