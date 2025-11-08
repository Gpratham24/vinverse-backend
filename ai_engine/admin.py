"""
Admin configuration for AI Engine models.
"""
from django.contrib import admin
from .models import AIProcessingJob


@admin.register(AIProcessingJob)
class AIProcessingJobAdmin(admin.ModelAdmin):
    """Admin interface for AIProcessingJob model."""
    list_display = ('user', 'tournament', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'tournament__name', 'task_id')
    readonly_fields = ('created_at', 'completed_at')

