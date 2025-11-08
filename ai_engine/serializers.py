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
    ai_summary_parsed = serializers.SerializerMethodField()
    
    class Meta:
        model = MatchInsight
        fields = ['id', 'user', 'tournament', 'ai_summary', 'ai_summary_parsed', 'status', 'error_message', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_ai_summary_parsed(self, obj):
        """Parse AI summary JSON."""
        if obj.ai_summary:
            try:
                return json.loads(obj.ai_summary)
            except json.JSONDecodeError:
                return {'raw': obj.ai_summary}
        return None


class AIProcessingJobSerializer(serializers.ModelSerializer):
    """Serializer for AIProcessingJob model."""
    
    class Meta:
        model = AIProcessingJob
        fields = ['id', 'user', 'task_id', 'job_type', 'status', 'result', 'error_message', 'created_at', 'completed_at']
        read_only_fields = ['id', 'user', 'created_at', 'completed_at']

