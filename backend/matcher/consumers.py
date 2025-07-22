"""
WebSocket consumers for real-time notifications.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time notifications.
    Supports JWT token authentication via query parameters.
    """

    async def connect(self):
        """
        Handle WebSocket connection with JWT authentication.
        """
        # Try to authenticate user via JWT token
        self.user = await self.authenticate_user()
        
        if not self.user or self.user == AnonymousUser():
            logger.warning("WebSocket connection rejected: Authentication failed")
            await self.close(code=4001)  # Custom close code for auth failure
            return
        
        # Create user-specific group name
        self.user_group = f"user_{self.user.id}"
        
        # Create role-specific group names
        self.role_group = f"role_{self.user.user_type}"
        
        # Join user-specific group
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        
        # Join role-specific group (for broadcast notifications)
        await self.channel_layer.group_add(
            self.role_group,
            self.channel_name
        )
        
        logger.info(f"WebSocket connected for user {self.user.id} ({self.user.user_type})")
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'user_id': str(self.user.id),
            'user_type': self.user.user_type,
            'timestamp': self.get_current_timestamp()
        }))

    @database_sync_to_async
    def authenticate_user(self):
        """
        Authenticate user using JWT token from query parameters.
        """
        try:
            # Get token from query parameters
            query_string = self.scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
            
            if not token:
                # Fallback to session-based auth if no token provided
                return self.scope.get("user", AnonymousUser())
            
            # Validate JWT token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Get user from database
            user = User.objects.get(id=user_id)
            return user
            
        except (InvalidToken, TokenError, User.DoesNotExist) as e:
            logger.warning(f"JWT authentication failed: {e}")
            return AnonymousUser()
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return AnonymousUser()

    def get_current_timestamp(self):
        """
        Get current timestamp in ISO format.
        """
        from django.utils import timezone
        return timezone.now().isoformat()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        if hasattr(self, 'user_group'):
            # Leave user-specific group
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )
        
        if hasattr(self, 'role_group'):
            # Leave role-specific group
            await self.channel_layer.group_discard(
                self.role_group,
                self.channel_name
            )
        
        if hasattr(self, 'user'):
            logger.info(f"WebSocket disconnected for user {self.user.id} (code: {close_code})")

    async def receive(self, text_data):
        """
        Handle messages received from WebSocket.
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'ping')
            
            if message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp', self.get_current_timestamp())
                }))
            elif message_type == 'subscribe':
                # Handle subscription to specific notification types
                await self.handle_subscription(text_data_json)
            elif message_type == 'unsubscribe':
                # Handle unsubscription from specific notification types
                await self.handle_unsubscription(text_data_json)
            else:
                # Unknown message type
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}',
                    'timestamp': self.get_current_timestamp()
                }))
                
        except json.JSONDecodeError:
            # Invalid JSON received
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format',
                'timestamp': self.get_current_timestamp()
            }))
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error',
                'timestamp': self.get_current_timestamp()
            }))

    async def handle_subscription(self, data):
        """
        Handle subscription to specific notification types.
        """
        notification_types = data.get('notification_types', [])
        
        for notification_type in notification_types:
            if notification_type in ['job_posted', 'application_received', 'application_status_changed', 'match_score_calculated']:
                group_name = f"{notification_type}_{self.user.user_type}"
                await self.channel_layer.group_add(group_name, self.channel_name)
        
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'notification_types': notification_types,
            'timestamp': self.get_current_timestamp()
        }))

    async def handle_unsubscription(self, data):
        """
        Handle unsubscription from specific notification types.
        """
        notification_types = data.get('notification_types', [])
        
        for notification_type in notification_types:
            if notification_type in ['job_posted', 'application_received', 'application_status_changed', 'match_score_calculated']:
                group_name = f"{notification_type}_{self.user.user_type}"
                await self.channel_layer.group_discard(group_name, self.channel_name)
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'notification_types': notification_types,
            'timestamp': self.get_current_timestamp()
        }))

    async def notification_message(self, event):
        """
        Handle notification messages sent to the group.
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message'],
            'notification_type': event.get('notification_type', 'info'),
            'timestamp': event.get('timestamp', self.get_current_timestamp()),
            'data': event.get('data', {}),
            'priority': event.get('priority', 'normal')
        }))

    async def job_posted_notification(self, event):
        """
        Handle job posted notifications.
        """
        await self.send(text_data=json.dumps({
            'type': 'job_posted',
            'message': event['message'],
            'job_id': event.get('job_id'),
            'job_title': event.get('job_title'),
            'company': event.get('company'),
            'location': event.get('location'),
            'timestamp': event.get('timestamp', self.get_current_timestamp()),
            'data': event.get('data', {})
        }))

    async def application_received_notification(self, event):
        """
        Handle application received notifications.
        """
        await self.send(text_data=json.dumps({
            'type': 'application_received',
            'message': event['message'],
            'application_id': event.get('application_id'),
            'job_id': event.get('job_id'),
            'applicant_name': event.get('applicant_name'),
            'timestamp': event.get('timestamp', self.get_current_timestamp()),
            'data': event.get('data', {})
        }))

    async def application_status_changed_notification(self, event):
        """
        Handle application status change notifications.
        """
        await self.send(text_data=json.dumps({
            'type': 'application_status_changed',
            'message': event['message'],
            'application_id': event.get('application_id'),
            'old_status': event.get('old_status'),
            'new_status': event.get('new_status'),
            'job_title': event.get('job_title'),
            'timestamp': event.get('timestamp', self.get_current_timestamp()),
            'data': event.get('data', {})
        }))

    async def match_score_calculated_notification(self, event):
        """
        Handle match score calculation notifications.
        """
        await self.send(text_data=json.dumps({
            'type': 'match_score_calculated',
            'message': event['message'],
            'job_id': event.get('job_id'),
            'job_title': event.get('job_title'),
            'match_score': event.get('match_score'),
            'timestamp': event.get('timestamp', self.get_current_timestamp()),
            'data': event.get('data', {})
        }))