from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404
from decimal import Decimal
from decouple import config  # Добавляем импорт config
from .models import Hotel, Apartment, Review, BlogPost, SiteImage, HotelPhoto, ApartmentPhoto

"""Делаем по запросу поиска"""
def home(request):
    hotel = Hotel.objects.first()  # Выберите отель
    search_query = f"{hotel.name}, {hotel.address}" if hotel else "Unknown location"
    site_image = SiteImage.objects.last()
    hotel_photos = HotelPhoto.objects.filter(hotel=hotel)
    return render(request, 'home.html', {
        'hotel': hotel,
        'google_maps_key': config('GOOGLE_MAPS_KEY'),
        'search_query': search_query,  # Передаём строку поиска в контекст
        'site_image': site_image,
        'hotel_photos': hotel_photos,
    })

def apartments_list(request):
    apartments = Apartment.objects.all()  # Получение всех апартаментов
    apartments_with_photos = []
    for apartment in apartments:
        apartments_with_photos.append(
            {
                'apartment': apartment,
                'apartment_photos': ApartmentPhoto.objects.filter(apartment=apartment)
            }
        )

    context = {
        'apartments_with_photos': apartments_with_photos
    }
    return render(request, 'apartments_list.html', context)

def booking_form(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    context = {
        'apartment': apartment,
    }
    return render(request, 'booking_form.html', context)

def reviews(request):
    reviews_list = Review.objects.all()  # Получите список отзывов из базы данных
    context = {
        'reviews': reviews_list,
    }
    return render(request, 'reviews.html', context)

def blog_home(request):
    # Если есть модель блога, замените пустой список на запрос к базе
    blog_posts = BlogPost.objects.all()
    context = {
        'blog_posts': blog_posts,
    }
    return render(request, 'blog_home.html', context)

