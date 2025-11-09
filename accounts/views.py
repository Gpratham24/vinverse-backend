"""
API views for user authentication and profile management.
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import models
from .models import CustomUser, Badge, UserBadge
from .serializers import UserRegistrationSerializer, UserProfileSerializer
from .badges import update_user_activity, check_badge_eligibility


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    """
    Register a new user and return JWT tokens.
    Endpoint: POST /api/auth/register/
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    """
    Authenticate user by email and return JWT tokens.
    Endpoint: POST /api/auth/login/
    Body: { "email": "...", "password": "..." }
    """
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find user by email
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Account does not exist. Please sign up first.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': f'Database error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Authenticate with username (Django's authenticate uses username)
        user = authenticate(username=user.username, password=password)
        
        if user:
            try:
                # Update user activity and streak
                update_user_activity(user)
                
                # Check and award badges
                eligible_badges = check_badge_eligibility(user)
                for badge_key in eligible_badges:
                    try:
                        badge = Badge.objects.get(key=badge_key)
                        UserBadge.objects.get_or_create(user=user, badge=badge)
                    except Badge.DoesNotExist:
                        pass  # Badge not defined yet
                
                refresh = RefreshToken.for_user(user)
                # Refresh user data after activity update
                user.refresh_from_db()
                serializer = UserProfileSerializer(user)
                return Response({
                    'user': serializer.data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                    'message': 'Login successful'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {'error': f'Token generation error: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            {'error': 'Invalid password. Please try again.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        return Response(
            {'error': f'Login error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
    """
    Check if username is available.
    Endpoint: GET /api/auth/check-username/?username=...
    Returns: { "available": true/false, "username": "..." }
    """
    username = request.query_params.get('username', '').strip()
    
    if not username:
        return Response(
            {'error': 'Username parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate username length
    if len(username) < 3:
        return Response({
            'available': False,
            'username': username,
            'message': 'Username must be at least 3 characters'
        }, status=status.HTTP_200_OK)
    
    # Check database for existing username (case-insensitive)
    exists = CustomUser.objects.filter(username__iexact=username).exists()
    
    return Response({
        'available': not exists,
        'username': username,
        'message': 'Username is available' if not exists else 'Username already taken'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_players(request):
    """
    Search for players by username, gamer_tag, or vin_id.
    Endpoint: GET /api/auth/search-players/?q=...
    Returns: { "players": [...], "count": N, "query": "..." }
    """
    query = request.query_params.get('q', '').strip()
    
    if not query:
        return Response({
            'players': [],
            'count': 0,
            'query': '',
            'message': 'Please enter a search query'
        }, status=status.HTTP_200_OK)
    
    if len(query) < 2:
        return Response({
            'players': [],
            'count': 0,
            'query': query,
            'message': 'Search query must be at least 2 characters'
        }, status=status.HTTP_200_OK)
    
    # Search in database: username, gamer_tag, vin_id (case-insensitive)
    # Return ALL matching users - show all players (users with VIN ID are considered players)
    # Only exclude users without VIN ID who are superuser (actual admin accounts, not players)
    players = CustomUser.objects.filter(
        models.Q(username__icontains=query) |
        models.Q(gamer_tag__icontains=query) |
        models.Q(vin_id__icontains=query)
    ).exclude(
        models.Q(is_superuser=True) & models.Q(vin_id__isnull=True)
    ).order_by('username')[:20]  # Limit to 20 results, exclude only admin accounts without VIN ID
    
    serializer = UserProfileSerializer(players, many=True)
    
    return Response({
        'players': serializer.data,
        'count': len(serializer.data),
        'query': query,
        'message': f'Found {len(serializer.data)} player(s)' if serializer.data else 'No players found'
    }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update user profile.
    Endpoints:
    - GET /api/auth/profile/ - Get current user profile
    - PUT /api/auth/profile/ - Update current user profile
    - GET /api/auth/profile/<user_id>/ - Get user profile by ID (public)
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Return the current authenticated user or user by ID."""
        user_id = self.kwargs.get('pk')
        if user_id:
            # Viewing another user's profile (public read access)
            from django.shortcuts import get_object_or_404
            return get_object_or_404(CustomUser, id=user_id)
        # Viewing own profile - update activity
        user = self.request.user
        if user.is_authenticated:
            update_user_activity(user)
            # Check and award badges
            eligible_badges = check_badge_eligibility(user)
            for badge_key in eligible_badges:
                try:
                    badge = Badge.objects.get(key=badge_key)
                    UserBadge.objects.get_or_create(user=user, badge=badge)
                except Badge.DoesNotExist:
                    pass
            user.refresh_from_db()
        return user
    
    def get_permissions(self):
        """Allow public read access for viewing other users' profiles."""
        if self.request.method == 'GET' and self.kwargs.get('pk'):
            # Public read access for viewing other users
            return [permissions.AllowAny()]
        # Authenticated access for own profile or updates
        return [permissions.IsAuthenticated()]
