"""
Chat API views for REST endpoints.
"""
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Room, Message, RoomJoinRequest
from .serializers import RoomSerializer, MessageSerializer, RoomJoinRequestSerializer
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
import traceback

User = get_user_model()


class RoomViewSet(viewsets.ModelViewSet):
    """ViewSet for Chat Rooms."""
    queryset = Room.objects.filter(is_active=True)
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        """Filter rooms based on user access."""
        try:
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
            
            # Filter by public/private
            is_private = self.request.query_params.get('is_private', None)
            if is_private is not None:
                queryset = queryset.filter(is_private=is_private.lower() == 'true')
            
            # For team rooms, only show if user is a member
            team_rooms = queryset.filter(room_type='team')
            accessible_team_rooms = []
            for room in team_rooms:
                try:
                    if room.team and user in room.team.members.all():
                        accessible_team_rooms.append(room.id)
                except Exception:
                    continue
            
            # For private rooms, only show if user is a member or creator
            # Use prefetch_related to optimize member queries
            private_rooms = queryset.filter(
                room_type='private', 
                is_private=True
            ).prefetch_related('members', 'created_by')
            accessible_private_rooms = []
            for room in private_rooms:
                try:
                    # Check if user is creator
                    is_creator = room.created_by and room.created_by.id == user.id
                    # Check if user is a member (optimized with prefetch)
                    is_member = user.id in [m.id for m in room.members.all()]
                    if is_member or is_creator:
                        accessible_private_rooms.append(room.id)
                except Exception as e:
                    print(f"Error checking room access: {e}")
                    continue
            
            # Combine public rooms with accessible team/private rooms
            # Handle empty lists to avoid query issues
            if not accessible_team_rooms and not accessible_private_rooms:
                return queryset.filter(
                    Q(room_type__in=['global', 'game'], is_private=False)
                ).order_by('room_type', 'display_name')
            
            if not accessible_team_rooms:
                return queryset.filter(
                    Q(room_type__in=['global', 'game'], is_private=False) |
                    Q(id__in=accessible_private_rooms)
                ).order_by('room_type', 'display_name')
            
            if not accessible_private_rooms:
                return queryset.filter(
                    Q(room_type__in=['global', 'game'], is_private=False) |
                    Q(id__in=accessible_team_rooms)
                ).order_by('room_type', 'display_name')
            
            return queryset.filter(
                Q(room_type__in=['global', 'game'], is_private=False) |
                Q(id__in=accessible_team_rooms) |
                Q(id__in=accessible_private_rooms)
            ).order_by('room_type', 'display_name')
        except Exception as e:
            # Fallback to basic query on error
            return Room.objects.filter(is_active=True, room_type__in=['global', 'game'], is_private=False).order_by('room_type', 'display_name')
    
    def perform_create(self, serializer):
        """Set created_by when creating a room."""
        try:
            room = serializer.save(created_by=self.request.user)
            # Room code should be auto-generated in model's save() method
            # But ensure it's set if somehow it wasn't
            if room.is_private and not room.room_code:
                try:
                    room.room_code = room.generate_room_code()
                    room.save(update_fields=['room_code'])
                except Exception as e:
                    print(f"Warning: Could not generate room code: {e}")
            return room
        except Exception as e:
            print(f"Error creating room: {e}")
            print(traceback.format_exc())
            raise serializers.ValidationError({'error': f'Failed to create room: {str(e)}'})
    
    @action(detail=False, methods=['get'])
    def default_rooms(self, request):
        """Get default rooms (Global Lobby + game channels)."""
        try:
            rooms = Room.objects.filter(
                is_active=True,
                room_type__in=['global', 'game']
            ).order_by('room_type', 'display_name')
            
            serializer = self.get_serializer(rooms, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            print(f"Error in default_rooms: {e}")
            print(traceback.format_exc())
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def invite_user(self, request, pk=None):
        """Invite a user to a private room (room creator only)."""
        room = self.get_object()
        user = request.user
        
        # Check if user is the room creator
        if not room.is_private or room.created_by != user:
            return Response(
                {'error': 'Only the room creator can invite users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        username = request.data.get('username')
        if not username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            invitee = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is already a member
        if invitee in room.members.all() or invitee == room.created_by:
            return Response(
                {'error': 'User is already a member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update join request as invite
        join_request, created = RoomJoinRequest.objects.get_or_create(
            room=room,
            user=invitee,
            status='pending',
            defaults={
                'requested_by': user,
                'is_invite': True,
                'message': request.data.get('message', '')
            }
        )
        
        if not created:
            # Update existing request
            join_request.status = 'pending'
            join_request.is_invite = True
            join_request.requested_by = user
            join_request.message = request.data.get('message', '')
            join_request.save()
        
        serializer = RoomJoinRequestSerializer(join_request, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def request_join(self, request, pk=None):
        """Request to join a private room."""
        room = self.get_object()
        user = request.user
        
        if not room.is_private:
            return Response(
                {'error': 'This room is not private'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is already a member
        if user in room.members.all() or user == room.created_by:
            return Response(
                {'error': 'You are already a member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create join request
        join_request, created = RoomJoinRequest.objects.get_or_create(
            room=room,
            user=user,
            status='pending',
            defaults={
                'requested_by': user,
                'is_invite': False,
                'message': request.data.get('message', '')
            }
        )
        
        if not created:
            # Update existing request
            join_request.status = 'pending'
            join_request.message = request.data.get('message', '')
            join_request.save()
        
        serializer = RoomJoinRequestSerializer(join_request, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def search_private(self, request):
        """Search for private rooms by name, ID, or room code."""
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search by name, ID, or room code
        rooms = Room.objects.filter(
            is_private=True,
            is_active=True
        ).filter(
            Q(display_name__icontains=query) | 
            Q(name__icontains=query) | 
            Q(id__icontains=query) |
            Q(room_code=query)  # Exact match for room code
        )[:20]  # Limit results
        
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
                # Check access for private rooms
                if room.is_private:
                    if self.request.user not in room.members.all() and self.request.user != room.created_by:
                        return Message.objects.none()
                return Message.objects.filter(room=room).select_related('author').order_by('created_at')
            except Room.DoesNotExist:
                return Message.objects.none()
        return Message.objects.none()


class RoomJoinRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for Room Join Requests."""
    queryset = RoomJoinRequest.objects.all()
    serializer_class = RoomJoinRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        """Get join requests relevant to the user."""
        user = self.request.user
        
        # Get requests where user is the requester or room creator
        return RoomJoinRequest.objects.filter(
            Q(user=user) | Q(room__created_by=user)
        ).select_related('user', 'requested_by', 'room').order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a join request (room creator only)."""
        join_request = self.get_object()
        user = request.user
        
        # Check if user is the room creator
        if join_request.room.created_by != user:
            return Response(
                {'error': 'Only the room creator can accept requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if join_request.status != 'pending':
            return Response(
                {'error': 'Request has already been processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user to room members
        join_request.room.members.add(join_request.user)
        join_request.status = 'accepted'
        join_request.responded_at = timezone.now()
        join_request.save()
        
        serializer = self.get_serializer(join_request, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a join request (room creator only)."""
        join_request = self.get_object()
        user = request.user
        
        # Check if user is the room creator
        if join_request.room.created_by != user:
            return Response(
                {'error': 'Only the room creator can reject requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if join_request.status != 'pending':
            return Response(
                {'error': 'Request has already been processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        join_request.status = 'rejected'
        join_request.responded_at = timezone.now()
        join_request.save()
        
        serializer = self.get_serializer(join_request, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending requests for rooms the user created."""
        try:
            user = request.user
            pending_requests = RoomJoinRequest.objects.filter(
                room__created_by=user,
                room__created_by__isnull=False,
                status='pending'
            ).select_related('user', 'requested_by', 'room').order_by('-created_at')
            
            serializer = self.get_serializer(pending_requests, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            print(f"Error in pending requests: {e}")
            print(traceback.format_exc())
            return Response(
                {'error': str(e), 'detail': 'Failed to fetch pending requests'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

