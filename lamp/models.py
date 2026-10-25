from django.db import models
from django.conf import settings


class RobloxUser(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tournament_registrations",
    )
    Roblox_username = models.CharField(max_length=100)
    roblox_email = models.EmailField()
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return self.Roblox_username
