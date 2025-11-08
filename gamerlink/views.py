"""
GamerLink API views for social networking features.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count
from .models import Friendship, Post, Team, LFTPost, MatchInsight
from .serializers import (
    FriendshipSerializer, PostSerializer, TeamSerializer,
    LFTPostSerializer, MatchInsightSerializer
)
from accounts.models import CustomUser
from accounts.serializers import UserProfileSerializer


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def follow_user(request, user_id):
    """
    Follow or unfollow a user.
    POST /api/gamerlink/follow/{user_id}/ - Follow user
    DELETE /api/gamerlink/follow/{user_id}/ - Unfollow user
    """
    try:
        target_user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.user.id == target_user.id:
        return Response(
            {'error': 'Cannot follow yourself'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if request.method == 'POST':
        # Use get_or_create to handle race conditions (idempotent operation)
        friendship, created = Friendship.objects.get_or_create(
            follower=request.user,
            following=target_user,
            defaults={'is_accepted': True}
        )
        
        # If friendship already existed, ensure it's accepted
        if not created:
            if not friendship.is_accepted:
                friendship.is_accepted = True
                friendship.save()
            # Return success even if already following (idempotent - no error)
            # This handles double-click/race conditions gracefully
            return Response({
                'message': f'Already following {target_user.username}',
                'friendship': FriendshipSerializer(friendship).data
            }, status=status.HTTP_200_OK)
        
        # Only create notification for NEW follows (when created=True)
        try:
            from notifications.models import Notification
            # Check if notification already exists to avoid duplicates
            Notification.objects.get_or_create(
                user=target_user,
                notification_type='follow',
                related_user=request.user,
                defaults={
                    'title': 'New Follower',
                    'message': f"{request.user.username} started following you",
                    'related_url': f'/profile/{request.user.id}'
                }
            )
        except Exception as e:
            # If notification creation fails, log but don't fail the follow operation
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create notification for follow: {e}")
        
        return Response({
            'message': f'Now following {target_user.username}',
            'friendship': FriendshipSerializer(friendship).data
        }, status=status.HTTP_201_CREATED)
    
    elif request.method == 'DELETE':
        # Unfollow user
        try:
            friendship = Friendship.objects.get(
                follower=request.user,
                following=target_user
            )
            friendship.delete()
            return Response(
                {'message': f'Unfollowed {target_user.username}'},
                status=status.HTTP_200_OK
            )
        except Friendship.DoesNotExist:
            return Response(
                {'error': 'Not following this user'},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_feed(request):
    """
    Get social feed - all posts or filtered by user.
    GET /api/gamerlink/feed/?filter=all|following|my
    """
    filter_type = request.query_params.get('filter', 'all')
    
    if filter_type == 'my':
        # Only current user's posts
        posts = Post.objects.filter(author=request.user)
    elif filter_type == 'following':
        # Posts from users you follow
        following_ids = Friendship.objects.filter(
            follower=request.user,
            is_accepted=True
        ).values_list('following_id', flat=True)
        posts = Post.objects.filter(author_id__in=following_ids)
    else:
        # All posts (default)
        posts = Post.objects.all()
    
    # Order by newest first and limit
    posts = posts.select_related('author').order_by('-created_at')[:100]
    
    serializer = PostSerializer(posts, many=True)
    return Response({
        'posts': serializer.data,
        'count': len(serializer.data),
        'filter': filter_type
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_connections(request, user_id):
    """
    Get user's followers and following lists.
    GET /api/gamerlink/connections/{user_id}/
    Public read access - anyone can see followers/following lists.
    """
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get followers (public data)
    followers = Friendship.objects.filter(
        following=user,
        is_accepted=True
    ).select_related('follower')
    
    # Get following (public data)
    following = Friendship.objects.filter(
        follower=user,
        is_accepted=True
    ).select_related('following')
    
    # Check if current user follows this user (only if authenticated)
    is_following = False
    if request.user.is_authenticated and request.user.id != user.id:
        is_following = Friendship.objects.filter(
            follower=request.user,
            following=user,
            is_accepted=True
        ).exists()
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'vin_id': user.vin_id,
        },
        'followers': [UserProfileSerializer(f.follower).data for f in followers],
        'following': [UserProfileSerializer(f.following).data for f in following],
        'followers_count': followers.count(),
        'following_count': following.count(),
        'is_following': is_following,
    })


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for Post CRUD operations."""
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return posts, ordered by newest first."""
        return Post.objects.all().select_related('author').prefetch_related('likes', 'comments').order_by('-created_at')
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """Set author to current user when creating post and notify followers."""
        post = serializer.save(author=self.request.user)
        
        # Create notification for followers when user posts
        from notifications.models import Notification
        followers = Friendship.objects.filter(
            following=self.request.user,
            is_accepted=True
        ).select_related('follower')
        
        for friendship in followers:
            Notification.objects.create(
                user=friendship.follower,
                notification_type='post',
                title='New Post',
                message=f"{self.request.user.username} posted: {post.content[:50]}...",
                related_user=self.request.user,
                related_url='/feed'
            )
        
        return post
    
    @action(detail=True, methods=['post', 'delete'])
    def like(self, request, pk=None):
        """Like or unlike a post."""
        post = self.get_object()
        from .models import PostLike
        
        if request.method == 'POST':
            # Like the post
            like, created = PostLike.objects.get_or_create(
                post=post,
                user=request.user
            )
            if created:
                # Create notification
                from notifications.models import Notification
                if post.author != request.user:
                    Notification.objects.create(
                        user=post.author,
                        notification_type='like',
                        title='Post Liked',
                        message=f"{request.user.username} liked your post",
                        related_user=request.user,
                        related_url='/feed'
                    )
                return Response({'message': 'Post liked', 'liked': True}, status=status.HTTP_201_CREATED)
            return Response({'message': 'Already liked', 'liked': True}, status=status.HTTP_200_OK)
        else:
            # Unlike the post
            PostLike.objects.filter(post=post, user=request.user).delete()
            return Response({'message': 'Post unliked', 'liked': False}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """Get or create comments for a post."""
        post = self.get_object()
        from .models import PostComment
        from .serializers import PostCommentSerializer
        
        if request.method == 'GET':
            # Get comments
            comments = PostComment.objects.filter(post=post).select_related('author').order_by('created_at')
            serializer = PostCommentSerializer(comments, many=True)
            return Response(serializer.data)
        else:
            # Create comment
            content = request.data.get('content', '').strip()
            if not content:
                return Response({'error': 'Comment content is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            comment = PostComment.objects.create(
                post=post,
                author=request.user,
                content=content
            )
            
            # Create notification
            from notifications.models import Notification
            if post.author != request.user:
                Notification.objects.create(
                    user=post.author,
                    notification_type='comment',
                    title='New Comment',
                    message=f"{request.user.username} commented on your post",
                    related_user=request.user,
                    related_url='/feed'
                )
            
            serializer = PostCommentSerializer(comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeamViewSet(viewsets.ModelViewSet):
    """ViewSet for Team CRUD operations."""
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return teams with member counts."""
        return Team.objects.annotate(
            current_members_count=Count('members')
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set created_by to current user."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a team."""
        team = self.get_object()
        if team.members.count() >= team.max_members:
            return Response(
                {'error': 'Team is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        team.members.add(request.user)
        return Response({'message': 'Joined team successfully'})
    
    @action(detail=True, methods=['delete'])
    def leave(self, request, pk=None):
        """Leave a team."""
        team = self.get_object()
        team.members.remove(request.user)
        return Response({'message': 'Left team successfully'})


class LFTPostViewSet(viewsets.ModelViewSet):
    """ViewSet for LFT (Looking For Team) posts."""
    queryset = LFTPost.objects.filter(is_active=True)
    serializer_class = LFTPostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination to return array directly
    
    def get_queryset(self):
        """Filter LFT posts with search parameters."""
        queryset = LFTPost.objects.filter(is_active=True)
        
        # Filter by game
        game = self.request.query_params.get('game', None)
        if game:
            queryset = queryset.filter(game__icontains=game)
        
        # Filter by game_id
        game_id = self.request.query_params.get('game_id', None)
        if game_id:
            queryset = queryset.filter(game_id__icontains=game_id)
        
        # Filter by rank
        rank = self.request.query_params.get('rank', None)
        if rank:
            queryset = queryset.filter(rank__icontains=rank)
        
        # Filter by region
        region = self.request.query_params.get('region', None)
        if region:
            queryset = queryset.filter(region__icontains=region)
        
        # Filter by play style
        play_style = self.request.query_params.get('play_style', None)
        if play_style:
            queryset = queryset.filter(play_style=play_style)
        
        return queryset.select_related('author').order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """Override list to return array directly."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Set author to current user."""
        serializer.save(author=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get AI-powered teammate recommendations."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        user = request.user
        game_filter = request.query_params.get('game', None)
        
        # Get user's profile data
        user_data = {
            'rank': user.rank or '',
            'gamer_tag': user.gamer_tag or '',
        }
        
        # Get all active LFT posts (excluding user's own)
        lft_posts = LFTPost.objects.filter(
            is_active=True
        ).exclude(author=user).select_related('author')
        
        if game_filter:
            lft_posts = lft_posts.filter(game__icontains=game_filter)
        
        if not lft_posts.exists():
            return Response({'recommendations': []})
        
        # Build feature vectors for similarity matching
        user_features = f"{user_data['rank']} {user_data['gamer_tag']}".lower()
        
        recommendations = []
        for post in lft_posts:
            post_features = f"{post.rank or ''} {post.game or ''} {post.play_style or ''}".lower()
            
            # Simple cosine similarity on text features
            try:
                vectorizer = TfidfVectorizer()
                vectors = vectorizer.fit_transform([user_features, post_features])
                similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
                
                # Calculate additional match score
                match_score = similarity
                if user_data['rank'] and post.rank and user_data['rank'].lower() == post.rank.lower():
                    match_score += 0.2
                if game_filter and game_filter.lower() in post.game.lower():
                    match_score += 0.1
                
                recommendations.append({
                    'post': {
                        'id': post.id,
                        'author': {
                            'id': post.author.id,
                            'username': post.author.username,
                            'gamer_tag': post.author.gamer_tag,
                            'rank': post.author.rank,
                        },
                        'game': post.game,
                        'rank': post.rank,
                        'region': post.region,
                        'play_style': post.play_style,
                        'message': post.message,
                    },
                    'match_score': float(match_score),
                    'similarity': float(similarity),
                })
            except:
                # Fallback: simple text matching
                match_score = 0.1
                if user_data['rank'] and post.rank:
                    if user_data['rank'].lower() in post.rank.lower() or post.rank.lower() in user_data['rank'].lower():
                        match_score += 0.3
                
                recommendations.append({
                    'post': {
                        'id': post.id,
                        'author': {
                            'id': post.author.id,
                            'username': post.author.username,
                            'gamer_tag': post.author.gamer_tag,
                            'rank': post.author.rank,
                        },
                        'game': post.game,
                        'rank': post.rank,
                        'region': post.region,
                        'play_style': post.play_style,
                        'message': post.message,
                    },
                    'match_score': match_score,
                    'similarity': match_score,
                })
        
        # Sort by match score (highest first)
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Return top 10 recommendations
        return Response({
            'recommendations': recommendations[:10],
            'count': len(recommendations[:10])
        })


class MatchInsightViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Match Insights (read-only)."""
    queryset = MatchInsight.objects.all()
    serializer_class = MatchInsightSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return insights for current user."""
        return MatchInsight.objects.filter(
            user=self.request.user
        ).select_related('tournament', 'user').order_by('-generated_at')
