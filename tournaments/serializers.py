"""
Serializers for Tournament CRUD operations.
"""
from rest_framework import serializers
from .models import Tournament, TournamentParticipant
from accounts.serializers import UserProfileSerializer


class TournamentParticipantSerializer(serializers.ModelSerializer):
    """
    Serializer for Tournament Participant.
    """
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = TournamentParticipant
        fields = ('id', 'user', 'joined_at')
        read_only_fields = ('id', 'joined_at')


class TournamentSerializer(serializers.ModelSerializer):
    """
    Serializer for Tournament model.
    Includes created_by user info and participants in read operations.
    """
    created_by = UserProfileSerializer(read_only=True)
    created_by_id = serializers.IntegerField(write_only=True, required=False)
    participants = serializers.SerializerMethodField()  # Only show in detail view
    participant_count = serializers.SerializerMethodField()
    is_joined = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()
    
    class Meta:
        model = Tournament
        fields = (
            'id', 'name', 'game', 'date', 'prize_pool', 
            'created_by', 'created_by_id', 'created_at', 'updated_at',
            'participants', 'participant_count', 'is_joined', 'is_creator'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'participants', 'participant_count', 'is_joined', 'is_creator')
    
    def get_participants(self, obj):
        """Get participants list (only in detail view, empty in list view for performance)."""
        # Only return participants in detail view (when viewing single tournament)
        # In list view, return empty to avoid loading all participants
        view = self.context.get('view')
        if view and hasattr(view, 'action') and view.action == 'retrieve':
            return TournamentParticipantSerializer(obj.participants.all()[:50], many=True).data
        return []  # Empty array in list view
    
    def get_participant_count(self, obj):
        """Get count of participants."""
        # Use annotated count if available, otherwise count manually
        if hasattr(obj, 'participant_count'):
            return obj.participant_count
        return obj.participants.count()
    
    def get_is_joined(self, obj):
        """Check if current user has joined this tournament."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return TournamentParticipant.objects.filter(
                tournament=obj, 
                user=request.user
            ).exists()
        return False
    
    def get_is_creator(self, obj):
        """Check if current user is the creator of this tournament."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.created_by == request.user
        return False
    
    def create(self, validated_data):
        """Create tournament and set created_by to current user."""
        validated_data.pop('created_by_id', None)
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

