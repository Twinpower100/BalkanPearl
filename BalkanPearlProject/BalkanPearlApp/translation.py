# C:\Mail.ru\CodeIt\Django\BalkanPearl\BalkanPearlProject\BalkanPearlApp\translation.py
from modeltranslation.translator import register, TranslationOptions
from .admin import *
from .models import Hotel, Apartment, HotelPhoto, WindowView, ApartmentType, Season, ApartmentPhoto, Booking, \
    Review, BlogPost, Address
from .models import *


@register(Address)
class AddressTranslationOptions(TranslationOptions):
    fields = ('street', 'city', 'state', 'country')


@register(Hotel)
class HotelTranslationOptions(TranslationOptions):
    fields = ('description',)


@register(HotelPhoto)
class HotelPhotoTranslationOptions(TranslationOptions):
    fields = ('description',)


@register(WindowView)
class WindowViewTranslationOptions(TranslationOptions):
    fields = ('view',)


@register(ApartmentType)
class ApartmentTypeTranslationOptions(TranslationOptions):
    fields = ('name',)  # Убедитесь, что поле называется "name", а не "type".


@register(Apartment)
class ApartmentTranslationOptions(TranslationOptions):
    fields = ('description',)  # Убрали "balcony", если это BooleanField.


@register(Season)
class SeasonTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(ApartmentPhoto)
class ApartmentPhotoTranslationOptions(TranslationOptions):
    fields = ('description',)  # Убрали "apartment", так как это ForeignKey.



@register(Review)
class ReviewTranslationOptions(TranslationOptions):
    fields = ('commentary',)


@register(BlogPost)
class BlogPostTranslationOptions(TranslationOptions):
    fields = ('title', 'content',)


@register(SiteImage)
class SiteImageTranslationOptions(TranslationOptions):
    fields = ('description',)