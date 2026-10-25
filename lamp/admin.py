from django.contrib import admin

from .models import RobloxUser


@admin.register(RobloxUser)
class RobloxUserAdmin(admin.ModelAdmin):
    list_display = ("Roblox_username", "telegram_username", "registered_at", "user")
    search_fields = ("Roblox_username", "telegram_username", "user__username")
