"""
URL routes for GamerLink endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    follow_user, user_feed, user_connections,
    PostViewSet, TeamViewSet, LFTPostViewSet, MatchInsightViewSet,
    smart_matchmaking, leaderboard
)

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'lft', LFTPostViewSet, basename='lft')
router.register(r'insights', MatchInsightViewSet, basename='insight')

urlpatterns = [
    path('follow/<int:user_id>/', follow_user, name='follow-user'),
    path('feed/', user_feed, name='user-feed'),
    path('connections/<int:user_id>/', user_connections, name='user-connections'),
    path('matchmaking/', smart_matchmaking, name='smart-matchmaking'),
    path('leaderboard/', leaderboard, name='leaderboard'),
    path('', include(router.urls)),
]
