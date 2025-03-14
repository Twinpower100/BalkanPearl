# C:\Mail.ru\CodeIt\Django\BalkanPearl\BalkanPearlProject\BalkanPearlApp\models.py
# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Q
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Address(models.Model):
    street = models.CharField(max_length=255, verbose_name=_("Street"))
    city = models.CharField(max_length=100, verbose_name=_("City"))
    state = models.CharField(max_length=100, verbose_name=_("State/Province"))
    postal_code = models.CharField(max_length=20, verbose_name=_("Postal Code"))
    country = models.CharField(max_length=100, verbose_name=_("Country"))

    class Meta:
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state}, {self.country} ({self.postal_code})"


class WindowView(models.Model):
    view = models.CharField(max_length=255, verbose_name=_('Window view'))

    def __str__(self):
        return f'View {self.view}'


class ApartmentType(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Apartment type'), )

    def __str__(self):
        return f'Type {self.name}'


class Hotel(models.Model):
    """Описываем отель"""
    name = models.CharField(max_length=255, verbose_name=_('Hotel'), default='Balkan Pearl')
    description = models.TextField(verbose_name=_('Hotel description'))
    floors = models.IntegerField(verbose_name=_('Floors quantity'))
    address = models.OneToOneField(Address, on_delete=models.CASCADE, verbose_name=_('Address'))
    contact_email = models.EmailField(verbose_name=_('Our E-Mail'))
    contact_phone = PhoneNumberField(verbose_name=_('Our phone (WatsApp, Telegram, Viber)'))
    instagram_link = models.URLField(verbose_name=_('Instagram link'), blank=True, null=True)
    facebook_link = models.URLField(verbose_name=_('Facebook link'), blank=True, null=True)


    class Meta:
        verbose_name = _('Hotel')
        verbose_name_plural = _('Hotels')

    def __str__(self):
        return self.name

    def get_google_maps_url(self):
        """Сформировать ссылку на Google Maps"""
        return f"https://www.google.com/maps/search/?api=1&query={self.address}"


class Season(models.Model):
    """Сезон с уникальными датами и коэффициентом цен"""
    name = models.CharField(max_length=50, verbose_name=_("Season's name"),
                            help_text=_(
                                "Задним числом стоимость не пересчитывается. Начало и конец действия при расчете"
                                " цены считается по дате заезда"))
    start_date = models.DateField(verbose_name=_("Start date"), help_text=_("По дате заезда"))
    end_date = models.DateField(verbose_name=_("End date"), help_text=_("По дате заезда"))
    price_multiplier = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.0, verbose_name=_("Price coefficient"))

    def clean(self):
        """Валидатор дат"""
        if self.start_date >= self.end_date:
            raise ValidationError(_("Start date must be earlier than end date"))
        # Проверяем, есть ли пересечение с другим сезоном (НЕ учитывая название)
        overlapping_seasons = Season.objects.filter(
            start_date__lt=self.end_date,  # Начало текущего сезона < конец другого
            end_date__gt=self.start_date  # Конец текущего сезона > начало другого
        ).exclude(id=self.id)  # Исключает сам себя при обновлении

        if overlapping_seasons.exists():
            raise ValidationError(_("Season dates cannot overlap with another season."))

    def save(self, *args, **kwargs):
        """ Вызов валидации перед сохранением """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

    class Meta:
        verbose_name = _('Season')
        verbose_name_plural = _('Seasons')


