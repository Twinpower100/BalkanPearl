# -*- coding: utf-8 -*-
from allauth.account.forms import LoginForm

class CustomLoginForm(LoginForm):
    """Custom authentication form"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email или имя пользователя'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})
