"""
URL routes for AI Engine endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatchInsightViewSet

router = DefaultRouter()
router.register(r'insights', MatchInsightViewSet, basename='insight')

urlpatterns = [
    path('', include(router.urls)),
]