class Apartment(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='apartments', verbose_name=_('Hotel'))
    number = models.IntegerField(unique=True, verbose_name=_('Apartment number'))
    description = models.TextField(verbose_name=_('Description'))
    window_view = models.ForeignKey(WindowView, on_delete=models.CASCADE)
    floor = models.IntegerField(verbose_name=_('Floor'))

    def clean(self):
        """Проверка этажа - не может быть больше количества этажей в отеле"""
        super().clean()
        if self.hotel and self.floor > self.hotel.floors:
            raise ValidationError({
                'floor': _("The floor number you've entered is bigger than the Hotel's floors quantity")
            })

    type = models.ForeignKey(ApartmentType, on_delete=models.CASCADE, related_name='apartments',
                             verbose_name=_('Apartment type'))
    BALCONY_CHOICES = (
        ('B', 'Balcony'),
        ('T', 'Terrace'),
        ('N', 'No balcony or terrace')
    )
    balcony = models.CharField(max_length=1, verbose_name=_('Balcony type'), choices=BALCONY_CHOICES)
    rooms_quantity = models.IntegerField(verbose_name=_('Rooms quantity'))
    mini_kitchen = models.BooleanField(verbose_name=_('Mini kitchen in apartment'), default=True)
    bathrooms_quantity = models.IntegerField(verbose_name=_('Bathrooms quantity'), default=1)
    beds_quantity = models.IntegerField(verbose_name=_('Beds quantity'))

    class Meta:
        verbose_name = _('Apartment')
        verbose_name_plural = _('Apartments')
        constraints = [
            models.UniqueConstraint(
                fields=['hotel', 'number'],
                name='unique_apartment_number_per_hotel'
            )
        ]

    sofa = models.BooleanField(verbose_name=_('Sofa'))
    washing_machine = models.BooleanField(verbose_name=_('Washing machine'), default=True)
    desk = models.BooleanField(verbose_name=_('desk'))
    iron_and_board = models.BooleanField(verbose_name=_("Iron and ironing board"))
    child_bed = models.BooleanField(verbose_name=_('Child bed'))
    microwave = models.BooleanField(verbose_name=_('Microwave'))
    square = models.IntegerField(verbose_name=_('Square'))
    capacity = models.IntegerField(verbose_name=_('Max capacity, people'))
    base_price_per_night = models.DecimalField(
        verbose_name="Base price per night", max_digits=10, decimal_places=2
    )
    is_closed = models.BooleanField(default=False, verbose_name=_('Apartment is closed'))

    def calculate_price(self, check_in, check_out):
        if isinstance(check_in, str):
            check_in = timezone.datetime.strptime(check_in, "%Y-%m-%d").date()
        if isinstance(check_out, str):
            check_out = timezone.datetime.strptime(check_out, "%Y-%m-%d").date()



        today = timezone.now().date()
        if check_in < today:
            raise ValidationError(_("Дата заезда не может быть в прошлом"))
        if check_in >= check_out:
            raise ValidationError(_("Дата выезда должна быть позже даты заезда"))

        total_price = Decimal("0.00")
        current_date = check_in

        while current_date < check_out:
            # season = Season.objects.filter(
            #     start_date__lte=current_date,
            #     end_date__gte=current_date
            # ).first()
            season = Season.objects.filter(
                start_date__lte=current_date,
                end_date__gt=current_date
            ).first()

            if season:
                price_for_day = self.base_price_per_night * season.price_multiplier
                # Граница сезона – если бронирование пересекается, то до check_out:
                #end_of_season = min(season.end_date + timezone.timedelta(days=1), check_out)
                end_of_season = min(season.end_date, check_out) # Не прибавляем 1 день
                days_in_season = (end_of_season - current_date).days
                total_price += days_in_season * price_for_day
                current_date = end_of_season
            else:
                next_season = Season.objects.filter(start_date__gt=current_date).order_by('start_date').first()
                if next_season:
                    end_of_period = min(next_season.start_date, check_out)
                else:
                    end_of_period = check_out
                days_in_period = (end_of_period - current_date).days
                total_price += days_in_period * self.base_price_per_night
                current_date = end_of_period

        return total_price.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

    def is_available(self, check_in, check_out):
        overlapping_bookings = self.bookings.filter(
            models.Q(check_in__lt=check_out) &
            models.Q(check_out__gt=check_in) &
            ~models.Q(status__in=['cancelled_by_user', 'cancelled_by_admin'])
        )
        return not overlapping_bookings.exists()

    def __str__(self):
        return f"{self.number} {self.hotel.name} {self.type} {self.floor} {self.base_price_per_night}"


