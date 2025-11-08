"""
Admin configuration for Chat models.
"""
from django.contrib import admin
from .models import Room, Message


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin interface for Room model."""
    list_display = ('name', 'display_name', 'room_type', 'game', 'is_active', 'created_at')
    list_filter = ('room_type', 'is_active', 'created_at')
    search_fields = ('name', 'display_name', 'game')
    readonly_fields = ('created_at',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for Message model."""
    list_display = ('author', 'room', 'content_preview', 'is_edited', 'created_at')
    list_filter = ('is_edited', 'created_at', 'room')
    search_fields = ('author__username', 'content', 'room__name')
    readonly_fields = ('created_at', 'updated_at')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

