# C:\Mail.ru\CodeIt\Django\BalkanPearl\BalkanPearlProject\BalkanPearlApp\views.py
# -*- coding: utf-8 -*-
from allauth.account.views import LoginView
from django.contrib.auth.views import LogoutView
from django.core.exceptions import ValidationError
from allauth.core.internal.httpkit import redirect
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.templatetags.i18n import language
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from decouple import config  # Добавляем импорт config
from allauth.socialaccount.providers.google.views import oauth2_login
from .forms import CustomLoginForm
from .models import Hotel, Apartment, Review, BlogPost, SiteImage, HotelPhoto, ApartmentPhoto, Booking
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django import forms
import emoji
from django.shortcuts import render, get_object_or_404, redirect
from itertools import combinations

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
        'apartments_with_photos': apartments_with_photos,
        'hotel': hotel
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
    hotel = Hotel.objects.first()
    apartment = get_object_or_404(Apartment, id=apartment_id)
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
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
        "check_in": check_in,
        "check_out": check_out,
        "error": error,
        'hotel': hotel
    }
    return render(request, "booking_form.html", context)


def blog_home(request):
    # Если есть модель блога, замените пустой список на запрос к базе
    hotel = Hotel.objects.first()
    blog_posts = BlogPost.objects.all()
    context = {
        'blog_posts': blog_posts,
        'hotel': hotel
    }
    return render(request, 'blog_home.html', context)


@login_required
def profile(request):
    hotel = Hotel.objects.first()
    context = {
        'hotel': hotel
    }
    return render(request, 'profile.html', context)


@login_required
def create_booking(request):
    if request.method == 'POST':
        apartment_id = request.POST.get('apartment_id')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        people_quantity = int(request.POST.get('people_quantity', 1))  # Получаем количество гостей

        try:
            # Проверка обязательных полей
            if not all([apartment_id, check_in, check_out]):
                raise ValueError(_("Не все обязательные поля заполнены"))

            apartment = get_object_or_404(Apartment, id=apartment_id)

            # Проверка количества гостей
            if people_quantity > apartment.capacity:
                raise ValueError(_("Количество гостей превышает вместимость апартамента"))

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
                check_out=check_out_date,
                people_quantity=people_quantity, # Сохраняем количество гостей
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
    hotel = Hotel.objects.first()
    context = {
        'booking': booking,
        'hotel': hotel
    }
    return render(request, 'booking_confirmation.html', context)


@login_required
def booking_details(request, booking_id):
    hotel = Hotel.objects.first()
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    context = {
        'booking': booking,
        'hotel': hotel,
    }
    return render(request, 'booking.html', context)


@login_required
def profile(request):
    hotel = Hotel.objects.first()
    user_bookings = Booking.objects.filter(user=request.user, status='confirmed').order_by('check_in')
    context = {
        'user_bookings': user_bookings,
        'hotel': hotel,
    }
    return render(request, 'profile.html', context)


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
    hotel = Hotel.objects.first()
    context = {
        'booking': booking,
        'hotel': hotel,
        'stripe_public_key': 'ваш_публичный_ключ_stripe'  # Из settings.py
    }
    return render(request, 'payment.html', context)


def reviews(request):
    hotel = Hotel.objects.first()
    reviews_list = Review.objects.all()  # Получите список отзывов из базы данных
    context = {
        'reviews': reviews_list,
        'hotel': hotel,
    }
    return render(request, 'reviews.html', context)


class ReviewForm(forms.ModelForm):
    anonymous = forms.BooleanField(required=False, label=_("Опубликовать анонимно"))
    hotel = Hotel.objects.first()

    class Meta:
        model = Review
        fields = ['apartment', 'rating', 'commentary', 'anonymous']
        widgets = {'commentary': forms.Textarea(attrs={'rows': 4, 'cols': 40})}

    def clean_commentary(self):
        commentary = self.cleaned_data['commentary']
        return emoji.emojize(commentary, language='alias')


