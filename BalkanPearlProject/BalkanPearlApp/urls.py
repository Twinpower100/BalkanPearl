from django.urls import path
from . import views  # импортируйте ваши представления

urlpatterns = [
    # Пример маршрута
    # path('some-path/', views.some_view, name='some_name'),
    path('', views.home, name='home'),
    path('apartments/', views.apartments_list, name='apartments_list'),
    path('booking/<int:apartment_id>/', views.booking_form, name='booking_form'),
    path('reviews/', views.reviews, name='reviews'),
    path('blog/', views.blog_home, name='blog_home'),
]
