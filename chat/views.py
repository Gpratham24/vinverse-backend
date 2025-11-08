"""
Chat API views for REST endpoints.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Room, Message
from .serializers import RoomSerializer, MessageSerializer
from django.db.models import Q


class RoomViewSet(viewsets.ModelViewSet):
    """ViewSet for Chat Rooms."""
    queryset = Room.objects.filter(is_active=True)
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter rooms based on user access."""
        user = self.request.user
        queryset = Room.objects.filter(is_active=True)
        
        # Filter by room type
        room_type = self.request.query_params.get('type', None)
        if room_type:
            queryset = queryset.filter(room_type=room_type)
        
        # Filter by game
        game = self.request.query_params.get('game', None)
        if game:
            queryset = queryset.filter(game__icontains=game)
        
        # For team rooms, only show if user is a member
        team_rooms = queryset.filter(room_type='team')
        accessible_team_rooms = []
        for room in team_rooms:
            if room.team and user in room.team.members.all():
                accessible_team_rooms.append(room.id)
        
        # Combine global/game rooms with accessible team rooms
        return queryset.filter(
            Q(room_type__in=['global', 'game']) | Q(id__in=accessible_team_rooms)
        ).order_by('room_type', 'display_name')
    
    @action(detail=False, methods=['get'])
    def default_rooms(self, request):
        """Get default rooms (Global Lobby + game channels)."""
        rooms = Room.objects.filter(
            is_active=True,
            room_type__in=['global', 'game']
        ).order_by('room_type', 'display_name')
        
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Chat Messages (read-only via REST, real-time via WebSocket)."""
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get messages for a specific room."""
        room_name = self.request.query_params.get('room', None)
        if room_name:
            try:
                room = Room.objects.get(name=room_name, is_active=True)
                # Check access for team rooms
                if room.room_type == 'team' and room.team:
                    if self.request.user not in room.team.members.all():
                        return Message.objects.none()
                return Message.objects.filter(room=room).select_related('author').order_by('created_at')
            except Room.DoesNotExist:
                return Message.objects.none()
        return Message.objects.none()

