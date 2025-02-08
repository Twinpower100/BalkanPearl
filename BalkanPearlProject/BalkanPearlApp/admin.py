from django.contrib import admin

from BalkanPearlApp.models import Hotel, Address, HotelPhoto, WindowView, ApartmentType, Apartment, Season, \
    ApartmentPhoto, Booking, BookingLog, Review, BlogPost, SiteImage, Payment
from django import forms
from django.utils.translation import gettext_lazy as _


# Register your models here.

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('street', 'city', 'state', 'postal_code', 'country')


class HotelAdminForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = '__all__'


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    form = HotelAdminForm  # Используем пользовательскую форму
    list_display = ('name', 'description', 'floors', 'address', 'contact_email',
                    'contact_phone', 'instagram_link', 'facebook_link',)
    list_filter = ('name',)


@admin.register(HotelPhoto)
class HotelPhotoAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'photo', 'description', 'uploaded_at')


@admin.register(WindowView)
class WindowViewAdmin(admin.ModelAdmin):
    list_display = ('view',)


@admin.register(ApartmentType)
class ApartmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'number', 'description', 'window_view', 'floor', 'type', 'balcony', 'rooms_quantity',
                    'mini_kitchen', 'bathrooms_quantity', 'beds_quantity', 'sofa', 'washing_machine', 'desk',
                    'iron_and_board', 'child_bed', 'microwave', 'square', 'capacity', 'base_price_per_night',
                    'is_closed')
    list_filter = ('hotel', 'number', 'window_view', 'floor', 'type', 'balcony', 'rooms_quantity',
                   'base_price_per_night', 'is_closed')
    ordering = ('hotel', 'number')


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'price_multiplier')


@admin.register(ApartmentPhoto)
class ApartmentPhotoAdmin(admin.ModelAdmin):
    list_display = ('apartment__number', 'photo', 'description', 'uploaded_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'payment_value', 'payment_method', 'payment_date', 'note']
    list_filter = ['payment_method', 'payment_date']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    #form = BookingAdminForm
    list_display = ('id', 'apartment__number', 'user', 'check_in', 'check_out', 'status', 'total_value', 'debt_display',
                    'created_at')
    list_filter = ('status', 'apartment', 'user')
    search_fields = ('apartment__number', 'user__username', 'status')
    readonly_fields = ('created_at', 'debt_display', 'total_value')
    actions = ['cancel_booking']

    def cancel_booking(self, request, queryset):
        """Эта функция — кастомное действие (admin action) в Django Admin.
        Она позволяет администратору отменять выбранные бронирования через панель
        управления."""

        """self — текущий экземпляр класса BookingAdmin (наследник admin.ModelAdmin).
            request — объект запроса HTTP (от Django Admin).
            queryset — набор объектов Booking, выбранных администратором."""
        cancelled = queryset.exclude(status='cancelled')

        for booking in cancelled:
            booking.cancel_booking(cancelled_by='admin')
        self.message_user(request, _("Выбранные бронирования отменены."))

    cancel_booking.short_description = _("Отменить выбранные бронирования")

    @admin.display(description=_('Задолженность'))
    def debt_display(self, obj):
        return obj.debt


@admin.register(BookingLog)
class BookingLogAdmin(admin.ModelAdmin):
    list_display = ('booking', 'action', 'performed_by', 'timestamp')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'apartment', 'rating', 'commentary', 'created_at', 'is_approved')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'content', 'author', 'created_at', 'updated_at')


@admin.register(SiteImage)
class SiteImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'description')
