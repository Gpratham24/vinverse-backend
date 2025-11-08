"""
GamerLink models for social networking features.
Includes: Friendship, Post, Team, MatchInsight
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Friendship(models.Model):
    """
    Friendship/Follow relationship between users.
    Symmetric relationship (user A follows user B).
    """
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        help_text="User who is following"
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers',
        help_text="User being followed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=True, help_text="For future friend requests")
    
    class Meta:
        db_table = 'friendship'
        unique_together = ['follower', 'following']
        ordering = ['-created_at']
        verbose_name = 'Friendship'
        verbose_name_plural = 'Friendships'
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Post(models.Model):
    """
    User posts for social feed.
    Text posts with optional images.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        help_text="User who created the post"
    )
    content = models.TextField(max_length=1000, help_text="Post content")
    image = models.ImageField(upload_to='posts/', blank=True, null=True, help_text="Optional post image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'post'
        ordering = ['-created_at']
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
    
    def __str__(self):
        return f"Post by {self.author.username} - {self.content[:50]}"
    
    @property
    def likes_count(self):
        """Get count of likes for this post."""
        return self.likes.count()
    
    @property
    def comments_count(self):
        """Get count of comments for this post."""
        return self.comments.count()


class PostLike(models.Model):
    """
    Like model for posts.
    Users can like posts.
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
        help_text="Post that was liked"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_likes',
        help_text="User who liked the post"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'post_like'
        unique_together = ['post', 'user']
        ordering = ['-created_at']
        verbose_name = 'Post Like'
        verbose_name_plural = 'Post Likes'
    
    def __str__(self):
        return f"{self.user.username} liked post {self.post.id}"


class PostComment(models.Model):
    """
    Comment model for posts.
    Users can comment on posts.
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="Post that was commented on"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_comments',
        help_text="User who wrote the comment"
    )
    content = models.TextField(max_length=500, help_text="Comment content")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'post_comment'
        ordering = ['created_at']
        verbose_name = 'Post Comment'
        verbose_name_plural = 'Post Comments'
    
    def __str__(self):
        return f"{self.author.username} commented on post {self.post.id}"


class Team(models.Model):
    """
    Esports team model.
    Teams can be created by users and have members.
    """
    name = models.CharField(max_length=200, help_text="Team name")
    description = models.TextField(max_length=500, blank=True, null=True)
    game = models.CharField(max_length=100, help_text="Primary game (e.g., Valorant, BGMI)")
    region = models.CharField(max_length=100, blank=True, null=True, help_text="Region/timezone")
    play_style = models.CharField(
        max_length=50,
        choices=[
            ('casual', 'Casual'),
            ('competitive', 'Competitive'),
            ('professional', 'Professional'),
        ],
        default='casual'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_teams',
        help_text="User who created the team"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teams',
        blank=True,
        help_text="Team members"
    )
    max_members = models.IntegerField(default=5, help_text="Maximum team size")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'team'
        ordering = ['-created_at']
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'
    
    def __str__(self):
        return f"{self.name} ({self.game})"
    
    @property
    def current_members_count(self):
        return self.members.count()


class LFTPost(models.Model):
    """
    Looking For Team (LFT) posts.
    Users post when they're looking for a team.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lft_posts',
        help_text="User looking for team"
    )
    game = models.CharField(max_length=100, help_text="Game they want to play")
    game_id = models.CharField(max_length=100, blank=True, null=True, help_text="In-game ID/Username for the game")
    rank = models.CharField(max_length=100, blank=True, null=True, help_text="Current rank")
    region = models.CharField(max_length=100, blank=True, null=True, help_text="Region/timezone")
    play_style = models.CharField(
        max_length=50,
        choices=[
            ('casual', 'Casual'),
            ('competitive', 'Competitive'),
            ('professional', 'Professional'),
        ],
        default='casual'
    )
    message = models.TextField(max_length=500, help_text="LFT message")
    is_active = models.BooleanField(default=True, help_text="Is this LFT post still active?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lft_post'
        ordering = ['-created_at']
        verbose_name = 'LFT Post'
        verbose_name_plural = 'LFT Posts'
    
    def __str__(self):
        return f"LFT by {self.author.username} - {self.game}"


class MatchInsight(models.Model):
    """
    AI-generated match insights for players.
    Generated after tournaments using AI analysis.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='match_insights',
        help_text="User this insight is for"
    )
    tournament = models.ForeignKey(
        'tournaments.Tournament',
        on_delete=models.CASCADE,
        related_name='insights',
        help_text="Tournament this insight is based on"
    )
    summary = models.TextField(help_text="AI-generated performance summary")
    strengths = models.JSONField(default=list, help_text="List of identified strengths")
    improvements = models.JSONField(default=list, help_text="List of suggested improvements")
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Overall performance score (0-100)"
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    ai_model = models.CharField(
        max_length=50,
        default='gpt-4',
        help_text="AI model used for generation"
    )
    
    class Meta:
        db_table = 'match_insight'
        ordering = ['-generated_at']
        verbose_name = 'Match Insight'
        verbose_name_plural = 'Match Insights'
        unique_together = ['user', 'tournament']
    
    def __str__(self):
        return f"Insight for {self.user.username} - {self.tournament.name}"

