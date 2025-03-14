# C:\Mail.ru\CodeIt\Django\BalkanPearl\BalkanPearlProject\BalkanPearlApp\views.py
# -*- coding: utf-8 -*-
import datetime
from datetime import timedelta

from allauth.account.views import LoginView
from django.contrib.auth.views import LogoutView
from django.core.exceptions import ValidationError
from allauth.core.internal.httpkit import redirect
from django.db import transaction
from django.http import JsonResponse
from django.templatetags.i18n import language
from django.utils import timezone
from decouple import config  # Добавляем импорт config
from allauth.socialaccount.providers.google.views import oauth2_login
from BalkanPearlApp.forms import CustomLoginForm
from BalkanPearlApp.models import Hotel, Apartment, Review, BlogPost, SiteImage, HotelPhoto, ApartmentPhoto, Booking
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django import forms
import emoji
from django.shortcuts import render, get_object_or_404, redirect
from itertools import combinations
from decimal import Decimal
from django.urls import reverse

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
        'no_description': _("No description available"),
    })


def apartments_list(request):
    hotel = Hotel.objects.first()

    # Получение GET параметров для фильтрации и сортировки
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_order = request.GET.get('sort_order')
    if sort_order:
        sort_order = sort_order.strip().lower()
    else:
        sort_order = ""
    only_available = request.GET.get('only_available')  # будет присутствовать, если чекбокс установлен

    apartments_qs = Apartment.objects.filter(is_closed=False)
    apartments_with_photos = []

    # Вычисляем сегодняшнюю и завтрашнюю даты для установки значений по умолчанию
    today = datetime.datetime.today().date()
    tomorrow = today + timedelta(days=1)

    # Если даты не заданы, устанавливаем значения по умолчанию
    if not check_in:
        check_in = today.strftime('%Y-%m-%d')
    if not check_out:
        check_out = tomorrow.strftime('%Y-%m-%d')

    # Если даты указаны, пытаемся их распарсить
    try:
        check_in_date = datetime.datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.datetime.strptime(check_out, '%Y-%m-%d').date()
    except ValueError:
        check_in_date = check_out_date = None

    # Проверка корректности выбранных дат
    validation_error = ""
    if not (check_in_date and check_out_date):
        validation_error = _("Пожалуйста, заполните обе даты")
    elif check_in_date < today:
        validation_error = _("Дата заезда не может быть в прошлом")
    elif check_in_date >= check_out_date:
        validation_error = _("Дата выезда должна быть позже даты заезда")

    for apartment in apartments_qs:
        if not (check_in_date and check_out_date):
            calculated_price = None
            available = None
            error_message = _("Введите корректные даты")
        else:
            try:
                calculated_price = apartment.calculate_price(check_in_date, check_out_date)
                available = apartment.is_available(check_in_date, check_out_date)
                error_message = ""
            except (ValidationError, TypeError) as e:
                calculated_price = None
                available = None
                error_message = e.messages[0] if hasattr(e, 'messages') and e.messages else str(e)

        apt_dict = {
            'apartment': apartment,
            'apartment_photos': ApartmentPhoto.objects.filter(apartment=apartment),
            'hotel': hotel,
            'calculated_price': calculated_price,
            'available': available,
            'error': error_message,
        }
        apartments_with_photos.append(apt_dict)

    # Фильтрация по цене и доступности, если даты указаны
    if check_in_date and check_out_date:
        filtered = []
        for apt in apartments_with_photos:
            price = apt.get('calculated_price')
            available = apt.get('available')

            if only_available and available is not None:
                if not available:
                    continue

            if price is not None:
                if min_price:
                    try:
                        if price < float(min_price):
                            continue
                    except ValueError:
                        pass
                if max_price:
                    try:
                        if price > float(max_price):
                            continue
                    except ValueError:
                        pass
            filtered.append(apt)
        apartments_with_photos = filtered

        try:
            if sort_order == 'asc':
                apartments_with_photos = sorted(apartments_with_photos,
                                                key=lambda x: float(x.get('calculated_price') or 0))
            elif sort_order == 'desc':
                apartments_with_photos = sorted(apartments_with_photos,
                                                key=lambda x: float(x.get('calculated_price') or 0), reverse=True)
        except Exception as e:
            print("Sorting error:", e)

    context = {
        'apartments_with_photos': apartments_with_photos,
        'hotel': hotel,
        'check_in': check_in,
        'check_out': check_out,
        'min_price': min_price,
        'max_price': max_price,
        'sort_order': sort_order,
        'only_available': only_available,
        'today': today,
        'tomorrow': tomorrow,
        'validation_error': validation_error,
    }
    return render(request, 'apartments_list.html', context)


