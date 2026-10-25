from django.contrib import admin

from .models import RobloxUser


@admin.register(RobloxUser)
class RobloxUserAdmin(admin.ModelAdmin):
    list_display = ("Roblox_username", "roblox_email", "phone_number", "user")
    search_fields = ("Roblox_username", "roblox_email", "phone_number", "user__username")
