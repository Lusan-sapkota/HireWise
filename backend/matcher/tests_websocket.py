"""
Tests for WebSocket functionality and real-time notifications.
"""

import json
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from unittest.mock import patch, MagicMock
import asyncio

from .consumers import NotificationConsumer
from .notification_utils import NotificationBroadcaster

User = get_user_model()


class WebSocketTestCase(TransactionTestCase):
    """
    Base test case for WebSocket tests with database transactions.
    """
    
    def setUp(self):
        """Set up test data."""
        self.job_seeker = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter1',
            email='recruiter@example.com',
            password='testpass123',
            user_type='recruiter'
        )
        
        # Create JWT tokens
        self.job_seeker_token = str(AccessToken.for_user(self.job_seeker))
        self.recruiter_token = str(AccessToken.for_user(self.recruiter))


class TestNotificationConsumer(WebSocketTestCase):
    """
    Test cases for the NotificationConsumer WebSocket consumer.
    """
    
    def test_websocket_connection_with_valid_jwt(self):
        """Test WebSocket connection with valid JWT token."""
        async def _test():
            communicator = WebsocketCommunicator(
                NotificationConsumer.as_asgi(),
                f"/ws/notifications/?token={self.job_seeker_token}"
            )
            
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)
            
            # Should receive connection confirmation
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], 'connection_established')
            self.assertEqual(response['user_type'], 'job_seeker')
            
            await communicator.disconnect()
        
        asyncio.run(_test())
    
    def test_ping_pong_functionality(self):
        """Test ping-pong functionality."""
        async def _test():
            communicator = WebsocketCommunicator(
                NotificationConsumer.as_asgi(),
                f"/ws/notifications/?token={self.job_seeker_token}"
            )
            
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)
            
            # Skip connection confirmation
            await communicator.receive_json_from()
            
            # Send ping
            await communicator.send_json_to({
                'type': 'ping',
                'timestamp': '2024-01-01T00:00:00Z'
            })
            
            # Should receive pong
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], 'pong')
            self.assertEqual(response['timestamp'], '2024-01-01T00:00:00Z')
            
            await communicator.disconnect()
        
        asyncio.run(_test())


class TestNotificationBroadcaster(WebSocketTestCase):
    """
    Test cases for the NotificationBroadcaster utility.
    """
    
    def setUp(self):
        super().setUp()
        self.broadcaster = NotificationBroadcaster()
    
    @patch('matcher.notification_utils.async_to_sync')
    def test_notify_user(self, mock_async_to_sync):
        """Test sending notification to a specific user."""
        mock_group_send = MagicMock()
        mock_async_to_sync.return_value = mock_group_send
        
        self.broadcaster.notify_user(
            user_id=str(self.job_seeker.id),
            message="Test notification",
            notification_type="info"
        )
        
        mock_group_send.assert_called_once()
        call_args = mock_group_send.call_args[0]
        self.assertEqual(call_args[0], f"user_{self.job_seeker.id}")
        self.assertEqual(call_args[1]['message'], "Test notification")
        self.assertEqual(call_args[1]['notification_type'], "info")
    
    @patch('matcher.notification_utils.async_to_sync')
    def test_notify_job_posted(self, mock_async_to_sync):
        """Test job posted notification."""
        mock_group_send = MagicMock()
        mock_async_to_sync.return_value = mock_group_send
        
        self.broadcaster.notify_job_posted(
            job_id="123",
            job_title="Software Engineer",
            company="Tech Corp",
            location="Remote",
            skills_required=["Python", "Django"]
        )
        
        mock_group_send.assert_called_once()
        call_args = mock_group_send.call_args[0]
        self.assertEqual(call_args[0], "role_job_seeker")
        self.assertIn("Software Engineer", call_args[1]['message'])
        self.assertIn("Tech Corp", call_args[1]['message'])


class TestWebSocketAuthentication(WebSocketTestCase):
    """
    Test cases for WebSocket authentication mechanisms.
    """
    
    def test_jwt_token_validation(self):
        """Test JWT token validation in WebSocket consumer."""
        from .consumers import NotificationConsumer
        
        consumer = NotificationConsumer()
        
        # Mock scope with valid token
        consumer.scope = {
            'query_string': f'token={self.job_seeker_token}'.encode(),
            'user': None
        }
        
        # Test authentication
        user = asyncio.run(consumer.authenticate_user())
        
        self.assertEqual(user.id, self.job_seeker.id)
        self.assertEqual(user.user_type, 'job_seeker')
    
    def test_invalid_jwt_token_handling(self):
        """Test handling of invalid JWT tokens."""
        from .consumers import NotificationConsumer
        
        consumer = NotificationConsumer()
        
        # Mock scope with invalid token
        consumer.scope = {
            'query_string': b'token=invalid_token_here',
            'user': None
        }
        
        # Test authentication
        from django.contrib.auth.models import AnonymousUser
        user = asyncio.run(consumer.authenticate_user())
        
        self.assertIsInstance(user, AnonymousUser)