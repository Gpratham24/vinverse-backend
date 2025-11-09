"""
Admin configuration for CustomUser model.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Badge, UserBadge


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin interface for CustomUser with esports fields."""
    list_display = ('username', 'email', 'vin_id', 'gamer_tag', 'rank', 'xp_points', 'streak_days', 'is_online', 'verified', 'is_staff')
    list_filter = ('verified', 'is_online', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'vin_id', 'gamer_tag')
    fieldsets = UserAdmin.fieldsets + (
        ('VinVerse Profile', {'fields': ('vin_id', 'verified', 'xp_points', 'streak_days', 'last_active_date')}),
        ('Esports Profile', {'fields': ('bio', 'rank', 'gamer_tag')}),
        ('Online Status', {'fields': ('is_online', 'last_seen')}),
    )
    readonly_fields = ('vin_id', 'last_seen')  # VIN ID is auto-generated, read-only


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    """Admin interface for Badge model."""
    list_display = ('icon', 'name', 'key', 'badge_type', 'color', 'created_at')
    list_filter = ('badge_type', 'color', 'created_at')
    search_fields = ('name', 'key', 'description')
    readonly_fields = ('created_at',)


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    """Admin interface for UserBadge model."""
    list_display = ('user', 'badge', 'earned_at')
    list_filter = ('earned_at', 'badge__badge_type')
    search_fields = ('user__username', 'badge__name', 'badge__key')
    readonly_fields = ('earned_at',)

