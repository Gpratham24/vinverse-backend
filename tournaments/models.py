"""
Tournament model for esports tournament management.
"""
from django.db import models
from django.conf import settings


class Tournament(models.Model):
    """
    Tournament model with fields: name, game, date, prize_pool, created_by.
    """
    name = models.CharField(max_length=200, help_text="Tournament name")
    game = models.CharField(max_length=100, help_text="Game title (e.g., Valorant, CS2)")
    date = models.DateTimeField(help_text="Tournament date and time")
    prize_pool = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        help_text="Prize pool amount"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_tournaments',
        help_text="User who created this tournament"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tournament'
        ordering = ['-date']
        verbose_name = 'Tournament'
        verbose_name_plural = 'Tournaments'
    
    def __str__(self):
        return f"{self.name} - {self.game}"


class TournamentParticipant(models.Model):
    """
    Model to track which users have joined which tournaments.
    """
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='participants',
        help_text="Tournament the user joined"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='joined_tournaments',
        help_text="User who joined the tournament"
    )
    joined_at = models.DateTimeField(auto_now_add=True, help_text="When the user joined")
    
    class Meta:
        db_table = 'tournament_participant'
        unique_together = ['tournament', 'user']  # Prevent duplicate joins
        ordering = ['-joined_at']
        verbose_name = 'Tournament Participant'
        verbose_name_plural = 'Tournament Participants'
    
    def __str__(self):
        return f"{self.user.username} joined {self.tournament.name}"

