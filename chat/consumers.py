"""
WebSocket consumers for real-time chat.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Room, Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for chat rooms."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        try:
            user = self.scope.get('user')
            
            # Check if user is authenticated
            if not user or not user.is_authenticated:
                print(f"WebSocket connection rejected: User not authenticated. User: {user}")
                await self.close(code=4001)  # Unauthorized
                return
            
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'chat_{self.room_name}'
            
            # Check room access
            room = await self.get_room(self.room_name)
            if not room:
                print(f"WebSocket connection rejected: Room '{self.room_name}' not found")
                await self.close(code=4004)  # Room not found
                return
            
            # Check if user can access private room
            if room.is_private:
                has_access = await self.check_room_access(room, user)
                if not has_access:
                    print(f"WebSocket connection rejected: User {user.username} doesn't have access to private room '{self.room_name}'")
                    await self.close(code=4003)  # Forbidden
                    return
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            print(f"WebSocket connected: User {user.username} joined room '{self.room_name}'")
            
            # Send room history
            await self.send_room_history()
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            await self.close(code=4000)  # Internal error
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            message_content = data.get('message', '').strip()
            user = self.scope['user']
            
            if message_content and user.is_authenticated:
                # Save message to database
                room = await self.get_room(self.room_name)
                if room:
                    message = await self.save_message(room, user, message_content)
                    
                    # Send message to room group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': message_content,
                            'username': user.username,
                            'user_id': user.id,
                            'timestamp': message.created_at.isoformat() if message else None,
                            'message_id': message.id if message else None,
                        }
                    )
    
    async def chat_message(self, event):
        """Receive message from room group."""
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
            'message_id': event.get('message_id'),
        }))
    
    async def send_room_history(self):
        """Send recent messages when user joins."""
        room = await self.get_room(self.room_name)
        if room:
            messages = await self.get_recent_messages(room, limit=50)
            await self.send(text_data=json.dumps({
                'type': 'history',
                'messages': messages,
            }))
    
    @database_sync_to_async
    def get_room(self, room_name):
        """Get or create room."""
        try:
            return Room.objects.get(name=room_name, is_active=True)
        except Room.DoesNotExist:
            # Create default global room if it doesn't exist
            if room_name == 'lobby':
                return Room.objects.create(
                    name='lobby',
                    display_name='Global Lobby',
                    room_type='global',
                    description='Main chat room for all users'
                )
            return None
    
    @database_sync_to_async
    def save_message(self, room, user, content):
        """Save message to database."""
        return Message.objects.create(
            room=room,
            author=user,
            content=content
        )
    
    @database_sync_to_async
    def check_room_access(self, room, user):
        """Check if user has access to private room."""
        if not room.is_private:
            return True
        return room.members.filter(id=user.id).exists() or room.created_by == user
    
    @database_sync_to_async
    def get_recent_messages(self, room, limit=50):
        """Get recent messages from room."""
        messages = Message.objects.filter(room=room).select_related('author').order_by('-created_at')[:limit]
        return [
            {
                'id': msg.id,
                'content': msg.content,
                'message': msg.content,  # Also include as 'message' for compatibility
                'username': msg.author.username,
                'user_id': msg.author.id,
                'timestamp': msg.created_at.isoformat(),
            }
            for msg in reversed(messages)  # Reverse to show oldest first
        ]

