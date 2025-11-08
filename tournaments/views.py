"""
API views for Tournament CRUD operations.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import Tournament, TournamentParticipant
from .serializers import TournamentSerializer, TournamentParticipantSerializer


class TournamentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tournament CRUD operations.
    Endpoints:
    - GET /api/tournaments/ - List all tournaments
    - POST /api/tournaments/ - Create new tournament
    - GET /api/tournaments/{id}/ - Get tournament details
    - PUT /api/tournaments/{id}/ - Update tournament (creator only)
    - DELETE /api/tournaments/{id}/ - Delete tournament (creator only)
    - POST /api/tournaments/{id}/join/ - Join tournament
    - DELETE /api/tournaments/{id}/leave/ - Leave tournament
    - GET /api/tournaments/{id}/participants/ - Get tournament participants
    """
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for this viewset
    
    def get_queryset(self):
        """Return tournaments with participant count."""
        return Tournament.objects.annotate(
            participant_count=Count('participants')
        ).order_by('-date')
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """Set created_by to current user when creating tournament."""
        serializer.save(created_by=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Only allow creator to update tournament."""
        tournament = self.get_object()
        if tournament.created_by != request.user:
            return Response(
                {'error': 'You can only edit tournaments you created.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only allow creator to delete tournament."""
        tournament = self.get_object()
        if tournament.created_by != request.user:
            return Response(
                {'error': 'You can only delete tournaments you created.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a tournament."""
        tournament = self.get_object()
        user = request.user
        
        # Check if already joined
        if TournamentParticipant.objects.filter(tournament=tournament, user=user).exists():
            return Response(
                {'error': 'You have already joined this tournament.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create participant
        participant = TournamentParticipant.objects.create(
            tournament=tournament,
            user=user
        )
        
        return Response({
            'message': 'Successfully joined tournament',
            'participant': TournamentParticipantSerializer(participant).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def leave(self, request, pk=None):
        """Leave a tournament."""
        tournament = self.get_object()
        user = request.user
        
        try:
            participant = TournamentParticipant.objects.get(
                tournament=tournament,
                user=user
            )
            participant.delete()
            return Response(
                {'message': 'Successfully left tournament'},
                status=status.HTTP_200_OK
            )
        except TournamentParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant of this tournament.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """Get all participants of a tournament."""
        tournament = self.get_object()
        search_query = request.query_params.get('search', '').strip()
        
        participants = TournamentParticipant.objects.filter(tournament=tournament)
        
        # Search by username, email, or gamer_tag
        if search_query:
            participants = participants.filter(
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(user__gamer_tag__icontains=search_query)
            )
        
        serializer = TournamentParticipantSerializer(participants, many=True)
        return Response({
            'tournament': tournament.name,
            'participants': serializer.data,
            'count': participants.count()
        })

