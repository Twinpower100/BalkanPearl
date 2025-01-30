from django.core.exceptions import ValidationError
from django.db import models
from decimal import Decimal
from django.db.models import CASCADE
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


# Create your models here.

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
    # latitude = models.DecimalField(max_digits=17, decimal_places=15, verbose_name=_('Latitude'), default=0)
    # longitude = models.DecimalField(max_digits=17, decimal_places=15, verbose_name=_('Longitude'), default=0)

    # def save(self, *args, **kwargs):
    #     if isinstance(self.latitude, str):
    #         self.latitude = Decimal(self.latitude.replace(',', '.'))
    #     if isinstance(self.longitude, str):
    #         self.longitude = Decimal(self.longitude.replace(',', '.'))
    #
    #     super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Hotel')
        verbose_name_plural = _('Hotels')

    def __str__(self):
        return self.name

    def get_google_maps_url(self):
        """Сформировать ссылку на Google Maps"""
        return f"https://www.google.com/maps/search/?api=1&query={self.address}"


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


class WindowView(models.Model):
    view = models.CharField(max_length=255, verbose_name=_('Window view'))

    def __str__(self):
        return f'View {self.view}'


class ApartmentType(models.Model):
    name = models.CharField(verbose_name=_('Apartment type'))

    def __str__(self):
        return f'Type {self.name}'


class Apartment(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='apartment', verbose_name=_('Hotel'))
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

    type = models.ForeignKey(ApartmentType, on_delete=models.CASCADE, related_name='apartment',
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
        """Рассчитать цену на основе сезона"""
        nights = (check_out - check_in).days
        if nights <= 0:
            raise ValueError("Дата выезда должна быть позже даты заезда.")

        seasons = Season.objects.filter(start_date__lte=check_out, end_date__gte=check_in)
        total_price = 0
        for season in seasons:
            overlapping_days = min(season.end_date, check_out) - max(season.start_date, check_in)
            if overlapping_days.days > 0:
                total_price += overlapping_days.days * self.base_price_per_night * season.price_multiplier
        return total_price

    def is_available(self, check_in, check_out):
        overlapping_bookings = self.booking.filter(
            models.Q(check_in__lt=check_out) &
            models.Q(check_out__gt=check_in) &
            ~models.Q(status__in=['cancelled_by_user', 'cancelled_by_admin'])
        )
        return not overlapping_bookings.exists()

    def __str__(self):
        return f"{self.number} {self.hotel.name} {self.type} {self.floor} {self.base_price_per_night}"


class Season(models.Model):
    """Сезон с уникальными датами и коэффициентом цен"""
    name = models.CharField(max_length=50, verbose_name=_("Season's name"))
    start_date = models.DateField(verbose_name=_("Start date"))
    end_date = models.DateField(verbose_name=_("End date"))
    price_multiplier = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.0, verbose_name=_("Price coefficient"))

    def clean(self):
        """Валидатор дат"""
        if self.start_date >= self.end_date:
            raise ValidationError(_("Start date must be earlier than end date"))

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

    class Meta:
        verbose_name = _('Season')
        verbose_name_plural = _('Seasons')


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
        return f'Photo {self.apartment} {self.photo}'


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', _('Confirmed')),
        ('cancelled_by_user', _('Cancelled by User')),
        ('cancelled_by_admin', _('Cancelled by Admin')),
    ]

    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name="booking",
                                  verbose_name=_("Apartment number"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="booking", verbose_name=_("User"))
    check_in = models.DateField(verbose_name=_('Check in date'))
    check_out = models.DateField(verbose_name=_('Check out date'))
    is_paid = models.BooleanField(default=False, verbose_name=_("Paid"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed', verbose_name=_("Status"))
    cancellation_reason = models.TextField(blank=True, null=True, verbose_name=_("Cancellation reason"))

    def __str__(self):
        return f"Booking {self.id} by {self.user.username} - {self.apartment.number}"

    class Meta:
        verbose_name = _('Booking')
        verbose_name_plural = _('Bookings')
        unique_together = ('apartment', 'check_in', 'check_out')

    def cancel_booking(self, cancelled_by, reason=None):
        """
        Отмена бронирования.

        :param cancelled_by: 'user' или 'admin'
        :param reason: Причина отмены (опционально)
        """
        if self.status != 'confirmed':
            raise ValueError(_("Cannot cancel a booking that is not confirmed."))

        if cancelled_by == 'user':
            self.status = 'cancelled_by_user'
        elif cancelled_by == 'admin':
            self.status = 'cancelled_by_admin'
        else:
            raise ValueError(_("Invalid cancellation initiator. Must be 'user' or 'admin'."))

        self.cancellation_reason = reason
        self.save()


class BookingLog(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, verbose_name=_("Booking"))
    action = models.CharField(max_length=50, verbose_name=_("Action"))
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Performed by"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Timestamp"))


class Review(models.Model):
    """Отзывы пользователей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('Username'))
    apartment = models.ForeignKey(Apartment, on_delete=models.SET_NULL, null=True, verbose_name=_('Apartment'),
                                  blank=True)
    rating = models.IntegerField(verbose_name=_('Rating'), choices=[(i, i) for i in range(1, 6)])
    commentary = models.TextField(verbose_name=_("Commentary"))
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False, verbose_name=_('Approved'))

    class Meta:
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')

    def clean(self):
        if not (1 <= self.rating <= 5):
            raise ValidationError(_("Rating must be between 1 and 5"))

    def __str__(self):
        return f"Отзыв {self.user.username} - {self.rating} - {self.commentary}"


class BlogPost(models.Model):
    """Блог или форум"""
    title = models.CharField(max_length=200, verbose_name=_("Header"))
    content = models.TextField(verbose_name=_('Content'))
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Author"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Blog post')
        verbose_name_plural = _('Blog posts')

    def __str__(self):
        return self.title


class SiteImage(models.Model):
    image = models.ImageField(upload_to='site_images/')
    description = models.CharField(max_length=255, blank=True, verbose_name=_('Description'))

    def __str__(self):
        # Используем gettext для перевода
        return self.description or _('No description')
