"""
Admin configuration for GamerLink models.
"""
from django.contrib import admin
from .models import Friendship, Post, PostLike, PostComment, Team, LFTPost, MatchInsight


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    """Admin interface for Friendship model."""
    list_display = ('follower', 'following', 'is_accepted', 'created_at')
    list_filter = ('is_accepted', 'created_at')
    search_fields = ('follower__username', 'following__username')
    readonly_fields = ('created_at',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin interface for Post model."""
    list_display = ('author', 'content_preview', 'likes_count', 'comments_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('author__username', 'content')
    readonly_fields = ('created_at', 'updated_at', 'likes_count', 'comments_count')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Admin interface for Team model."""
    list_display = ('name', 'game', 'play_style', 'created_by', 'current_members_count', 'max_members', 'is_active', 'created_at')
    list_filter = ('game', 'play_style', 'is_active', 'created_at')
    search_fields = ('name', 'game', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('members',)


@admin.register(LFTPost)
class LFTPostAdmin(admin.ModelAdmin):
    """Admin interface for LFTPost model."""
    list_display = ('author', 'game', 'rank', 'play_style', 'is_active', 'created_at')
    list_filter = ('game', 'play_style', 'is_active', 'created_at')
    search_fields = ('author__username', 'game', 'rank')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    """Admin interface for PostLike model."""
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__content')
    readonly_fields = ('created_at',)


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    """Admin interface for PostComment model."""
    list_display = ('author', 'post', 'content_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('author__username', 'content', 'post__content')
    readonly_fields = ('created_at', 'updated_at')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(MatchInsight)
class MatchInsightAdmin(admin.ModelAdmin):
    """Admin interface for MatchInsight model."""
    list_display = ('user', 'tournament', 'score', 'ai_model', 'generated_at')
    list_filter = ('ai_model', 'generated_at')
    search_fields = ('user__username', 'tournament__name')
    readonly_fields = ('generated_at',)