@login_required
def create_review(request):
    hotel = Hotel.objects.first()
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

    return render(request, 'create_review.html', {'form': form, 'hotel': hotel,})


from .models import SiteImage


class CustomLoginView(LoginView):
    form_class = CustomLoginForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_image'] = SiteImage.objects.first()  # Первое изображение из модели
        return context


class CustomLogoutView(LogoutView):
    template_name = 'account/logout.html'
    extra_context = {'site_image': SiteImage.objects.first()}

def login_form(request):
    return render(request, 'account/login_form.html')

def google_login(request):
    return render(request, 'account/google_login.html')

@login_required
def booking_wizard(request):
    hotel = Hotel.objects.first()
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
    people_quantity = int(request.GET.get('people_quantity', 1))

    # Если даты не переданы, отображаем форму для их ввода
    if not check_in or not check_out:
        return render(request, 'booking_wizard.html', {'show_form': True, 'hotel': hotel})

    # Проверяем, что даты корректны
    try:
        check_in_date = timezone.datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = timezone.datetime.strptime(check_out, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Некорректный формат даты'}, status=400)

    apartments = Apartment.objects.filter(is_closed=False)
    available_apartments = []
    for apartment in apartments:
        if apartment.is_available(check_in_date, check_out_date):
            price = apartment.calculate_price(check_in_date, check_out_date)
            photos = ApartmentPhoto.objects.filter(apartment=apartment)
            available_apartments.append({
                'id': apartment.id,
                'number': apartment.number,
                'description': apartment.description,
                'price': price,
                'photos': [{'photo': photo.photo.url} for photo in photos],
                'hotel': hotel
            })

    return render(request, 'booking_wizard.html', {
        'apartments': available_apartments,
        'check_in': check_in,
        'check_out': check_out,
        'people_quantity': people_quantity,
        'show_form': False,
        'hotel': hotel,
    })



@login_required
def booking_wizard1(request):
    hotel = Hotel.objects.first()
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
    people_quantity = int(request.GET.get('people_quantity', 1))

    if not check_in or not check_out:
        return render(request, 'booking_wizard1.html', {'show_form': True, 'hotel': hotel})

    try:
        check_in_date = timezone.datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = timezone.datetime.strptime(check_out, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Некорректный формат даты'}, status=400)

    available_apartments = list(Apartment.objects.filter(is_closed=False))

    # Фильтруем доступные апартаменты на выбранные даты
    available_apartments = [
        apt for apt in available_apartments
        if apt.is_available(check_in_date, check_out_date)
    ]

    if not available_apartments:
        return render(request, 'booking_wizard1.html', {
            'show_form': False,
            'hotel': hotel,
            'no_apartments_available': True,
            'check_in': check_in,
            'check_out': check_out,
            'people_quantity': people_quantity,
        })


    apartment_blocks = create_apartment_blocks(available_apartments, people_quantity, check_in_date, check_out_date)
    for block in apartment_blocks:
        for apartment in block['apartments']:
            apartment.photos = ApartmentPhoto.objects.filter(apartment=apartment)
    # Сортируем блоки по общей стоимости
    apartment_blocks.sort(key=lambda block: block['total_price'])

    context = {
        'apartment_blocks': apartment_blocks,
        'check_in': check_in,
        'check_out': check_out,
        'people_quantity': people_quantity,
        'show_form': False,
        'hotel': hotel,
    }
    return render(request, 'booking_wizard1.html', context)


# def create_apartment_blocks(available_apartments, people_quantity, check_in_date, check_out_date):
#     """
# Создает блоки апартаментов, комбинируя различные варианты,
# и сортирует их по общей стоимости.
#     """
#     possible_blocks = []
#     min_block_capacity = people_quantity
#
#     # 1. Генерируем все возможные комбинации апартаментов (подмножества)
#     for block_size in range(1, len(available_apartments) + 1): # Рассматриваем блоки размером от 1 до всех доступных номеров
#         for apartment_combination in combinations(available_apartments, block_size):
#             block_capacity = sum(apt.capacity for apt in apartment_combination)
#
#             if block_capacity >= min_block_capacity: # 2. Фильтруем комбинации по вместимости
#                 block_price = sum(apt.calculate_price(check_in_date, check_out_date) for apt in apartment_combination)
#                 possible_blocks.append({
#                     'apartments': list(apartment_combination), # Преобразуем tuple в list для удобства шаблона
#                     'total_capacity': block_capacity,
#                     'total_price': block_price,
#                     'num_apartments': len(apartment_combination) # Добавляем количество апартаментов в блоке
#                 })
#
#     # 3. Сортировка по цене (уже делается в booking_wizard1 представлении после вызова этой функции)
#     # 4. Возврат отсортированных блоков
#     return possible_blocks

def create_apartment_blocks(available_apartments, people_quantity, check_in_date, check_out_date):
    # Сортируем по вместимости (сначала самые большие)
    sorted_apartments = sorted(
        available_apartments,
        key=lambda x: (-x.capacity, x.calculate_price(check_in_date, check_out_date))
    )

    # Вычисляем минимальное количество номеров
    max_capacity = max([apt.capacity for apt in sorted_apartments], default=0)
    min_apartments = (people_quantity // max_capacity) + 1 if max_capacity > 0 else 0

    blocks = []

    # Перебираем возможные комбинации
    for n in range(min_apartments, len(sorted_apartments) + 1):
        for combo in combinations(sorted_apartments, n):
            total_capacity = sum(apt.capacity for apt in combo)

            if total_capacity >= people_quantity:
                # Проверка доступности всех в комбинации
                if all(apt.is_available(check_in_date, check_out_date) for apt in combo):
                    price = sum(apt.calculate_price(check_in_date, check_out_date) for apt in combo)
                    blocks.append({
                        'apartments': combo,
                        'total_price': price,
                        'total_capacity': total_capacity,
                        'num_apartments': n
                    })
        # Прерываем, если нашли варианты
        if blocks:
            break

    # Сортируем по цене и вместимости
    blocks.sort(key=lambda x: (x['total_price'], -x['total_capacity']))

    return blocks[:5]  # Ограничиваем до 5 вариантов


@transaction.atomic
def create_booking_from_block(request):
    if request.method == 'POST':
        try:
            apartment_ids = request.POST.getlist('apartment_ids')
            check_in = request.POST.get('check_in')
            check_out = request.POST.get('check_out')
            people_quantity = int(request.POST.get('people_quantity', 1))

            # 1. Блокировка записей для проверки доступности
            apartments = Apartment.objects.select_for_update().filter(
                id__in=apartment_ids,
                is_closed=False
            )

            # 2. Проверка что все ID валидны
            if len(apartments) != len(apartment_ids):
                raise ValidationError("Некоторые апартаменты не найдены или закрыты")

            # 3. Проверка доступности каждого апартамента
            for apartment in apartments:
                if not apartment.is_available(check_in, check_out):
                    raise ValidationError(f"Апартамент {apartment.number} занят")

            # 4. Создание бронирований
            bookings = [
                Booking(
                    user=request.user,
                    apartment=apartment,
                    check_in=check_in,
                    check_out=check_out,
                    people_quantity=people_quantity,
                    status='confirmed'
                ) for apartment in apartments
            ]

            # 5. Сохранение всех бронирований одним запросом
            Booking.objects.bulk_create(bookings)

            messages.success(request, "Все апартаменты успешно забронированы!")
            return redirect('booking_confirmation')

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('booking_wizard1')

        except Exception as e:
            messages.error(request, f"Ошибка бронирования: {str(e)}")
            return redirect('booking_wizard1')

    return redirect('home')