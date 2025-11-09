"""
ASGI config for vinverse project.
Supports both HTTP and WebSocket connections.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vinverse.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import routing after Django is initialized
from chat.routing import websocket_urlpatterns

# Try to use JWT auth middleware, fallback to session auth
try:
    from chat.middleware import JWTAuthMiddlewareStack
    websocket_auth = JWTAuthMiddlewareStack
except ImportError:
    # Fallback to session-based auth
    websocket_auth = AuthMiddlewareStack

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,
    
    # WebSocket handler
    "websocket": websocket_auth(
        URLRouter(websocket_urlpatterns)
    ),
})
