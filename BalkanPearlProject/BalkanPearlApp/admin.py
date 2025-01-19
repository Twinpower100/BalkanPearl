from django.contrib import admin
from BalkanPearlApp.models import Hotel, Address, HotelPhoto, WindowView, ApartmentType, Apartment, Season, \
    ApartmentPhoto, Booking, BookingLog, Review, BlogPost, SiteImage
from django import forms
from decimal import Decimal


# Register your models here.

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('street', 'city', 'state', 'postal_code', 'country')

class HotelAdminForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = '__all__'

    # def clean_latitude(self):
    #     latitude = self.cleaned_data.get('latitude')
    #     if isinstance(latitude, str):
    #         latitude = latitude.replace(',', '.')
    #     return Decimal(latitude)
    #
    # def clean_longitude(self):
    #     longitude = self.cleaned_data.get('longitude')
    #     if isinstance(longitude, str):
    #         longitude = longitude.replace(',', '.')
    #     return Decimal(longitude)

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    form = HotelAdminForm  # Используем пользовательскую форму
    list_display = ('name', 'description', 'floors', 'address', 'contact_email',
                    'contact_phone', )
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
    list_display = ('apartment', 'photo', 'description', 'uploaded_at')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'apartment', 'user', 'check_in', 'check_out', 'status', 'is_paid')
    list_filter = ('status', 'is_paid')
    search_fields = ('apartment__number', 'user__username', 'status')


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
