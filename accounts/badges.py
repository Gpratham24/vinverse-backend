"""
Badge definitions and badge earning logic.
"""
from django.utils import timezone
from datetime import timedelta, date


# Badge definitions
BADGES = {
    'first_login': {
        'name': 'First Steps',
        'description': 'Welcome to VinVerse!',
        'icon': '🎯',
        'color': 'blue',
    },
    'streak_7': {
        'name': 'Week Warrior',
        'description': '7 day login streak',
        'icon': '🔥',
        'color': 'orange',
    },
    'streak_30': {
        'name': 'Monthly Master',
        'description': '30 day login streak',
        'icon': '⭐',
        'color': 'gold',
    },
    'streak_100': {
        'name': 'Century Champion',
        'description': '100 day login streak',
        'icon': '👑',
        'color': 'purple',
    },
    'first_tournament': {
        'name': 'Tournament Rookie',
        'description': 'Joined your first tournament',
        'icon': '🏆',
        'color': 'yellow',
    },
    'first_win': {
        'name': 'First Victory',
        'description': 'Won your first tournament',
        'icon': '🎉',
        'color': 'green',
    },
    'social_butterfly': {
        'name': 'Social Butterfly',
        'description': 'Reached 100 followers',
        'icon': '🦋',
        'color': 'pink',
    },
}


def calculate_streak(user):
    """
    Calculate user's current login streak based on last_active_date.
    Returns the streak count in days.
    """
    if not user.last_active_date:
        return 0
    
    today = date.today()
    last_active = user.last_active_date
    
    # If last active was today, streak continues
    if last_active == today:
        return user.streak_days
    
    # If last active was yesterday, increment streak
    if last_active == today - timedelta(days=1):
        return user.streak_days + 1
    
    # If last active was more than 1 day ago, reset streak
    if last_active < today - timedelta(days=1):
        return 1  # Start new streak
    
    return user.streak_days


def update_user_activity(user):
    """
    Update user's activity and streak when they log in or perform actions.
    Should be called whenever user is active.
    """
    today = date.today()
    
    if not user.last_active_date:
        # First time active
        user.last_active_date = today
        user.streak_days = 1
    elif user.last_active_date == today:
        # Already active today, no change
        pass
    elif user.last_active_date == today - timedelta(days=1):
        # Consecutive day, increment streak
        user.streak_days += 1
        user.last_active_date = today
    else:
        # Streak broken, start new streak
        user.streak_days = 1
        user.last_active_date = today
    
    user.save(update_fields=['streak_days', 'last_active_date'])


def check_badge_eligibility(user):
    """
    Check if user is eligible for any badges based on their stats.
    Returns list of badge keys user should earn.
    """
    earned_badges = []
    
    # Check streak badges
    if user.streak_days >= 100:
        earned_badges.append('streak_100')
    elif user.streak_days >= 30:
        earned_badges.append('streak_30')
    elif user.streak_days >= 7:
        earned_badges.append('streak_7')
    
    # First login badge (if streak is 1 and just started)
    if user.streak_days == 1 and user.last_active_date == date.today():
        earned_badges.append('first_login')
    
    return earned_badges

