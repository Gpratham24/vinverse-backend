"""
Serializers for AI Engine models.
"""
from rest_framework import serializers
from .models import AIProcessingJob
from gamerlink.models import MatchInsight
from tournaments.serializers import TournamentSerializer
import json


class MatchInsightSerializer(serializers.ModelSerializer):
    """Serializer for MatchInsight model."""
    tournament = TournamentSerializer(read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_gamer_tag = serializers.CharField(source='user.gamer_tag', read_only=True)
    
    class Meta:
        model = MatchInsight
        fields = [
            'id', 'user', 'user_username', 'user_gamer_tag', 'tournament', 
            'summary', 'strengths', 'improvements', 'score', 
            'generated_at', 'ai_model'
        ]
        read_only_fields = ['id', 'user', 'generated_at']


class AIProcessingJobSerializer(serializers.ModelSerializer):
    """Serializer for AIProcessingJob model."""
    
    class Meta:
        model = AIProcessingJob
        fields = ['id', 'user', 'task_id', 'job_type', 'status', 'result', 'error_message', 'created_at', 'completed_at']
        read_only_fields = ['id', 'user', 'created_at', 'completed_at']

