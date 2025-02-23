# C:\Mail.ru\CodeIt\Django\BalkanPearl\BalkanPearlProject\BalkanPearlApp\forms.py
# -*- coding: utf-8 -*-
from allauth.account.forms import LoginForm
from django.utils.translation import gettext_lazy as _

class CustomLoginForm(LoginForm):
    """Custom authentication form"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Email или имя пользователя')})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Пароль')})