def calculate_price(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')

    if not check_in or not check_out:
        return JsonResponse({'error': 'Missing check_in or check_out parameters'}, status=400)

    try:
        check_in_date = timezone.datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = timezone.datetime.strptime(check_out, '%Y-%m-%d').date()

        if check_in_date >= check_out_date:
            return JsonResponse({'error': _('Check-out date must be after check-in')}, status=400)
        if check_in_date < timezone.now().date():
            return JsonResponse({'error': _("Check-in date can't be in the past")})

        price = apartment.calculate_price(check_in_date, check_out_date)
        available = apartment.is_available(check_in_date, check_out_date)
        return JsonResponse({'price': price, 'available': available})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def booking_form(request, apartment_id):
    hotel = Hotel.objects.first()
    apartment = get_object_or_404(Apartment, id=apartment_id)

    # Получаем параметры из GET или подставляем значения по умолчанию.
    check_in = request.GET.get('check_in', '')
    check_out = request.GET.get('check_out', '')
    people_quantity = 1

    from datetime import timedelta
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    if not check_in:
        check_in = today.strftime('%Y-%m-%d')
    if not check_out:
        check_out = tomorrow.strftime('%Y-%m-%d')

    # Здесь нет логики POST – мы просто готовим данные для отображения формы.
    context = {
        "apartment": apartment,
        "check_in": check_in,
        "check_out": check_out,
        "people_quantity": people_quantity,
        "error": None,  # Если шаблон учитывает error, передаём None
        "hotel": hotel
    }
    return render(request, "booking_form.html", context)


@login_required
def create_booking(request):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': _("Неверный метод запроса")
        }, content_type='application/json')

    try:
        with transaction.atomic():
            # Данные из клиента
            apartment_id = request.POST.get('apartment_id')
            check_in = request.POST.get('check_in')
            check_out = request.POST.get('check_out')
            people_quantity = int(request.POST.get('people_quantity', 1))
            client_price = Decimal(request.POST.get('total_price', '0.00'))

            # Проверка обязательных данных
            if not all([apartment_id, check_in, check_out]):
                return JsonResponse({
                    'success': False,
                    'error': _("Не все обязательные поля заполнены")
                }, content_type='application/json')

            # Проверяем и преобразуем данные
            apartment = get_object_or_404(Apartment, id=apartment_id)
            check_in_date = timezone.datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = timezone.datetime.strptime(check_out, '%Y-%m-%d').date()

            # Валидация дат
            if check_in_date < timezone.now().date():
                return JsonResponse({
                    'success': False,
                    'error': _("Дата заезда не может быть в прошлом")
                }, content_type='application/json')
            if check_in_date >= check_out_date:
                return JsonResponse({
                    'success': False,
                    'error': _("Дата выезда должна быть позже даты заезда")
                }, content_type='application/json')

            # Проверка доступности апартамента
            if not apartment.is_available(check_in_date, check_out_date):
                return JsonResponse({
                    'success': False,
                    'error': _("Апартамент более недоступен в указанный период, попробуйте выбрать либо другие даты, либо апартамент, либо воспользуйтесь мастером бронирования")
                }, content_type='application/json')

            # Перерасчёт стоимости на сервере
            server_price = apartment.calculate_price(check_in_date, check_out_date)

            # Сравнение цен
            if client_price != server_price:
                return JsonResponse({
                    'success': False,
                    'error': _(
                        "Стоимость изменилась с момента просмотра. Ожидаемая стоимость: %(expected_price)s €") % {
                                 'expected_price': server_price},
                }, content_type='application/json')

            # Сохранение бронирования
            booking = Booking.objects.create(
                user=request.user,
                check_in=check_in_date,
                check_out=check_out_date,
                people_quantity=people_quantity,
                total_value=server_price,
                status='confirmed'
            )
            booking.apartments.add(apartment)
            # Пересчёт total_value и расчёт долга (debt)
            if booking.status == 'confirmed':
                if booking.manual_value is not None:
                    booking.total_value = booking.manual_value
                else:
                    booking.total_value = booking.calculate_total_value()
            else:
                booking.total_value = Decimal('0.00')
            booking.debt = booking.total_value
            booking.save()

            # Переадресация на страницу подтверждения
            from django.urls import reverse
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('booking_confirmation', args=[booking.id])
            }, content_type='application/json')

    except Exception as e:
        # Логирование для отладки
        print(f"Error in create_booking: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': _("Произошла ошибка: %(error)s") % {'error': str(e)}
        }, content_type='application/json')


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


