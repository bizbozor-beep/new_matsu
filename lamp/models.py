from django.db import models
from django.conf import settings
from django.utils import timezone


class RobloxUser(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tournament_registrations",
    )
    Roblox_username = models.CharField(max_length=100)
    telegram_username = models.CharField(max_length=100, blank=True, default="")
    registered_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return self.Roblox_username
