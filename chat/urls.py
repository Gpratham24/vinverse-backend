"""
URL routes for Chat endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, MessageViewSet, RoomJoinRequestViewSet

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'join-requests', RoomJoinRequestViewSet, basename='join-request')

urlpatterns = [
    path('', include(router.urls)),
]

