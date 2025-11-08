"""
Serializers for GamerLink social features.
"""
from rest_framework import serializers
from .models import Friendship, Post, PostLike, PostComment, Team, LFTPost, MatchInsight
from accounts.serializers import UserProfileSerializer


class FriendshipSerializer(serializers.ModelSerializer):
    """Serializer for Friendship/Follow relationships."""
    follower = UserProfileSerializer(read_only=True)
    following = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Friendship
        fields = ('id', 'follower', 'following', 'is_accepted', 'created_at')
        read_only_fields = ('id', 'created_at')


class PostSerializer(serializers.ModelSerializer):
    """Serializer for social feed posts."""
    author = UserProfileSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Post
        fields = ('id', 'author', 'content', 'image', 'likes_count', 'comments_count', 'is_liked', 'created_at', 'updated_at')
        read_only_fields = ('id', 'author', 'likes_count', 'comments_count', 'is_liked', 'created_at', 'updated_at')
    
    def get_is_liked(self, obj):
        """Check if current user liked this post."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(post=obj, user=request.user).exists()
        return False


class PostCommentSerializer(serializers.ModelSerializer):
    """Serializer for PostComment model."""
    author = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = PostComment
        fields = ('id', 'post', 'author', 'content', 'created_at', 'updated_at')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model."""
    created_by = UserProfileSerializer(read_only=True)
    members = UserProfileSerializer(many=True, read_only=True)
    current_members_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Team
        fields = (
            'id', 'name', 'description', 'game', 'region', 'play_style',
            'created_by', 'members', 'max_members', 'current_members_count',
            'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'current_members_count')


class LFTPostSerializer(serializers.ModelSerializer):
    """Serializer for Looking For Team posts."""
    author = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = LFTPost
        fields = (
            'id', 'author', 'game', 'game_id', 'rank', 'region', 'play_style',
            'message', 'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')


class MatchInsightSerializer(serializers.ModelSerializer):
    """Serializer for AI Match Insights."""
    user = UserProfileSerializer(read_only=True)
    tournament_name = serializers.CharField(source='tournament.name', read_only=True)
    
    class Meta:
        model = MatchInsight
        fields = (
            'id', 'user', 'tournament', 'tournament_name', 'summary',
            'strengths', 'improvements', 'score', 'generated_at', 'ai_model'
        )
        read_only_fields = ('id', 'user', 'generated_at')

