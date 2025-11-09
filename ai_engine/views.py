"""
AI Engine API views.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from gamerlink.models import MatchInsight
from .serializers import MatchInsightSerializer
from .tasks import generate_match_insight, calculate_player_stats
from tournaments.models import Tournament
from django.contrib.auth import get_user_model

User = get_user_model()


class MatchInsightViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Match Insights (read-only)."""
    serializer_class = MatchInsightSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get insights for current user or specified user."""
        user_id = self.request.query_params.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                # Allow viewing if it's the same user or public insights
                return MatchInsight.objects.filter(
                    user=user
                ).select_related('user', 'tournament').order_by('-generated_at')
            except User.DoesNotExist:
                return MatchInsight.objects.none()
        
        return MatchInsight.objects.filter(
            user=self.request.user
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
        
        # Trigger async task
        task = generate_match_insight.delay(request.user.id, tournament_id)
        
        return Response({
            'message': 'AI insight generation started',
            'task_id': task.id,
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get player statistics."""
        user_id = request.query_params.get('user_id', request.user.id)
        game = request.query_params.get('game', None)
        
        try:
            user = User.objects.get(id=user_id)
            # Calculate stats synchronously for now (can be async if needed)
            from .tasks import calculate_win_rate, calculate_skill_consistency
            from gamerlink.models import Team
            
            tournaments = Tournament.objects.filter(participants__user=user)
            if game:
                tournaments = tournaments.filter(game=game)
            
            stats = {
                'total_tournaments': tournaments.count(),
                'win_rate': calculate_win_rate(user, game),
                'skill_consistency': calculate_skill_consistency(user, game),
                'total_xp': user.xp_points,
                'rank': user.rank or 'Unranked',
                'teams_count': Team.objects.filter(members=user).count(),
                'games_played': tournaments.values('game').distinct().count(),
            }
            
            return Response(stats, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

