"""
Serializers for Chat models.
"""
from rest_framework import serializers
from .models import Room, Message
from accounts.serializers import UserProfileSerializer


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for Room model."""
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = ['id', 'name', 'display_name', 'room_type', 'game', 'description', 'message_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_message_count(self, obj):
        """Get message count for room."""
        return obj.messages.count()


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    author = UserProfileSerializer(read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'room', 'room_name', 'author', 'content', 'created_at', 'updated_at', 'is_edited']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

