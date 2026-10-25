from django import forms

from .models import RobloxUser


class RobloxUserRegistrationForm(forms.ModelForm):
    telegram_username = forms.CharField(
        label="Telegram username",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "@telegram_username"}),
    )

    class Meta:
        model = RobloxUser
        fields = ("Roblox_username", "telegram_username")
        labels = {
            "Roblox_username": "Roblox username",
        }
        widgets = {
            "Roblox_username": forms.TextInput(
                attrs={"placeholder": "Roblox username"}
            ),
        }


class MatsuPasswordForm(forms.Form):
    password = forms.CharField(
        label="Admin akkaunti paroli",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password"},
            render_value=False,
        ),
    )
