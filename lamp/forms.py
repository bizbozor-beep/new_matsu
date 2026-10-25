from django import forms

from .models import RobloxUser


class RobloxUserRegistrationForm(forms.ModelForm):
    class Meta:
        model = RobloxUser
        fields = ("Roblox_username", "roblox_email", "phone_number")
        labels = {
            "Roblox_username": "Roblox username",
            "roblox_email": "Email manzilingiz",
            "phone_number": "Telefon raqamingiz",
        }
        widgets = {
            "Roblox_username": forms.TextInput(
                attrs={"placeholder": "Roblox username"}
            ),
            "roblox_email": forms.EmailInput(
                attrs={"placeholder": "name@example.com"}
            ),
            "phone_number": forms.TelInput(attrs={"placeholder": "+998 90 123 45 67"}),
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
