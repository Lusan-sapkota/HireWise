"""
WebSocket consumers for real-time notifications, messaging, and updates.
"""

import json
import logging
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.utils import timezone
from .middleware import websocket_connection_manager

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
        # Get user from scope (set by JWTAuthMiddleware)
        self.user = self.scope.get("user", AnonymousUser())
        
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
        
        # Register connection with connection manager
        await self.register_connection()
        
        logger.info(f"Notification WebSocket connected for user {self.user.id} ({self.user.user_type})")
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'user_id': str(self.user.id),
            'user_type': self.user.user_type,
            'timestamp': self.get_current_timestamp()
        }))

    async def register_connection(self):
        """
        Register this connection with the connection manager.
        """
        connection_info = {
            'consumer_type': 'notification',
            'user_type': self.user.user_type,
            'groups': [self.user_group, self.role_group]
        }
        
        # Use database_sync_to_async to call the sync method
        await database_sync_to_async(websocket_connection_manager.add_connection)(
            str(self.user.id), 
            self.channel_name, 
            connection_info
        )

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
        
        # Unregister connection from connection manager
        if hasattr(self, 'user') and self.user != AnonymousUser():
            await database_sync_to_async(websocket_connection_manager.remove_connection)(
                str(self.user.id), 
                self.channel_name
            )
            logger.info(f"Notification WebSocket disconnected for user {self.user.id} (code: {close_code})")

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

class MessageConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time messaging between users.
    """

    async def connect(self):
        """
        Handle WebSocket connection for messaging.
        """
        # Get user from scope (set by JWTAuthMiddleware)
        self.user = self.scope.get("user", AnonymousUser())
        
        if not self.user or self.user == AnonymousUser():
            logger.warning("Message WebSocket connection rejected: Authentication failed")
            await self.close(code=4001)
            return
        
        # Create user-specific group for receiving messages
        self.user_group = f"messages_user_{self.user.id}"
        
        # Join user-specific group
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        
        # Register connection
        await self.register_connection()
        
        logger.info(f"Message WebSocket connected for user {self.user.id}")
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'user_id': str(self.user.id),
            'timestamp': timezone.now().isoformat()
        }))

    async def register_connection(self):
        """
        Register this connection with the connection manager.
        """
        connection_info = {
            'consumer_type': 'message',
            'user_type': self.user.user_type,
            'groups': [self.user_group]
        }
        
        await database_sync_to_async(websocket_connection_manager.add_connection)(
            str(self.user.id), 
            self.channel_name, 
            connection_info
        )

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )
        
        # Unregister connection
        if hasattr(self, 'user') and self.user != AnonymousUser():
            await database_sync_to_async(websocket_connection_manager.remove_connection)(
                str(self.user.id), 
                self.channel_name
            )
            logger.info(f"Message WebSocket disconnected for user {self.user.id} (code: {close_code})")

    async def receive(self, text_data):
        """
        Handle messages received from WebSocket.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'ping')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'send_message':
                await self.handle_send_message(data)
            elif message_type == 'typing_start':
                await self.handle_typing_indicator(data, True)
            elif message_type == 'typing_stop':
                await self.handle_typing_indicator(data, False)
            elif message_type == 'mark_read':
                await self.handle_mark_read(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}',
                    'timestamp': timezone.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format',
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error handling message WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error',
                'timestamp': timezone.now().isoformat()
            }))

    async def handle_send_message(self, data):
        """
        Handle sending a message to another user.
        """
        try:
            conversation_id = data.get('conversation_id')
            content = data.get('content', '').strip()
            message_type = data.get('message_type', 'text')
            
            if not conversation_id or not content:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Missing conversation_id or content',
                    'timestamp': timezone.now().isoformat()
                }))
                return
            
            # Create message in database
            message = await self.create_message(conversation_id, content, message_type)
            
            if message:
                # Get conversation participants
                participants = await self.get_conversation_participants(conversation_id)
                
                # Send message to all participants
                for participant_id in participants:
                    await self.channel_layer.group_send(
                        f"messages_user_{participant_id}",
                        {
                            'type': 'message_received',
                            'message_id': str(message['id']),
                            'conversation_id': conversation_id,
                            'sender_id': str(self.user.id),
                            'sender_name': message['sender_name'],
                            'content': content,
                            'message_type': message_type,
                            'timestamp': message['timestamp'],
                            'is_read': participant_id == str(self.user.id)
                        }
                    )
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to send message',
                'timestamp': timezone.now().isoformat()
            }))

    async def handle_typing_indicator(self, data, is_typing):
        """
        Handle typing indicators.
        """
        try:
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                return
            
            # Get conversation participants
            participants = await self.get_conversation_participants(conversation_id)
            
            # Send typing indicator to other participants
            for participant_id in participants:
                if participant_id != str(self.user.id):
                    await self.channel_layer.group_send(
                        f"messages_user_{participant_id}",
                        {
                            'type': 'typing_indicator',
                            'conversation_id': conversation_id,
                            'user_id': str(self.user.id),
                            'user_name': f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username,
                            'is_typing': is_typing,
                            'timestamp': timezone.now().isoformat()
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error handling typing indicator: {e}")

    async def handle_mark_read(self, data):
        """
        Handle marking messages as read.
        """
        try:
            message_ids = data.get('message_ids', [])
            if not message_ids:
                return
            
            # Mark messages as read in database
            await self.mark_messages_read(message_ids)
            
            # Send read receipt to sender
            for message_id in message_ids:
                message_info = await self.get_message_info(message_id)
                if message_info and message_info['sender_id'] != str(self.user.id):
                    await self.channel_layer.group_send(
                        f"messages_user_{message_info['sender_id']}",
                        {
                            'type': 'message_read_receipt',
                            'message_id': message_id,
                            'reader_id': str(self.user.id),
                            'reader_name': f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username,
                            'timestamp': timezone.now().isoformat()
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")

    @database_sync_to_async
    def create_message(self, conversation_id, content, message_type):
        """
        Create a new message in the database.
        """
        try:
            from .models import Conversation, Message
            
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Check if user is participant in conversation
            if not conversation.participants.filter(id=self.user.id).exists():
                return None
            
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content,
                message_type=message_type
            )
            
            return {
                'id': message.id,
                'sender_name': f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username,
                'timestamp': message.sent_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None

    @database_sync_to_async
    def get_conversation_participants(self, conversation_id):
        """
        Get list of participant IDs for a conversation.
        """
        try:
            from .models import Conversation
            
            conversation = Conversation.objects.get(id=conversation_id)
            return list(conversation.participants.values_list('id', flat=True))
            
        except Exception as e:
            logger.error(f"Error getting conversation participants: {e}")
            return []

    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """
        Mark messages as read for the current user.
        """
        try:
            from .models import Message
            
            Message.objects.filter(
                id__in=message_ids,
                conversation__participants=self.user
            ).exclude(sender=self.user).update(is_read=True)
            
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")

    @database_sync_to_async
    def get_message_info(self, message_id):
        """
        Get message information.
        """
        try:
            from .models import Message
            
            message = Message.objects.select_related('sender').get(id=message_id)
            return {
                'sender_id': str(message.sender.id),
                'conversation_id': str(message.conversation.id)
            }
            
        except Exception as e:
            logger.error(f"Error getting message info: {e}")
            return None

    # Event handlers for receiving messages from channel layer
    async def message_received(self, event):
        """
        Handle message received event.
        """
        await self.send(text_data=json.dumps({
            'type': 'message_received',
            'message_id': event['message_id'],
            'conversation_id': event['conversation_id'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'content': event['content'],
            'message_type': event['message_type'],
            'timestamp': event['timestamp'],
            'is_read': event['is_read']
        }))

    async def typing_indicator(self, event):
        """
        Handle typing indicator event.
        """
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'conversation_id': event['conversation_id'],
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'is_typing': event['is_typing'],
            'timestamp': event['timestamp']
        }))

    async def message_read_receipt(self, event):
        """
        Handle message read receipt event.
        """
        await self.send(text_data=json.dumps({
            'type': 'message_read_receipt',
            'message_id': event['message_id'],
            'reader_id': event['reader_id'],
            'reader_name': event['reader_name'],
            'timestamp': event['timestamp']
        }))


class UpdateConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling general updates like job matches, application status changes, etc.
    """

    async def connect(self):
        """
        Handle WebSocket connection for updates.
        """
        # Get user from scope (set by JWTAuthMiddleware)
        self.user = self.scope.get("user", AnonymousUser())
        
        if not self.user or self.user == AnonymousUser():
            logger.warning("Update WebSocket connection rejected: Authentication failed")
            await self.close(code=4001)
            return
        
        # Create user-specific group
        self.user_group = f"updates_user_{self.user.id}"
        
        # Create role-specific group
        self.role_group = f"updates_role_{self.user.user_type}"
        
        # Join groups
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.channel_layer.group_add(self.role_group, self.channel_name)
        
        # Register connection
        await self.register_connection()
        
        logger.info(f"Update WebSocket connected for user {self.user.id}")
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'user_id': str(self.user.id),
            'timestamp': timezone.now().isoformat()
        }))

    async def register_connection(self):
        """
        Register this connection with the connection manager.
        """
        connection_info = {
            'consumer_type': 'update',
            'user_type': self.user.user_type,
            'groups': [self.user_group, self.role_group]
        }
        
        await database_sync_to_async(websocket_connection_manager.add_connection)(
            str(self.user.id), 
            self.channel_name, 
            connection_info
        )

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        
        if hasattr(self, 'role_group'):
            await self.channel_layer.group_discard(self.role_group, self.channel_name)
        
        # Unregister connection
        if hasattr(self, 'user') and self.user != AnonymousUser():
            await database_sync_to_async(websocket_connection_manager.remove_connection)(
                str(self.user.id), 
                self.channel_name
            )
            logger.info(f"Update WebSocket disconnected for user {self.user.id} (code: {close_code})")

    async def receive(self, text_data):
        """
        Handle messages received from WebSocket.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'ping')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'subscribe_updates':
                await self.handle_subscribe_updates(data)
            elif message_type == 'unsubscribe_updates':
                await self.handle_unsubscribe_updates(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}',
                    'timestamp': timezone.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format',
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error handling update WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error',
                'timestamp': timezone.now().isoformat()
            }))

    async def handle_subscribe_updates(self, data):
        """
        Handle subscription to specific update types.
        """
        update_types = data.get('update_types', [])
        
        for update_type in update_types:
            if update_type in ['job_matches', 'application_updates', 'profile_views', 'system_updates']:
                group_name = f"updates_{update_type}_{self.user.user_type}"
                await self.channel_layer.group_add(group_name, self.channel_name)
        
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'update_types': update_types,
            'timestamp': timezone.now().isoformat()
        }))

    async def handle_unsubscribe_updates(self, data):
        """
        Handle unsubscription from specific update types.
        """
        update_types = data.get('update_types', [])
        
        for update_type in update_types:
            if update_type in ['job_matches', 'application_updates', 'profile_views', 'system_updates']:
                group_name = f"updates_{update_type}_{self.user.user_type}"
                await self.channel_layer.group_discard(group_name, self.channel_name)
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'update_types': update_types,
            'timestamp': timezone.now().isoformat()
        }))

    # Event handlers
    async def job_match_update(self, event):
        """
        Handle job match updates.
        """
        await self.send(text_data=json.dumps({
            'type': 'job_match_update',
            'job_id': event.get('job_id'),
            'job_title': event.get('job_title'),
            'match_score': event.get('match_score'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
            'data': event.get('data', {})
        }))

    async def application_status_update(self, event):
        """
        Handle application status updates.
        """
        await self.send(text_data=json.dumps({
            'type': 'application_status_update',
            'application_id': event.get('application_id'),
            'job_title': event.get('job_title'),
            'old_status': event.get('old_status'),
            'new_status': event.get('new_status'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
            'data': event.get('data', {})
        }))

    async def profile_view_update(self, event):
        """
        Handle profile view updates.
        """
        await self.send(text_data=json.dumps({
            'type': 'profile_view_update',
            'viewer_name': event.get('viewer_name'),
            'viewer_company': event.get('viewer_company'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
            'data': event.get('data', {})
        }))

    async def system_update(self, event):
        """
        Handle system updates.
        """
        await self.send(text_data=json.dumps({
            'type': 'system_update',
            'update_type': event.get('update_type'),
            'message': event.get('message'),
            'priority': event.get('priority', 'normal'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
            'data': event.get('data', {})
        }))


class InterviewConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling AI interview sessions.
    """

    async def connect(self):
        """
        Handle WebSocket connection for interview sessions.
        """
        # Get user from scope (set by JWTAuthMiddleware)
        self.user = self.scope.get("user", AnonymousUser())
        
        if not self.user or self.user == AnonymousUser():
            logger.warning("Interview WebSocket connection rejected: Authentication failed")
            await self.close(code=4001)
            return
        
        # Get session ID from URL
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        
        # Verify user has access to this interview session
        if not await self.verify_session_access():
            logger.warning(f"User {self.user.id} denied access to interview session {self.session_id}")
            await self.close(code=4003)  # Forbidden
            return
        
        # Create session-specific group
        self.session_group = f"interview_session_{self.session_id}"
        
        # Join session group
        await self.channel_layer.group_add(self.session_group, self.channel_name)
        
        # Register connection
        await self.register_connection()
        
        logger.info(f"Interview WebSocket connected for user {self.user.id}, session {self.session_id}")
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'user_id': str(self.user.id),
            'session_id': self.session_id,
            'timestamp': timezone.now().isoformat()
        }))

    async def register_connection(self):
        """
        Register this connection with the connection manager.
        """
        connection_info = {
            'consumer_type': 'interview',
            'user_type': self.user.user_type,
            'session_id': self.session_id,
            'groups': [self.session_group]
        }
        
        await database_sync_to_async(websocket_connection_manager.add_connection)(
            str(self.user.id), 
            self.channel_name, 
            connection_info
        )

    @database_sync_to_async
    def verify_session_access(self):
        """
        Verify that the user has access to this interview session.
        """
        try:
            from .models import InterviewSession
            
            session = InterviewSession.objects.select_related('application__job_seeker', 'application__job_post__recruiter').get(id=self.session_id)
            
            # Check if user is the job seeker or recruiter for this session
            if (session.application.job_seeker.id == self.user.id or 
                session.application.job_post.recruiter.id == self.user.id):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying session access: {e}")
            return False

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        if hasattr(self, 'session_group'):
            await self.channel_layer.group_discard(self.session_group, self.channel_name)
        
        # Unregister connection
        if hasattr(self, 'user') and self.user != AnonymousUser():
            await database_sync_to_async(websocket_connection_manager.remove_connection)(
                str(self.user.id), 
                self.channel_name
            )
            logger.info(f"Interview WebSocket disconnected for user {self.user.id} (code: {close_code})")

    async def receive(self, text_data):
        """
        Handle messages received from WebSocket.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'ping')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'interview_response':
                await self.handle_interview_response(data)
            elif message_type == 'request_next_question':
                await self.handle_next_question_request(data)
            elif message_type == 'end_interview':
                await self.handle_end_interview(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}',
                    'timestamp': timezone.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format',
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error handling interview WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error',
                'timestamp': timezone.now().isoformat()
            }))

    async def handle_interview_response(self, data):
        """
        Handle interview response from candidate.
        """
        try:
            question_id = data.get('question_id')
            response_text = data.get('response', '').strip()
            response_type = data.get('response_type', 'text')
            
            if not question_id or not response_text:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Missing question_id or response',
                    'timestamp': timezone.now().isoformat()
                }))
                return
            
            # Save response and get analysis
            analysis = await self.save_interview_response(question_id, response_text, response_type)
            
            # Send response confirmation and analysis
            await self.send(text_data=json.dumps({
                'type': 'response_received',
                'question_id': question_id,
                'analysis': analysis,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling interview response: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to process response',
                'timestamp': timezone.now().isoformat()
            }))

    async def handle_next_question_request(self, data):
        """
        Handle request for next interview question.
        """
        try:
            next_question = await self.get_next_question()
            
            if next_question:
                await self.send(text_data=json.dumps({
                    'type': 'next_question',
                    'question': next_question,
                    'timestamp': timezone.now().isoformat()
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'interview_complete',
                    'message': 'No more questions available',
                    'timestamp': timezone.now().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"Error getting next question: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to get next question',
                'timestamp': timezone.now().isoformat()
            }))

    async def handle_end_interview(self, data):
        """
        Handle interview session end.
        """
        try:
            final_analysis = await self.finalize_interview_session()
            
            # Broadcast to all session participants
            await self.channel_layer.group_send(
                self.session_group,
                {
                    'type': 'interview_ended',
                    'final_analysis': final_analysis,
                    'ended_by': str(self.user.id),
                    'timestamp': timezone.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error ending interview: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to end interview',
                'timestamp': timezone.now().isoformat()
            }))

    @database_sync_to_async
    def save_interview_response(self, question_id, response_text, response_type):
        """
        Save interview response and get AI analysis.
        """
        try:
            from .models import InterviewQuestion, InterviewResponse
            from .ml_services import analyze_interview_response
            
            question = InterviewQuestion.objects.get(id=question_id)
            
            # Create response record
            response = InterviewResponse.objects.create(
                question=question,
                response_text=response_text,
                response_type=response_type,
                respondent=self.user
            )
            
            # Get AI analysis
            analysis = analyze_interview_response(question.question_text, response_text)
            
            # Update response with analysis
            response.analysis_result = analysis
            response.save()
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error saving interview response: {e}")
            return {'error': 'Failed to analyze response'}

    @database_sync_to_async
    def get_next_question(self):
        """
        Get the next interview question for the session.
        """
        try:
            from .models import InterviewSession, InterviewQuestion
            
            session = InterviewSession.objects.get(id=self.session_id)
            
            # Get questions that haven't been answered yet
            answered_questions = session.responses.values_list('question_id', flat=True)
            next_question = session.questions.exclude(id__in=answered_questions).first()
            
            if next_question:
                return {
                    'id': str(next_question.id),
                    'question_text': next_question.question_text,
                    'question_type': next_question.question_type,
                    'expected_duration': next_question.expected_duration_minutes
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting next question: {e}")
            return None

    @database_sync_to_async
    def finalize_interview_session(self):
        """
        Finalize the interview session and generate final analysis.
        """
        try:
            from .models import InterviewSession
            from .ml_services import generate_interview_analysis
            
            session = InterviewSession.objects.get(id=self.session_id)
            
            # Generate final analysis
            final_analysis = generate_interview_analysis(session)
            
            # Update session status
            session.status = 'completed'
            session.completed_at = timezone.now()
            session.final_analysis = final_analysis
            session.save()
            
            return final_analysis
            
        except Exception as e:
            logger.error(f"Error finalizing interview session: {e}")
            return {'error': 'Failed to generate final analysis'}

    # Event handlers
    async def interview_ended(self, event):
        """
        Handle interview ended event.
        """
        await self.send(text_data=json.dumps({
            'type': 'interview_ended',
            'final_analysis': event['final_analysis'],
            'ended_by': event['ended_by'],
            'timestamp': event['timestamp']
        }))

    async def question_update(self, event):
        """
        Handle question update event.
        """
        await self.send(text_data=json.dumps({
            'type': 'question_update',
            'question': event['question'],
            'timestamp': event['timestamp']
        }))


class AdminConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for admin-specific real-time updates.
    """

    async def connect(self):
        """
        Handle WebSocket connection for admin users.
        """
        # Get user from scope (set by JWTAuthMiddleware)
        self.user = self.scope.get("user", AnonymousUser())
        
        if not self.user or self.user == AnonymousUser():
            logger.warning("Admin WebSocket connection rejected: Authentication failed")
            await self.close(code=4001)
            return
        
        # Check if user is admin
        if not self.user.is_staff and not self.user.is_superuser:
            logger.warning(f"Non-admin user {self.user.id} attempted to connect to admin WebSocket")
            await self.close(code=4003)  # Forbidden
            return
        
        # Create admin group
        self.admin_group = "admin_updates"
        
        # Join admin group
        await self.channel_layer.group_add(self.admin_group, self.channel_name)
        
        # Register connection
        await self.register_connection()
        
        logger.info(f"Admin WebSocket connected for user {self.user.id}")
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'user_id': str(self.user.id),
            'admin_level': 'superuser' if self.user.is_superuser else 'staff',
            'timestamp': timezone.now().isoformat()
        }))

    async def register_connection(self):
        """
        Register this connection with the connection manager.
        """
        connection_info = {
            'consumer_type': 'admin',
            'user_type': self.user.user_type,
            'admin_level': 'superuser' if self.user.is_superuser else 'staff',
            'groups': [self.admin_group]
        }
        
        await database_sync_to_async(websocket_connection_manager.add_connection)(
            str(self.user.id), 
            self.channel_name, 
            connection_info
        )

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        if hasattr(self, 'admin_group'):
            await self.channel_layer.group_discard(self.admin_group, self.channel_name)
        
        # Unregister connection
        if hasattr(self, 'user') and self.user != AnonymousUser():
            await database_sync_to_async(websocket_connection_manager.remove_connection)(
                str(self.user.id), 
                self.channel_name
            )
            logger.info(f"Admin WebSocket disconnected for user {self.user.id} (code: {close_code})")

    async def receive(self, text_data):
        """
        Handle messages received from WebSocket.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'ping')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'get_system_stats':
                await self.handle_get_system_stats(data)
            elif message_type == 'broadcast_message':
                await self.handle_broadcast_message(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}',
                    'timestamp': timezone.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format',
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error handling admin WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error',
                'timestamp': timezone.now().isoformat()
            }))

    async def handle_get_system_stats(self, data):
        """
        Handle request for system statistics.
        """
        try:
            stats = await self.get_system_statistics()
            
            await self.send(text_data=json.dumps({
                'type': 'system_stats',
                'stats': stats,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to get system statistics',
                'timestamp': timezone.now().isoformat()
            }))

    async def handle_broadcast_message(self, data):
        """
        Handle admin broadcast message.
        """
        try:
            if not self.user.is_superuser:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Insufficient permissions for broadcast',
                    'timestamp': timezone.now().isoformat()
                }))
                return
            
            message = data.get('message', '').strip()
            target_group = data.get('target_group', 'all')
            priority = data.get('priority', 'normal')
            
            if not message:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Message content is required',
                    'timestamp': timezone.now().isoformat()
                }))
                return
            
            # Broadcast to appropriate groups
            await self.broadcast_admin_message(message, target_group, priority)
            
            await self.send(text_data=json.dumps({
                'type': 'broadcast_sent',
                'message': 'Message broadcasted successfully',
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to broadcast message',
                'timestamp': timezone.now().isoformat()
            }))

    @database_sync_to_async
    def get_system_statistics(self):
        """
        Get current system statistics.
        """
        try:
            from .models import User, JobPost, Application, Notification
            from django.db.models import Count, Q
            from datetime import timedelta
            
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            stats = {
                'users': {
                    'total': User.objects.count(),
                    'active_24h': User.objects.filter(last_login__gte=last_24h).count(),
                    'job_seekers': User.objects.filter(user_type='job_seeker').count(),
                    'recruiters': User.objects.filter(user_type='recruiter').count(),
                },
                'jobs': {
                    'total': JobPost.objects.count(),
                    'active': JobPost.objects.filter(is_active=True).count(),
                    'posted_24h': JobPost.objects.filter(created_at__gte=last_24h).count(),
                    'posted_7d': JobPost.objects.filter(created_at__gte=last_7d).count(),
                },
                'applications': {
                    'total': Application.objects.count(),
                    'submitted_24h': Application.objects.filter(applied_at__gte=last_24h).count(),
                    'submitted_7d': Application.objects.filter(applied_at__gte=last_7d).count(),
                    'pending': Application.objects.filter(status='pending').count(),
                },
                'notifications': {
                    'total': Notification.objects.count(),
                    'unread': Notification.objects.filter(is_read=False).count(),
                    'sent_24h': Notification.objects.filter(created_at__gte=last_24h).count(),
                },
                'websocket_connections': {
                    'total': len(websocket_connection_manager.connection_metadata),
                    'online_users': len(websocket_connection_manager.active_connections),
                    'by_type': {}
                }
            }
            
            # Get connection stats by type
            for channel_name, metadata in websocket_connection_manager.connection_metadata.items():
                consumer_type = metadata.get('connection_info', {}).get('consumer_type', 'unknown')
                if consumer_type not in stats['websocket_connections']['by_type']:
                    stats['websocket_connections']['by_type'][consumer_type] = 0
                stats['websocket_connections']['by_type'][consumer_type] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {'error': 'Failed to get statistics'}

    async def broadcast_admin_message(self, message, target_group, priority):
        """
        Broadcast message to specified target groups.
        """
        try:
            broadcast_data = {
                'type': 'admin_broadcast',
                'message': message,
                'priority': priority,
                'sender': f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username,
                'timestamp': timezone.now().isoformat()
            }
            
            if target_group == 'all':
                # Broadcast to all notification consumers
                await self.channel_layer.group_send("role_job_seeker", broadcast_data)
                await self.channel_layer.group_send("role_recruiter", broadcast_data)
            elif target_group == 'job_seekers':
                await self.channel_layer.group_send("role_job_seeker", broadcast_data)
            elif target_group == 'recruiters':
                await self.channel_layer.group_send("role_recruiter", broadcast_data)
            elif target_group == 'admins':
                await self.channel_layer.group_send("admin_updates", broadcast_data)
                
        except Exception as e:
            logger.error(f"Error broadcasting admin message: {e}")

    # Event handlers
    async def system_alert(self, event):
        """
        Handle system alert events.
        """
        await self.send(text_data=json.dumps({
            'type': 'system_alert',
            'alert_type': event.get('alert_type'),
            'message': event.get('message'),
            'severity': event.get('severity', 'info'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
            'data': event.get('data', {})
        }))

    async def user_activity_alert(self, event):
        """
        Handle user activity alerts.
        """
        await self.send(text_data=json.dumps({
            'type': 'user_activity_alert',
            'user_id': event.get('user_id'),
            'activity_type': event.get('activity_type'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
            'data': event.get('data', {})
        }))

    async def admin_broadcast(self, event):
        """
        Handle admin broadcast messages.
        """
        await self.send(text_data=json.dumps({
            'type': 'admin_broadcast',
            'message': event['message'],
            'priority': event['priority'],
            'sender': event['sender'],
            'timestamp': event['timestamp']
        }))