"""
Chat models for real-time messaging.
Includes: Room, Message
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import random
import string


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
    room_code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique code for private rooms (e.g., 237601)"
    )
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
    
    def generate_room_code(self):
        """Generate a unique 6-digit room code."""
        while True:
            code = ''.join(random.choices(string.digits, k=6))
            if not Room.objects.filter(room_code=code).exists():
                return code
    
    def save(self, *args, **kwargs):
        """Auto-generate room code for private rooms."""
        # Ensure room_type matches is_private
        if self.is_private and self.room_type != 'private':
            self.room_type = 'private'
        elif not self.is_private and self.room_type == 'private':
            # If not private but type is private, change to global
            self.room_type = 'global'
        
        # Only generate code if room is private and code doesn't exist
        if self.is_private and not self.room_code:
            try:
                self.room_code = self.generate_room_code()
            except Exception as e:
                # If code generation fails, still save the room
                print(f"Warning: Failed to generate room code: {e}")
        super().save(*args, **kwargs)
    
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


class RoomJoinRequest(models.Model):
    """
    Model for private room join requests.
    Users can request to join private rooms or be invited.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='join_requests',
        help_text="Private room being requested"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='room_join_requests',
        help_text="User requesting to join"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_room_invites',
        help_text="User who sent the invite/request (can be the same as user for self-requests)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_invite = models.BooleanField(default=False, help_text="True if this is an invite from room creator, False if user requested")
    message = models.TextField(max_length=200, blank=True, null=True, help_text="Optional message with request/invite")
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'room_join_request'
        ordering = ['-created_at']
        verbose_name = 'Room Join Request'
        verbose_name_plural = 'Room Join Requests'
        unique_together = [['room', 'user', 'status']]
        indexes = [
            models.Index(fields=['room', 'status']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} -> {self.room.display_name} ({self.status})"

