from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super(CustomAccountAdapter, self).save_user(request, user, form, commit)
        # Дополнительные действия с пользователем
        return user
