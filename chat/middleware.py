"""
Custom WebSocket authentication middleware for JWT tokens.
"""
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings

User = get_user_model()

try:
    from jwt import decode as jwt_decode
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


@database_sync_to_async
def get_user_from_token(token_string):
    """Get user from JWT token."""
    if not JWT_AVAILABLE:
        return AnonymousUser()
    
    try:
        # Validate token
        UntypedToken(token_string)
    except (InvalidToken, TokenError):
        return AnonymousUser()
    
    try:
        # Decode token
        decoded_data = jwt_decode(token_string, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_data.get('user_id')
        
        if user_id:
            return User.objects.get(id=user_id)
    except (User.DoesNotExist, Exception):
        pass
    
    return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    Token can be passed as query parameter: ?token=xxx
    """
    
    async def __call__(self, scope, receive, send):
        # Get token from query string
        query_string = scope.get('query_string', b'').decode()
        token = None
        
        # Parse query string
        if query_string:
            try:
                # Handle URL-encoded query string
                from urllib.parse import parse_qs, unquote
                params = parse_qs(query_string)
                if 'token' in params:
                    token = params['token'][0]
            except Exception:
                # Fallback to simple parsing
                params = {}
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[unquote(key)] = unquote(value)
                token = params.get('token')
        
        # If no token in query, try to get from headers (for cookie-based auth)
        if not token:
            headers = dict(scope.get('headers', []))
            # Try to get from cookie
            cookie_header = headers.get(b'cookie', b'').decode()
            if cookie_header:
                # Extract token from cookie if present
                for cookie in cookie_header.split(';'):
                    if 'access_token' in cookie:
                        token = cookie.split('=')[1].strip()
        
        # Authenticate user
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """Stack JWT auth middleware."""
    return JWTAuthMiddleware(inner)