class Booking(models.Model):
    STATUS_CHOICES = [('confirmed', _('Confirmed')), ('cancelled_by_user', _('Cancelled by User')),
                      ('cancelled_by_admin', _('Cancelled by Admin')),
                      ]
    apartments = models.ManyToManyField(Apartment, related_name='bookings', verbose_name=_('Apartments set'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings", verbose_name=_("User"))
    check_in = models.DateField(verbose_name=_('Check in date'))
    check_out = models.DateField(verbose_name=_('Check out date'))
    total_value = models.DecimalField(verbose_name=_('Total booking value'), max_digits=10, decimal_places=2,
                                      default=0.00, validators=[MinValueValidator(Decimal('0.00'))])
    manual_value = models.DecimalField(verbose_name=_('Manual value'), max_digits=10, decimal_places=2, blank=True,
                                       null=True, help_text=_("Admin is able to change total booking value"),
                                       validators=[MinValueValidator(Decimal('0.00'))])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed', verbose_name=_("Status"))
    debt = models.DecimalField(verbose_name=_('Debt'), help_text=_("Negative debt means hotel's debt"), max_digits=10,
                               decimal_places=2, default=Decimal(0.00))
    people_quantity = models.IntegerField(verbose_name=_('Guests quantity'), default=1, blank=True)

    class Meta:
        verbose_name = _('Booking')
        verbose_name_plural = _('Bookings')
        indexes = [
            models.Index(fields=['check_in', 'check_out'])
        ]

    def clean(self):
        """Валидация дат"""
        super().clean()
        if self.check_in >= self.check_out:
            raise ValidationError(_("Дата выезда должна быть позже даты заезда"))
        if self.check_in < timezone.now().date():
            raise ValidationError(_("Дата заезда не может быть в прошлом"))

        if self.pk:
            apartments = list(self.apartments.all())
            total_capacity = sum(a.capacity for a in apartments)
            if total_capacity < self.people_quantity:
                raise ValidationError(_('Total apartments capacity is insufficient'))

            if not apartments:
                raise ValidationError(_("At least one apartment must be selected"))

            if self.status == 'confirmed':
                for apartment in apartments:
                    overlapping = Booking.objects.filter(
                        apartments=apartment,
                        check_in__lt=self.check_out,
                        check_out__gt=self.check_in,
                        status='confirmed'
                    ).exclude(pk=self.pk)

                    if overlapping.exists():
                        raise ValidationError(
                            _("Apartment %(apartment)s is already booked for these dates"),
                            params={'apartment': apartment.number}
                        )

            overlapping_group = Booking.objects.filter(
                apartments__in=apartments,
                check_in__lt=self.check_out,
                check_out__gt=self.check_in,
                status='confirmed'
                ).exclude(pk=self.pk).distinct()
            if overlapping_group.exists():
                raise ValidationError(_("Один или несколько апартаментов уже заняты в выбранные даты"))

    def calculate_total_value(self):
        if not self.pk:
            return Decimal('0.00')
        apartments = self.apartments.all()
        total = Decimal('0.00')
        for apartment in apartments:
            price = apartment.calculate_price(self.check_in, self.check_out)
            total += price
        return total

    def save(self, *args, **kwargs):
        # Убираю автоматический пересчет total_value и debt, чтобы пересчет производился в представлении
        super().save(*args, **kwargs)

    def get_total_payments(self):
        return self.payments.aggregate(Sum('payment_value'))['payment_value__sum'] or Decimal(0.00)

    def get_total_refunds(self):
        return self.refunds.aggregate(Sum('refund_value'))['refund_value__sum'] or Decimal(0.00)

    def update_debt_value(self):
        self.debt = self.total_value - self.get_total_payments() + self.get_total_refunds()
        super().save(update_fields=['debt'])

    def cancel_booking(self, cancelled_by, reason=None):
        if self.status != 'confirmed':
            raise ValueError(_("Cannot cancel a booking that is not confirmed."))

        total_payments = self.get_total_payments()
        total_refunds = self.get_total_refunds()
        net_payments = total_payments - total_refunds

        # При отмене обнуляем стоимость
        self.total_value = Decimal(0.00)
        self.debt = -net_payments


        if cancelled_by == 'user':
            self.status = 'cancelled_by_user'
        elif cancelled_by == 'admin':
            self.status = 'cancelled_by_admin'
        else:
            raise ValueError(_("Invalid cancellation initiator. Must be 'user' or 'admin'."))

        super().save(update_fields=['status', 'total_value', 'debt'])


    def __str__(self):
        if not self.pk:
            return f"Booking (unsaved) by {self.user}"
        return _("Booking {id} by user {user} has a debt {debt}").format(
            id=self.id,
            user=self.user.username,
            debt=self.debt
        )


class Payment(models.Model):
    PAYMENT_CHOICES = [
        ('card', _('Card payment')),
        ('cash', _('Paid by cash')),
        ('online', _('Online')),
        ('other', _('Other')),
    ]
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments', verbose_name=_('Booking'))
    payment_method = models.CharField(verbose_name=_("Payment method"), max_length=25, choices=PAYMENT_CHOICES,
                                      blank=True, editable=True, )
    payment_value = models.DecimalField(verbose_name=_('Payment value'), max_digits=10, decimal_places=2,
                                        validators=[MinValueValidator(Decimal('0.01'))])
    payment_date = models.DateTimeField(auto_now_add=True)
    note = models.TextField(verbose_name=_('Note'), blank=True, )

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Блокируем запись бронирования
            booking = Booking.objects.select_for_update().get(pk=self.booking.pk)
            if self.payment_value > booking.debt:
                raise ValidationError(_("Payment exceeds debt."))
            super().save(*args, **kwargs)
            booking.update_debt_value()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            # Блокируем запись бронирования
            booking = Booking.objects.select_for_update().get(pk=self.booking.pk)
            super().delete(*args, **kwargs)
            # Обновляем задолженность после удаления оплаты
            booking.update_debt_value()

    def __str__(self):
        # return \
        #     f"{self.id} - {self.payment_date.strftime('%Y-%m-%d')} - {self.payment_value} - {self.payment_method}"
        return _("Payment {id} for {value} made {date} in {method} ").format(
            id=self.id,
            value=self.payment_value,
            date=self.payment_date,
            method=self.payment_method,
        )


class Refund(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='refunds', verbose_name=_('Booking'))
    refund_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00), )
    refund_date = models.DateField(verbose_name=_('Refund date'), auto_now_add=True)
    note = models.TextField(verbose_name=_('Note'), blank=True, )

    class Meta:
        verbose_name = _('Refund')
        verbose_name_plural = _('Refunds')

    def save(self, *args, **kwargs):
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(pk=self.booking.pk)
            if booking.debt >= 0:
                raise ValidationError(_("The hotel doesn't have any debt"))
            elif self.refund_value > - booking.debt:
                raise ValidationError(_("Refund exceeds debt!"))
            else:
                super().save(*args, **kwargs)
                booking.update_debt_value()

    def __str__(self):
        return _("Refund {id} for {value} made {date} ").format(
            id=self.id,
            value=self.refund_value,
            date=self.refund_date
        )


