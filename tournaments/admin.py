"""
Admin configuration for Tournament models.
"""
from django.contrib import admin
from .models import Tournament, TournamentParticipant


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    """Admin interface for Tournament model."""
    list_display = ('name', 'game', 'date', 'prize_pool', 'created_by', 'created_at')
    list_filter = ('game', 'date', 'created_at')
    search_fields = ('name', 'game', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TournamentParticipant)
class TournamentParticipantAdmin(admin.ModelAdmin):
    """Admin interface for TournamentParticipant model."""
    list_display = ('tournament', 'user', 'joined_at')
    list_filter = ('joined_at', 'tournament')
    search_fields = ('tournament__name', 'user__username')
    readonly_fields = ('joined_at',)

