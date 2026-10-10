from django.contrib.auth.forms import UserCreationForm

from users.models import User, UserRole


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "phone", "address")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = UserRole.CLIENT
        if commit:
            user.save()
        return user