def blog_home(request):
    # Если есть модель блога, замените пустой список на запрос к базе
    hotel = Hotel.objects.first()
    blog_posts = BlogPost.objects.all().order_by('-created_at')
    context = {
        'blog_posts':blog_posts,
        'hotel':hotel
    }
    return render(request, 'blog_home.html', context)


@login_required
def profile(request):
    hotel = Hotel.objects.first()
    user_bookings = Booking.objects.filter(user=request.user, status='confirmed').order_by('check_in')

    # Для каждого бронирования вычисляем строку с номерами апартаментов
    for booking in user_bookings:
        booking.apartments_str = ", ".join(
            [str(apartment.number) for apartment in booking.apartments.all()]
        )

    context = {
        'user_bookings': user_bookings,
        'hotel': hotel,
    }
    return render(request, 'profile.html', context)



def reviews(request):
    hotel = Hotel.objects.first()
    reviews_list = Review.objects.all().order_by('-created_at')  # Получаем список отзывов из базы данных и сортируем от нового к старому
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
        fields = ['rating', 'commentary', 'anonymous']
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

    return render(request, 'create_review.html', {'form': form, 'hotel': hotel, })


from BalkanPearlApp.models import SiteImage


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

    # Вычисляем сегодняшнюю и завтрашнюю даты для установки значений по умолчанию
    today = datetime.datetime.today().date()
    tomorrow = today + timedelta(days=1)

    # Если даты не заданы, устанавливаем значения по умолчанию
    if not check_in:
        check_in = today.strftime('%Y-%m-%d')
    if not check_out:
        check_out = tomorrow.strftime('%Y-%m-%d')

    if not check_in or not check_out or not people_quantity:
        return render(request, 'booking_wizard.html', {'show_form': True, 'hotel': hotel})

    try:
        check_in_date = timezone.datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = timezone.datetime.strptime(check_out, '%Y-%m-%d').date()
        if check_in_date < today:
            return JsonResponse({'error': _("Check-in date can't be in the past")}, status=400)
        elif check_in_date >= check_out_date:
            return JsonResponse({'error': _("Check-out date should be greater than check-in date")}, status=400)
    except ValueError:
        return JsonResponse({'error': _('Некорректный формат даты')}, status=400)

    # Фильтрация открытых и доступных апартаментов
    available_apartments = [
        apt for apt in Apartment.objects.filter(is_closed=False)
        if apt.is_available(check_in_date, check_out_date)
    ]

    if not available_apartments:
        return render(request, 'booking_wizard.html', {
            'show_form': False,
            'hotel': hotel,
            'no_apartments_available': True,
            'check_in': check_in,
            'check_out': check_out,
            'people_quantity': people_quantity,
        })

    apartment_blocks = create_apartment_blocks(available_apartments, people_quantity, check_in_date, check_out_date)
    # если блоков с апартаментами не создать (например, количество гостей не воткнуть в свободные номера, выводим ИСТИНУ или ЛОЖЬ и передаем в шаблон)
    if not apartment_blocks:
        no_apartments_available = True
    else:
        no_apartments_available = False

    # Подгрузка фотографий
    for block in apartment_blocks:
        for apartment in block['apartments']:
            apartment.photos = ApartmentPhoto.objects.filter(apartment=apartment)

    # Отправка данных в шаблон
    context = {
        'apartment_blocks': apartment_blocks,
        'check_in': check_in,
        'check_out': check_out,
        'people_quantity': people_quantity,
        'show_form': False,
        'hotel': hotel,
        'no_apartments_available': no_apartments_available,
    }
    return render(request, 'booking_wizard.html', context)


