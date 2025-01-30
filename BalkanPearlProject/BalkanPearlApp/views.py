from datetime import datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView
from allauth.core.internal.httpkit import redirect
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from decimal import Decimal
from decouple import config  # Добавляем импорт config
from .models import Hotel, Apartment, Review, BlogPost, SiteImage, HotelPhoto, ApartmentPhoto, Booking
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

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


def calculate_price(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')

    try:
        check_in_date = timezone.datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = timezone.datetime.strptime(check_out, '%Y-%m-%d').date()
        price = apartment.calculate_price(check_in_date, check_out_date)
        return JsonResponse({'price': price})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

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


@login_required
def create_booking(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    if request.method == 'POST':
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')

        if apartment.is_available(check_in, check_out):
            booking = Booking.objects.create(
                apartment=apartment,
                user=request.user,
                check_in=check_in,
                check_out=check_out
            )
            return redirect('payment_page', booking_id=booking.id)
        else:
            return JsonResponse({'error': 'Апартамент занят'}, status=400)

class BookingView(LoginRequiredMixin, FormView):
    login_url = '/accounts/login/'
    template_name = 'booking_form.html'


def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    context = {
        'booking': booking,
        'stripe_public_key': 'ваш_публичный_ключ_stripe'  # Из settings.py
    }
    return render(request, 'payment.html', context)
