"""
AI Engine models (if needed for storing AI processing jobs).
Most AI processing will be handled by Celery tasks.
"""
from django.db import models
from django.conf import settings


class AIProcessingJob(models.Model):
    """
    Track AI processing jobs (optional - for monitoring/debugging).
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_jobs'
    )
    tournament = models.ForeignKey(
        'tournaments.Tournament',
        on_delete=models.CASCADE,
        related_name='ai_jobs',
        blank=True,
        null=True
    )
    job_type = models.CharField(max_length=50, default='match_insight', help_text="Type of AI job")
    result = models.TextField(blank=True, null=True, help_text="Job result/response")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    task_id = models.CharField(max_length=255, blank=True, null=True, help_text="Celery task ID")
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'ai_processing_job'
        ordering = ['-created_at']
        verbose_name = 'AI Processing Job'
        verbose_name_plural = 'AI Processing Jobs'
    
    def __str__(self):
        return f"AI Job for {self.user.username} - {self.tournament.name}"

