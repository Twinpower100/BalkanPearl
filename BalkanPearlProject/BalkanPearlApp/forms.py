# C:\Mail.ru\CodeIt\Django\BalkanPearl\BalkanPearlProject\BalkanPearlApp\forms.py
# -*- coding: utf-8 -*-
from allauth.account.forms import LoginForm
from django.utils.translation import gettext_lazy as _
from django import forms
from django.core.exceptions import ValidationError
from .models import Booking, Apartment, Hotel
import datetime


class CustomLoginForm(LoginForm):
    """Custom authentication form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': _('Email или имя пользователя')})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Пароль')})


def is_apartment_available(apartment, check_in, check_out):
    """Проверяет, доступен ли апартамент в указанный период, без частичных пересечений бронирований."""
    # Поиск подтвержденных бронирований для апартамента, пересекающихся с заданным диапазоном
    overlapping_bookings = Booking.objects.filter(
        apartments=apartment,
        status='confirmed',
        check_in__lt=check_out,
        check_out__gt=check_in,
    )
    return not overlapping_bookings.exists()


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        apartments = cleaned_data.get('apartments')

        if check_in and check_out and apartments:
            if check_out <= check_in:
                raise ValidationError(_('Дата выезда должна быть позже даты заезда.'))
            for apartment in apartments:
                if not is_apartment_available(apartment, check_in, check_out):
                    raise ValidationError(_(f'Апартамент {apartment} недоступен в указанный период.'))
        return cleaned_data


class AvailabilityReportFilterForm(forms.Form):
    start_date = forms.DateField(
        label=_('Дата с'),
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=datetime.date.today().replace(day=1)
    )
    end_date = forms.DateField(
        label=_('Дата по'),
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=datetime.date.today()
    )
    hotel = forms.ModelChoiceField(
        queryset=Hotel.objects.all(),
        required=False,
        label=_('Отель')
    )
    apartments = forms.ModelMultipleChoiceField(
        queryset=Apartment.objects.all(),
        required=False,
        label=_('Апартаменты')
    )