class Review(models.Model):
    """Отзывы пользователей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('Username'))
    apartment = models.ForeignKey(Apartment, on_delete=models.SET_NULL, null=True, verbose_name=_('Apartment'),
                                  blank=True, )
    rating = models.IntegerField(verbose_name=_('Rating'), choices=[(i, i) for i in range(1, 6)])
    commentary = models.TextField(verbose_name=_("Commentary"))
    created_at = models.DateTimeField(auto_now_add=True)
    anonymous = models.BooleanField(default=False, verbose_name=_('Is anonymous'))

    class Meta:
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')

    def clean(self):
        if not (1 <= self.rating <= 5):
            raise ValidationError(_("Rating must be between 1 and 5"))

    def __str__(self):
        return _("Отзыв {user} - {rating} - {commentary}").format(
            user=self.user.username,
            rating=self.rating,
            commentary=self.commentary,
        )


class BlogPost(models.Model):
    """Блог или форум"""
    title = models.CharField(max_length=200, verbose_name=_("Header"))
    content = models.TextField(verbose_name=_('Content'))
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Author"), )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Blog post')
        verbose_name_plural = _('Blog posts')

    def __str__(self):
        return f"{self.title}"


class SiteImage(models.Model):
    image = models.ImageField(upload_to='site_images/')
    description = models.CharField(max_length=255, blank=True, verbose_name=_('Description'))

    def __str__(self):
        # Используем gettext для перевода
        return self.description or _('No description')


class ApartmentPhoto(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='apartment_photos',
                                  verbose_name=_('Apartment'))
    photo = models.ImageField(upload_to='apartment/photos/', verbose_name=_('Apartment photo'))
    description = models.CharField(max_length=255, blank=True, verbose_name=_('Description'))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Upload date'))

    class Meta:
        verbose_name = _('Apartment photo')
        verbose_name_plural = _('Apartment photos')

    def __str__(self):
        return f'Photo {self.apartment.number} {self.photo}'


class HotelPhoto(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='hotel_photos', verbose_name=_('Hotel'))
    photo = models.ImageField(upload_to='hotel/photos/', verbose_name=_('Hotel photo'))
    description = models.CharField(max_length=255, blank=True, verbose_name=_('Description'))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Upload date'))

    class Meta:
        verbose_name = _('Hotel photo')
        verbose_name_plural = _('Hotel photos')

    def __str__(self):
        return f'Photo {self.hotel} {self.photo}'
