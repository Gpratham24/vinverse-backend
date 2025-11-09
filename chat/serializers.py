"""
Serializers for Chat models.
"""
from rest_framework import serializers
from .models import Room, Message
from accounts.serializers import UserProfileSerializer


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for Room model."""
    message_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    created_by_username = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = [
            'id', 'name', 'display_name', 'room_type', 'game', 'description',
            'is_private', 'created_by', 'created_by_username', 'member_count',
            'message_count', 'is_member', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_member', 'created_by_username', 'member_count']
    
    def get_message_count(self, obj):
        """Get message count for room."""
        return obj.messages.count()
    
    def get_member_count(self, obj):
        """Get member count for room."""
        if obj.is_private:
            return obj.members.count()
        return None  # Public rooms don't have member lists
    
    def get_created_by_username(self, obj):
        """Get username of room creator."""
        return obj.created_by.username if obj.created_by else None
    
    def get_is_member(self, obj):
        """Check if current user is a member of private room."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if obj.is_private:
                return obj.members.filter(id=request.user.id).exists() or (obj.created_by and obj.created_by.id == request.user.id)
            return True  # Public rooms are accessible to all
        return False


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    author = UserProfileSerializer(read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'room', 'room_name', 'author', 'content', 'created_at', 'updated_at', 'is_edited']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

