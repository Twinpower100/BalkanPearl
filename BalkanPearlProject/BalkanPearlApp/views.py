# -*- coding: utf-8 -*-
from allauth.account.views import LoginView
from django.core.exceptions import ValidationError
from allauth.core.internal.httpkit import redirect
from django.http import JsonResponse, HttpResponse
from django.templatetags.i18n import language
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from decouple import config  # Добавляем импорт config

from .forms import CustomLoginForm
from .models import Hotel, Apartment, Review, BlogPost, SiteImage, HotelPhoto, ApartmentPhoto, Booking
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django import forms
import emoji

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
    hotel = Hotel.objects.first()
    apartments = Apartment.objects.filter(is_closed=False)  # Получение всех открытых апартаментов
    apartments_with_photos = []
    for apartment in apartments:
        apartments_with_photos.append(
            {
                'apartment': apartment,
                'apartment_photos': ApartmentPhoto.objects.filter(apartment=apartment),
                'hotel': hotel,
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
    error = None

    if request.method == "POST":
        try:
            price = apartment.calculate_price(
                request.POST.get("check_in"),
                request.POST.get("check_out")
            )
        except ValidationError as e:
            error = e.message

    context = {
        "apartment": apartment,
        "error": error,
        # ... остальные данные ...
    }
    return render(request, "booking_form.html", context)





def blog_home(request):
    # Если есть модель блога, замените пустой список на запрос к базе
    blog_posts = BlogPost.objects.all()
    context = {
        'blog_posts': blog_posts,
    }
    return render(request, 'blog_home.html', context)


@login_required
def profile(request):
    return render(request, 'profile.html')


@login_required
def create_booking(request):
    if request.method == 'POST':
        apartment_id = request.POST.get('apartment_id')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')

        try:
            # Проверка обязательных полей
            if not all([apartment_id, check_in, check_out]):
                raise ValueError(_("Не все обязательные поля заполнены"))

            apartment = get_object_or_404(Apartment, id=apartment_id)

            # Парсинг дат
            check_in_date = timezone.datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = timezone.datetime.strptime(check_out, '%Y-%m-%d').date()

            # Валидация дат
            if check_in_date >= check_out_date:
                raise ValueError(_("Дата выезда должна быть позже даты заезда"))

            if check_in_date < timezone.now().date():
                raise ValueError(_("Дата заезда не может быть в прошлом"))

            # Проверка доступности
            if not apartment.is_available(check_in_date, check_out_date):
                messages.error(request, _("Апартамент занят на выбранные даты"))
                return redirect('booking_form', apartment_id=apartment_id)

            # Создание бронирования
            new_booking = Booking.objects.create(
                user=request.user,
                apartment=apartment,
                check_in=check_in_date,
                check_out=check_out_date
            )

            messages.success(request, _("Бронирование успешно создано!"))
            return redirect('booking_confirmation', booking_id=new_booking.id)

        except ValueError as e:
            print("ValueError:", str(e))  # Отладочное сообщение
            messages.error(request, str(e))
            return redirect('booking_form', apartment_id=apartment_id)
        except Exception as e:
            print("Exception:", str(e))  # Отладочное сообщение
            messages.error(request, _("Системная ошибка: ") + str(e))
            return redirect('booking_form', apartment_id=apartment_id)

    return redirect('home')


@login_required
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'booking_confirmation.html', {'booking': booking})


@login_required
def booking_details(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'booking.html', {'booking': booking})


@login_required
def profile(request):
    user_bookings = Booking.objects.filter(user=request.user, status='confirmed').order_by('check_in')
    return render(request, 'profile.html', {'user_bookings': user_bookings})


@login_required
@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    try:
        booking.cancel_booking(cancelled_by='user')
        messages.success(request, _("Бронирование успешно отменено."))
    except Exception as e:
        messages.error(request, _("Ошибка: ") + str(e))
    return redirect('profile')


def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    context = {
        'booking': booking,
        'stripe_public_key': 'ваш_публичный_ключ_stripe'  # Из settings.py
    }
    return render(request, 'payment.html', context)


def reviews(request):
    reviews_list = Review.objects.all()  # Получите список отзывов из базы данных
    context = {
        'reviews': reviews_list,
    }
    return render(request, 'reviews.html', context)

class ReviewForm(forms.ModelForm):
    anonymous = forms.BooleanField(required=False, label=_("Опубликовать анонимно"))

    class Meta:
        model = Review
        fields = ['apartment', 'rating', 'commentary', 'anonymous']
        widgets = {'commentary': forms.Textarea(attrs={'rows': 4, 'cols': 40})}

    def clean_commentary(self):
        commentary = self.cleaned_data['commentary']
        return emoji.emojize(commentary, language='alias')


@login_required
def create_review(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user  # Сохраняем автора комментария
            review.anonymous = form.cleaned_data['anonymous']  # Сохраняем выбор анонимности
            review.save()
            messages.success(request, _("Ваш отзыв успешно создан!"))
            return redirect('reviews')
    else:
        form = ReviewForm()

    return render(request, 'create_review.html', {'form': form})

# def login_view(request):
#     if request.method == 'POST':
#         form = CustomLoginForm(request.POST)
#         if form.is_valid():
#             # Обработка формы
#             form.login(request)
#             return redirect('profile')  # Укажите нужный редирект
#     else:
#         form = CustomLoginForm()
#     return render(request, 'login.html', {'form': form})

class CustomLoginView(LoginView):
    form_class = CustomLoginForm

    def get(self, request, *args, **kwargs):
        return HttpResponse("CustomLoginView works")


