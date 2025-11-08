"""
Notification models for user notifications.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """
    User notification model.
    Supports various notification types: follow, team_invite, message, etc.
    """
    NOTIFICATION_TYPES = [
        ('follow', 'New Follower'),
        ('team_invite', 'Team Invitation'),
        ('message', 'New Message'),
        ('tournament', 'Tournament Update'),
        ('ai_insight', 'AI Insight Ready'),
        ('like', 'Post Liked'),
        ('comment', 'New Comment'),
        ('post', 'New Post'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who receives the notification"
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField(max_length=500)
    is_read = models.BooleanField(default=False)
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        blank=True,
        null=True,
        help_text="User who triggered the notification"
    )
    related_url = models.URLField(blank=True, null=True, help_text="URL to related content")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification'
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"

