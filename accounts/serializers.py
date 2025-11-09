"""
Serializers for user authentication and profile management.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Badge, UserBadge


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Validates password and creates new user.
    Simplified fields: username, email, password, gamer_tag
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password")
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2', 'gamer_tag')
        extra_kwargs = {
            'gamer_tag': {'required': True},  # Game ID is required
        }
    
    def validate_username(self, value):
        """Check if username is unique."""
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate_email(self, value):
        """Check if email is unique."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """Create and return a new user instance."""
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user


class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for badge information."""
    class Meta:
        model = Badge
        fields = ('id', 'key', 'name', 'description', 'icon', 'badge_type', 'color')


class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer for user badges with badge details."""
    badge = BadgeSerializer(read_only=True)
    
    class Meta:
        model = UserBadge
        fields = ('id', 'badge', 'earned_at')


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile (read/write user data).
    """
    verified = serializers.BooleanField(read_only=True)  # Only admins can update via admin panel
    badges = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'bio', 'rank', 'gamer_tag', 'verified', 'vin_id', 'xp_points', 'is_online', 'last_seen', 'date_joined', 'streak_days', 'last_active_date', 'badges')
        read_only_fields = ('id', 'username', 'date_joined', 'vin_id', 'verified', 'xp_points', 'is_online', 'last_seen', 'streak_days', 'last_active_date', 'badges')
    
    def get_badges(self, obj):
        """Get user's earned badges."""
        user_badges = UserBadge.objects.filter(user=obj).select_related('badge')
        return UserBadgeSerializer(user_badges, many=True).data

