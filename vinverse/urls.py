"""
URL configuration for vinverse project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),  # Authentication endpoints
    path('api/tournaments/', include('tournaments.urls')),  # Tournament CRUD
    path('api/gamerlink/', include('gamerlink.urls')),  # GamerLink Phase 2 endpoints
    path('api/notifications/', include('notifications.urls')),  # Notifications
    path('api/chat/', include('chat.urls')),  # Chat API
    path('api/ai/', include('ai_engine.urls')),  # AI Engine
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

