"""
Admin configuration for CustomUser model.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin interface for CustomUser with esports fields."""
    list_display = ('username', 'email', 'vin_id', 'gamer_tag', 'rank', 'xp_points', 'is_online', 'verified', 'is_staff')
    list_filter = ('verified', 'is_online', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'vin_id', 'gamer_tag')
    fieldsets = UserAdmin.fieldsets + (
        ('VinVerse Profile', {'fields': ('vin_id', 'verified', 'xp_points')}),
        ('Esports Profile', {'fields': ('bio', 'rank', 'gamer_tag')}),
        ('Online Status', {'fields': ('is_online', 'last_seen')}),
    )
    readonly_fields = ('vin_id', 'last_seen')  # VIN ID is auto-generated, read-only

