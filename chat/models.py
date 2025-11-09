"""
Chat models for real-time messaging.
Includes: Room, Message
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Room(models.Model):
    """
    Chat room model.
    Can be: Global Lobby, Game-specific, Team-specific, or Private.
    """
    ROOM_TYPES = [
        ('global', 'Global Lobby'),
        ('game', 'Game Channel'),
        ('team', 'Team Room'),
        ('private', 'Private Room'),
    ]
    
    name = models.CharField(max_length=200, unique=True, help_text="Room name/slug")
    display_name = models.CharField(max_length=200, help_text="Display name for UI")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='global')
    game = models.CharField(max_length=100, blank=True, null=True, help_text="Game for game-specific rooms")
    team = models.ForeignKey(
        'gamerlink.Team',
        on_delete=models.CASCADE,
        related_name='chat_rooms',
        blank=True,
        null=True,
        help_text="Team for team-specific rooms"
    )
    description = models.TextField(max_length=500, blank=True, null=True)
    is_private = models.BooleanField(default=False, help_text="Private rooms require invitation")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_chat_rooms',
        blank=True,
        null=True,
        help_text="User who created this room (for private rooms)"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='chat_rooms',
        blank=True,
        help_text="Members of private rooms"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'room'
        ordering = ['room_type', 'display_name']
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
    
    def __str__(self):
        return f"{self.display_name} ({self.room_type})"


class Message(models.Model):
    """
    Chat message model.
    Messages belong to a room and have an author.
    """
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Room this message belongs to"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="User who sent the message"
    )
    content = models.TextField(max_length=1000, help_text="Message content")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'message'
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['room', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.author.username} in {self.room.name}: {self.content[:50]}"

