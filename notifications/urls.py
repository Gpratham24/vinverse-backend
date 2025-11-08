"""
URL routes for Notifications endpoints.
"""
from django.urls import path
from .views import get_notifications, mark_read, mark_all_read

urlpatterns = [
    path('', get_notifications, name='notifications'),
    path('<int:notification_id>/read/', mark_read, name='mark-read'),
    path('mark-all-read/', mark_all_read, name='mark-all-read'),
]

