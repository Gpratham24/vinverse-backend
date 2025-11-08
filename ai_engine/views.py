"""
AI Engine API views.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from gamerlink.models import MatchInsight
from .serializers import MatchInsightSerializer
from .tasks import generate_match_insight
from tournaments.models import Tournament


class MatchInsightViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Match Insights (read-only)."""
    serializer_class = MatchInsightSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get insights for current user."""
        return MatchInsight.objects.filter(
            user=self.request.user,
            status='completed'
        ).select_related('user', 'tournament').order_by('-generated_at')
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate AI insight for a tournament."""
        tournament_id = request.data.get('tournament_id')
        
        if not tournament_id:
            return Response(
                {'error': 'tournament_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return Response(
                {'error': 'Tournament not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user participated in tournament
        # (You can add tournament participant check here)
        
        # Trigger async task
        task = generate_match_insight.delay(request.user.id, tournament_id)
        
        return Response({
            'message': 'AI insight generation started',
            'task_id': task.id,
        }, status=status.HTTP_202_ACCEPTED)

