"""
Custom User model extending AbstractUser for esports profiles.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Extended user model with esports-specific fields.
    Fields: username, email (from AbstractUser) + bio, rank, gamer_tag, verified, vin_id
    """
    bio = models.TextField(max_length=500, blank=True, null=True, help_text="User bio/description")
    rank = models.CharField(max_length=100, blank=True, null=True, help_text="Gaming rank/tier")
    gamer_tag = models.CharField(max_length=50, blank=True, null=True, help_text="In-game username/tag")
    verified = models.BooleanField(default=False, help_text="Verified badge status")
    vin_id = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="Unique VinVerse ID (e.g., VIN-0000001)"
    )
    xp_points = models.IntegerField(default=0, help_text="XP points for gamification")
    is_online = models.BooleanField(default=False, help_text="Online status")
    last_seen = models.DateTimeField(auto_now=True, help_text="Last seen timestamp")
    
    class Meta:
        db_table = 'custom_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.vin_id})" if self.vin_id else self.username
    
    def save(self, *args, **kwargs):
        """
        Auto-generate VIN ID if not set.
        Format: VIN-0000001, VIN-0000002, etc.
        """
        if not self.vin_id:
            # Get all existing VIN IDs and find the highest number
            existing_vins = CustomUser.objects.exclude(
                vin_id__isnull=True
            ).exclude(
                vin_id=''
            ).values_list('vin_id', flat=True)
            
            max_number = 0
            for vin in existing_vins:
                try:
                    # Extract number from VIN (e.g., "VIN-0000001" -> 1)
                    number = int(vin.split('-')[1])
                    max_number = max(max_number, number)
                except (IndexError, ValueError):
                    # Skip invalid VIN formats
                    continue
            
            # Next VIN number
            next_number = max_number + 1
            
            # Format as VIN-0000001 (7 digits with leading zeros)
            self.vin_id = f"VIN-{next_number:07d}"
        
        super().save(*args, **kwargs)

