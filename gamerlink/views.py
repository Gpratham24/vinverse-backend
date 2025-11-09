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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_matchmaking(request):
    """
    Smart matchmaking algorithm.
    Matches players based on: Elo rating, win rate, team synergy, region, game.
    POST /api/gamerlink/matchmaking/
    Body: { "game": "Valorant", "region": "NA", "team_size": 5 }
    """
    from tournaments.models import Tournament
    from ai_engine.tasks import calculate_win_rate, calculate_skill_consistency
    
    game = request.data.get('game')
    region = request.data.get('region', '')
    team_size = int(request.data.get('team_size', 5))
    user = request.user
    
    if not game:
        return Response(
            {'error': 'game is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get user's stats
    user_win_rate = calculate_win_rate(user, game)
    user_consistency = calculate_skill_consistency(user, game)
    
    # Calculate user's Elo-like score
    user_elo = (user_win_rate * 1000) + (user_consistency * 500) + (user.xp_points / 10)
    
    # Find potential teammates
    # Exclude users already in teams with user, and user themselves
    excluded_users = {user.id}
    user_teams = Team.objects.filter(members=user, game=game)
    for team in user_teams:
        excluded_users.update(team.members.values_list('id', flat=True))
    
    # Get LFT posts or active users for this game
    potential_teammates = CustomUser.objects.exclude(id__in=excluded_users).filter(
        joined_tournaments__tournament__game=game
    ).distinct()
    
    if region:
        # Filter by region if LFT posts have region info
        lft_with_region = LFTPost.objects.filter(
            game__icontains=game,
            region__icontains=region,
            is_active=True
        ).values_list('author_id', flat=True)
        potential_teammates = potential_teammates.filter(id__in=lft_with_region)
    
    matches = []
    for teammate in potential_teammates[:100]:  # Limit for performance
        teammate_win_rate = calculate_win_rate(teammate, game)
        teammate_consistency = calculate_skill_consistency(teammate, game)
        teammate_elo = (teammate_win_rate * 1000) + (teammate_consistency * 500) + (teammate.xp_points / 10)
        
        # Calculate match score
        elo_diff = abs(user_elo - teammate_elo)
        elo_score = max(0, 1 - (elo_diff / 2000))  # Closer Elo = higher score
        
        # Region match bonus (check LFT posts for region info)
        region_score = 0.1
        if region:
            teammate_lft = LFTPost.objects.filter(author=teammate, game__icontains=game, is_active=True).first()
            if teammate_lft and teammate_lft.region and region.lower() in teammate_lft.region.lower():
                region_score = 0.3
        
        # Team synergy (if they've been in tournaments together)
        synergy_score = 0
        user_tournament_ids = Tournament.objects.filter(
            participants__user=user,
            game=game
        ).values_list('id', flat=True)
        common_tournaments = Tournament.objects.filter(
            id__in=user_tournament_ids,
            participants__user=teammate,
            game=game
        ).count()
        if common_tournaments > 0:
            synergy_score = min(0.3, common_tournaments * 0.1)
        
        # Rank similarity
        rank_score = 0.1
        if user.rank and teammate.rank:
            if user.rank.lower() == teammate.rank.lower():
                rank_score = 0.2
        
        total_score = (elo_score * 0.4 + region_score * 0.2 + synergy_score * 0.3 + rank_score * 0.1)
        
        # Get teammate region from LFT post if available
        teammate_lft_for_region = LFTPost.objects.filter(author=teammate, game__icontains=game, is_active=True).first()
        teammate_region = teammate_lft_for_region.region if teammate_lft_for_region else ''
        
        matches.append({
            'user': {
                'id': teammate.id,
                'username': teammate.username,
                'gamer_tag': teammate.gamer_tag,
                'rank': teammate.rank,
                'region': teammate_region,
            },
            'match_score': round(total_score * 100, 2),
            'elo_score': round(elo_score * 100, 2),
            'region_match': region_score > 0.1,
            'synergy': common_tournaments,
            'win_rate': round(teammate_win_rate * 100, 2),
            'consistency': round(teammate_consistency * 100, 2),
        })
    
    # Sort by match score
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return Response({
        'matches': matches[:team_size * 2],  # Return 2x team size for options
        'user_stats': {
            'elo': round(user_elo, 2),
            'win_rate': round(user_win_rate * 100, 2),
            'consistency': round(user_consistency * 100, 2),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard(request):
    """
    Get leaderboard with rankings.
    GET /api/gamerlink/leaderboard/?game=Valorant&type=overall|tournaments|xp
    """
    from django.db.models import F, Count
    
    leaderboard_type = request.query_params.get('type', 'overall')
    game = request.query_params.get('game', None)
    limit = int(request.query_params.get('limit', 100))
    
    if leaderboard_type == 'xp':
        # XP-based leaderboard
        queryset = CustomUser.objects.all().order_by('-xp_points')
    elif leaderboard_type == 'tournaments':
        # Tournament participation leaderboard
        from tournaments.models import TournamentParticipant
        queryset = CustomUser.objects.annotate(
            tournament_count=Count('joined_tournaments')
        ).order_by('-tournament_count')
    else:
        # Overall (combined score)
        from tournaments.models import TournamentParticipant
        queryset = CustomUser.objects.annotate(
            tournament_count=Count('joined_tournaments'),
            combined_score=F('xp_points') + (F('tournament_count') * 100)
        ).order_by('-combined_score')
    
    # Filter by game if specified
    if game:
        queryset = queryset.filter(
            joined_tournaments__tournament__game=game
        ).distinct()
    
    # Get top users
    top_users = list(queryset[:limit])
    
    leaderboard_data = []
    for idx, user in enumerate(top_users, start=1):
        from ai_engine.tasks import calculate_win_rate, calculate_skill_consistency
        win_rate = calculate_win_rate(user, game) if game else calculate_win_rate(user)
        
        # Determine tier/badge
        tier = 'Bronze'
        if user.xp_points >= 10000:
            tier = 'Challenger'
        elif user.xp_points >= 7500:
            tier = 'Grandmaster'
        elif user.xp_points >= 5000:
            tier = 'Master'
        elif user.xp_points >= 3000:
            tier = 'Diamond'
        elif user.xp_points >= 2000:
            tier = 'Platinum'
        elif user.xp_points >= 1000:
            tier = 'Gold'
        elif user.xp_points >= 500:
            tier = 'Silver'
        
        leaderboard_data.append({
            'rank': idx,
            'user': {
                'id': user.id,
                'username': user.username,
                'gamer_tag': user.gamer_tag,
                'rank': user.rank,
                'xp_points': user.xp_points,
            },
            'tier': tier,
            'win_rate': round(win_rate * 100, 2),
            'tournaments': getattr(user, 'tournament_count', 0),
            'score': getattr(user, 'combined_score', user.xp_points),
        })
    
    return Response({
        'leaderboard': leaderboard_data,
        'type': leaderboard_type,
        'game': game,
    })