def create_apartment_blocks(available_apartments, people_quantity, check_in_date, check_out_date):
    """
    Возвращает список вариантов бронирования, отсортированных по стоимости.
    Каждый вариант - комбинация апартаментов, удовлетворяющих требованиям.
    """
    valid_blocks = []

    # Генерация всех возможных комбинаций апартаментов
    for n in range(1, len(available_apartments) + 1):
        for apartment_group in combinations(available_apartments, n):

            # Проверка общей вместимости
            total_capacity = sum(apt.capacity for apt in apartment_group)
            if total_capacity < people_quantity:
                continue  # Пропускаем, если не хватает мест

            # Проверка доступности всех апартаментов
            if not all(apt.is_available(check_in_date, check_out_date) for apt in apartment_group):
                continue

            # Расчет общей стоимости
            total_price = sum(apt.calculate_price(check_in_date, check_out_date) for apt in apartment_group)

            # Сохранение варианта
            valid_blocks.append({
                'apartments': apartment_group,
                'total_price': total_price,
                'total_capacity': total_capacity,
                'num_apartments': n
            })

    # Фильтрация блоков: оставляем минимально возможное количество апартаментов
    if valid_blocks:
        min_apartments = min(block['num_apartments'] for block in valid_blocks)
        valid_blocks = [
            block for block in valid_blocks
            if block['num_apartments'] <= min(min_apartments + 1, people_quantity)
        ]

    # Сортировка по цене, затем по количеству апартаментов
    valid_blocks.sort(key=lambda x: (x['total_price'], x['num_apartments']))

    return valid_blocks


@transaction.atomic
@transaction.atomic
def create_booking_from_block(request):
    # Функция обрабатывает POST-запрос для создания бронирования по выбранному блоку апартаментов
    if request.method == 'POST':
        try:
            # 1. Извлекаем данные из POST-запроса:
            apartment_ids = request.POST.getlist('apartment_ids')
            check_in = request.POST.get('check_in')
            check_out = request.POST.get('check_out')
            people_quantity = int(request.POST.get('people_quantity', 1))
            # Цена, которую видел пользователь (передана через скрытое поле формы)
            displayed_total_price_str = request.POST.get('displayed_total_price', '0.00').strip().replace(',', '.')
            displayed_total_price = Decimal(displayed_total_price_str)
            # Флаг, указывающий, что пользователь подтвердил новую цену, если она изменилась
            confirm_price_change = request.POST.get('confirm_price_change', 'false') == 'true'

            # 2. Блокировка записей апартаментов для обеспечения целостности данных
            apartments = Apartment.objects.select_for_update().filter(
                id__in=apartment_ids,
                is_closed=False
            )

            # 3. Проверка, что все запрошенные апартаменты существуют и доступны (не закрыты)
            if len(apartments) != len(apartment_ids):
                raise ValidationError(_("Некоторые апартаменты не найдены или закрыты"))

            # 4. Проверка доступности каждого апартамента на указанные даты
            for apartment in apartments:
                if not apartment.is_available(check_in, check_out):
                    raise ValidationError(
                        _("Apartment %(apartment)s is already booked for these dates"),
                        params={'apartment': apartment.number}
                    )

            # 5. Создание объекта бронирования (без установки ManyToMany-связей)
            booking = Booking.objects.create(
                user=request.user,
                check_in=check_in,
                check_out=check_out,
                people_quantity=people_quantity,
                status='confirmed'
            )

            # 6. Устанавливаем связь бронирования с выбранными апартаментами
            booking.apartments.set(apartments)

            # 7. Пересчитываем стоимость бронирования с учетом установленных апартаментов
            recalculated_total = booking.calculate_total_value()

            # 8. Сравниваем пересчитанную стоимость с ценой, которую видел пользователь
            if recalculated_total != displayed_total_price and not confirm_price_change:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'price_changed': True,
                        'new_price': str(recalculated_total)
                    })
                else:
                    raise ValidationError(
                        _("We are sorry. Booking price has been changed. Actual booking price: %(price)s"),
                        params={'price': recalculated_total}
                    )

            # 9. Обновляем стоимость бронирования в базе данных
            booking.total_value = recalculated_total
            booking.save(update_fields=['total_value'])
            booking.update_debt_value()

            # 10. Если запрос был отправлен через AJAX, возвращаем JSON с успешным результатом и URL для редиректа,
            # передавая в URL аргумент booking_id
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('booking_confirmation', kwargs={'booking_id': booking.id})
                })

            # 11. При обычном запросе добавляем сообщение об успехе и перенаправляем пользователя на страницу подтверждения
            messages.success(request, _("Апартаменты успешно забронированы!"))
            return redirect('booking_confirmation', booking_id=booking.id)

        except ValidationError as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=400)
            messages.error(request, str(e))
            return redirect('booking_wizard')

        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': f"Ошибка бронирования: {str(e)}"}, status=400)
            messages.error(request, f"Ошибка бронирования: {str(e)}")
            return redirect('booking_wizard')

    return redirect('booking_confirmation')
