"""
Tests for the notification system including signals, models, and WebSocket functionality.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from datetime import timedelta

from .models import (
    JobPost, Application, Resume, Notification, NotificationPreference, 
    NotificationTemplate, JobSeekerProfile, RecruiterProfile
)
from .signals import match_score_calculated
from .consumers import NotificationConsumer
from .notification_utils import notification_broadcaster

User = get_user_model()


class NotificationModelTests(TestCase):
    """Test notification models and their functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.job_seeker = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@example.com',
            user_type='job_seeker',
            first_name='John',
            last_name='Doe'
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter1',
            email='recruiter@example.com',
            user_type='recruiter',
            first_name='Jane',
            last_name='Smith'
        )
        
        # Create profiles
        JobSeekerProfile.objects.create(
            user=self.job_seeker,
            location='New York',
            experience_level='mid'
        )
        
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Corp',
            industry='Technology'
        )
        
        # Create job post
        self.job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Software Engineer',
            description='Python developer position',
            location='New York',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python,Django,React'
        )
    
    def test_notification_creation(self):
        """Test notification model creation and properties."""
        notification = Notification.objects.create(
            recipient=self.job_seeker,
            notification_type='job_posted',
            title='New Job: Software Engineer',
            message='A new job has been posted',
            job_post=self.job_post,
            priority='normal'
        )
        
        self.assertEqual(notification.recipient, self.job_seeker)
        self.assertEqual(notification.notification_type, 'job_posted')
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.is_sent)
        self.assertIsNone(notification.read_at)
        self.assertIsNone(notification.sent_at)
    
    def test_notification_mark_as_read(self):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            recipient=self.job_seeker,
            notification_type='job_posted',
            title='Test Notification',
            message='Test message'
        )
        
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        
        notification.mark_as_read()
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_notification_mark_as_sent(self):
        """Test marking notification as sent."""
        notification = Notification.objects.create(
            recipient=self.job_seeker,
            notification_type='job_posted',
            title='Test Notification',
            message='Test message'
        )
        
        self.assertFalse(notification.is_sent)
        self.assertIsNone(notification.sent_at)
        
        notification.mark_as_sent()
        
        self.assertTrue(notification.is_sent)
        self.assertIsNotNone(notification.sent_at)
    
    def test_notification_expiration(self):
        """Test notification expiration functionality."""
        # Create expired notification
        expired_notification = Notification.objects.create(
            recipient=self.job_seeker,
            notification_type='job_posted',
            title='Expired Notification',
            message='This should be expired',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        # Create non-expired notification
        active_notification = Notification.objects.create(
            recipient=self.job_seeker,
            notification_type='job_posted',
            title='Active Notification',
            message='This should be active',
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        self.assertTrue(expired_notification.is_expired)
        self.assertFalse(active_notification.is_expired)
    
    def test_notification_preference_creation(self):
        """Test notification preference model."""
        # Get the automatically created preferences
        preferences = NotificationPreference.objects.get(user=self.job_seeker)
        
        # Update preferences
        preferences.job_posted_enabled = True
        preferences.job_posted_delivery = 'websocket'
        preferences.quiet_hours_enabled = True
        preferences.quiet_hours_start = '22:00'
        preferences.quiet_hours_end = '08:00'
        preferences.save()
        
        self.assertTrue(preferences.is_notification_enabled('job_posted'))
        self.assertEqual(preferences.get_delivery_method('job_posted'), 'websocket')
    
    def test_notification_template_rendering(self):
        """Test notification template rendering."""
        template = NotificationTemplate.objects.create(
            template_type='job_posted',
            delivery_channel='websocket',
            title_template='New Job: {job_title}',
            message_template='A new {job_type} position at {company_name} has been posted.',
            is_default=True
        )
        
        context = {
            'job_title': 'Software Engineer',
            'job_type': 'full-time',
            'company_name': 'Tech Corp'
        }
        
        rendered_title = template.render_title(context)
        rendered_message = template.render_message(context)
        
        self.assertEqual(rendered_title, 'New Job: Software Engineer')
        self.assertEqual(rendered_message, 'A new full-time position at Tech Corp has been posted.')
    
    def test_notification_template_error_handling(self):
        """Test notification template error handling for missing variables."""
        template = NotificationTemplate.objects.create(
            template_type='job_posted',
            delivery_channel='websocket',
            title_template='New Job: {job_title}',
            message_template='Position at {company_name} - {missing_variable}',
            is_default=True
        )
        
        context = {
            'job_title': 'Software Engineer',
            'company_name': 'Tech Corp'
            # missing_variable is not provided
        }
        
        rendered_title = template.render_title(context)
        rendered_message = template.render_message(context)
        
        self.assertEqual(rendered_title, 'New Job: Software Engineer')
        self.assertIn('template error', rendered_message)


class NotificationSignalTests(TestCase):
    """Test notification signals and their behavior."""
    
    def setUp(self):
        """Set up test data."""
        self.job_seeker = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@example.com',
            user_type='job_seeker'
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter1',
            email='recruiter@example.com',
            user_type='recruiter'
        )
        
        # Create profiles
        JobSeekerProfile.objects.create(user=self.job_seeker)
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Corp'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker,
            original_filename='resume.pdf',
            file_size=1024
        )
    
    @patch('matcher.notification_utils.notification_broadcaster.notify_job_posted')
    def test_job_posted_signal(self, mock_notify):
        """Test job posted signal creates notifications."""
        job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Software Engineer',
            description='Python developer position',
            location='New York',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python,Django'
        )
        
        # Check that notification was created
        notifications = Notification.objects.filter(
            notification_type='job_posted',
            job_post=job_post
        )
        self.assertTrue(notifications.exists())
        
        # Check that WebSocket notification was sent
        mock_notify.assert_called_once()
    
    @patch('matcher.notification_utils.notification_broadcaster.notify_application_received')
    def test_application_received_signal(self, mock_notify):
        """Test application received signal creates notifications."""
        job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Software Engineer',
            description='Python developer position',
            location='New York',
            job_type='full_time',
            experience_level='mid'
        )
        
        application = Application.objects.create(
            job_seeker=self.job_seeker,
            job_post=job_post,
            resume=self.resume,
            cover_letter='I am interested in this position.'
        )
        
        # Check that notification was created for recruiter
        notifications = Notification.objects.filter(
            recipient=self.recruiter,
            notification_type='application_received',
            application=application
        )
        self.assertTrue(notifications.exists())
        
        # Check that WebSocket notification was sent
        mock_notify.assert_called_once()
    
    @patch('matcher.notification_utils.notification_broadcaster.notify_application_status_changed')
    def test_application_status_changed_signal(self, mock_notify):
        """Test application status change signal creates notifications."""
        job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Software Engineer',
            description='Python developer position',
            location='New York',
            job_type='full_time',
            experience_level='mid'
        )
        
        application = Application.objects.create(
            job_seeker=self.job_seeker,
            job_post=job_post,
            resume=self.resume,
            status='pending'
        )
        
        # Change status
        application.status = 'reviewed'
        application.save()
        
        # Check that notification was created for job seeker
        notifications = Notification.objects.filter(
            recipient=self.job_seeker,
            notification_type='application_status_changed',
            application=application
        )
        self.assertTrue(notifications.exists())
        
        # Check that WebSocket notification was sent
        mock_notify.assert_called_once()
    
    @patch('matcher.notification_utils.notification_broadcaster.notify_match_score_calculated')
    def test_match_score_calculated_signal(self, mock_notify):
        """Test match score calculated signal creates notifications."""
        job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Software Engineer',
            description='Python developer position',
            location='New York',
            job_type='full_time',
            experience_level='mid'
        )
        
        # Send custom signal
        match_score_calculated.send(
            sender=None,
            job_seeker_id=self.job_seeker.id,
            job_id=job_post.id,
            job_title=job_post.title,
            match_score=85.5
        )
        
        # Check that notification was created
        notifications = Notification.objects.filter(
            recipient=self.job_seeker,
            notification_type='match_score_calculated',
            job_post=job_post
        )
        self.assertTrue(notifications.exists())
        
        # Check that WebSocket notification was sent
        mock_notify.assert_called_once()
    
    def test_user_notification_preferences_created(self):
        """Test that notification preferences are created for new users."""
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            user_type='job_seeker'
        )
        
        # Check that preferences were created
        self.assertTrue(
            NotificationPreference.objects.filter(user=new_user).exists()
        )
        
        preferences = NotificationPreference.objects.get(user=new_user)
        self.assertTrue(preferences.job_posted_enabled)
        self.assertTrue(preferences.match_score_calculated_enabled)


class NotificationBroadcasterTests(TestCase):
    """Test notification broadcasting utilities."""
    
    def setUp(self):
        """Set up test data."""
        self.job_seeker = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@example.com',
            user_type='job_seeker'
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter1',
            email='recruiter@example.com',
            user_type='recruiter'
        )
    
    @patch('matcher.notification_utils.async_to_sync')
    def test_notify_user(self, mock_async_to_sync):
        """Test user-specific notification broadcasting."""
        mock_channel_layer = MagicMock()
        mock_async_to_sync.return_value = MagicMock()
        
        with patch.object(notification_broadcaster, 'channel_layer', mock_channel_layer):
            notification_broadcaster.notify_user(
                user_id=str(self.job_seeker.id),
                message='Test notification',
                notification_type='info'
            )
        
        mock_async_to_sync.assert_called_once()
    
    @patch('matcher.notification_utils.async_to_sync')
    def test_notify_role(self, mock_async_to_sync):
        """Test role-based notification broadcasting."""
        mock_channel_layer = MagicMock()
        mock_async_to_sync.return_value = MagicMock()
        
        with patch.object(notification_broadcaster, 'channel_layer', mock_channel_layer):
            notification_broadcaster.notify_role(
                user_type='job_seeker',
                message='Test role notification',
                notification_type='info'
            )
        
        mock_async_to_sync.assert_called_once()
    
    @patch('matcher.notification_utils.async_to_sync')
    def test_notify_job_posted(self, mock_async_to_sync):
        """Test job posted notification broadcasting."""
        mock_channel_layer = MagicMock()
        mock_async_to_sync.return_value = MagicMock()
        
        with patch.object(notification_broadcaster, 'channel_layer', mock_channel_layer):
            notification_broadcaster.notify_job_posted(
                job_id='123',
                job_title='Software Engineer',
                company='Tech Corp',
                location='New York',
                skills_required=['Python', 'Django']
            )
        
        mock_async_to_sync.assert_called_once()


class NotificationConsumerTests(TransactionTestCase):
    """Test WebSocket consumer for notifications."""
    
    def setUp(self):
        """Set up test data."""
        self.job_seeker = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@example.com',
            user_type='job_seeker'
        )
    
    @database_sync_to_async
    def create_test_user(self):
        """Create test user asynchronously."""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            user_type='job_seeker'
        )
    
    async def test_websocket_connection_without_auth(self):
        """Test WebSocket connection without authentication."""
        communicator = WebsocketCommunicator(NotificationConsumer.as_asgi(), "/ws/notifications/")
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)
        
        await communicator.disconnect()
    
    async def test_websocket_ping_pong(self):
        """Test WebSocket ping-pong functionality."""
        # Mock authentication
        user = await self.create_test_user()
        
        with patch.object(NotificationConsumer, 'authenticate_user') as mock_auth:
            mock_auth.return_value = user
            
            communicator = WebsocketCommunicator(
                NotificationConsumer.as_asgi(), 
                "/ws/notifications/"
            )
            
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)
            
            # First receive the connection_established message
            connection_response = await communicator.receive_json_from()
            self.assertEqual(connection_response['type'], 'connection_established')
            
            # Send ping
            await communicator.send_json_to({
                'type': 'ping',
                'timestamp': '2024-01-01T00:00:00Z'
            })
            
            # Receive pong
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], 'pong')
            
            await communicator.disconnect()
    
    async def test_websocket_subscription(self):
        """Test WebSocket notification subscription."""
        user = await self.create_test_user()
        
        with patch.object(NotificationConsumer, 'authenticate_user') as mock_auth:
            mock_auth.return_value = user
            
            communicator = WebsocketCommunicator(
                NotificationConsumer.as_asgi(), 
                "/ws/notifications/"
            )
            
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)
            
            # First receive the connection_established message
            connection_response = await communicator.receive_json_from()
            self.assertEqual(connection_response['type'], 'connection_established')
            
            # Subscribe to notifications
            await communicator.send_json_to({
                'type': 'subscribe',
                'notification_types': ['job_posted', 'match_score_calculated']
            })
            
            # Receive subscription confirmation
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], 'subscription_confirmed')
            self.assertEqual(
                response['notification_types'], 
                ['job_posted', 'match_score_calculated']
            )
            
            await communicator.disconnect()


class NotificationIntegrationTests(TestCase):
    """Integration tests for the complete notification system."""
    
    def setUp(self):
        """Set up test data."""
        self.job_seeker = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@example.com',
            user_type='job_seeker',
            first_name='John'
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter1',
            email='recruiter@example.com',
            user_type='recruiter',
            first_name='Jane'
        )
        
        # Create profiles
        JobSeekerProfile.objects.create(user=self.job_seeker)
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Corp'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker,
            original_filename='resume.pdf',
            file_size=1024
        )
    
    @patch('matcher.notification_utils.notification_broadcaster.notify_job_posted')
    @patch('matcher.notification_utils.notification_broadcaster.notify_application_received')
    def test_complete_application_workflow(self, mock_notify_app, mock_notify_job):
        """Test complete workflow from job posting to application."""
        # Create job post (should trigger job posted notification)
        job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Software Engineer',
            description='Python developer position',
            location='New York',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python,Django'
        )
        
        # Verify job posted notification
        job_notifications = Notification.objects.filter(
            notification_type='job_posted',
            job_post=job_post
        )
        self.assertTrue(job_notifications.exists())
        mock_notify_job.assert_called_once()
        
        # Create application (should trigger application received notification)
        application = Application.objects.create(
            job_seeker=self.job_seeker,
            job_post=job_post,
            resume=self.resume,
            cover_letter='I am interested in this position.'
        )
        
        # Verify application received notification
        app_notifications = Notification.objects.filter(
            recipient=self.recruiter,
            notification_type='application_received',
            application=application
        )
        self.assertTrue(app_notifications.exists())
        mock_notify_app.assert_called_once()
    
    def test_notification_preferences_filtering(self):
        """Test that notifications respect user preferences."""
        # Get and update the automatically created preferences
        preferences = NotificationPreference.objects.get(user=self.job_seeker)
        preferences.job_posted_enabled = False
        preferences.save()
        
        # Create job post
        job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Software Engineer',
            description='Python developer position',
            location='New York',
            job_type='full_time',
            experience_level='mid'
        )
        
        # Verify no notification was created for this user
        notifications = Notification.objects.filter(
            recipient=self.job_seeker,
            notification_type='job_posted',
            job_post=job_post
        )
        self.assertFalse(notifications.exists())
    
    def test_notification_template_usage(self):
        """Test that notifications use templates correctly."""
        # Create custom template
        template = NotificationTemplate.objects.create(
            template_type='job_posted',
            delivery_channel='websocket',
            title_template='Custom: {job_title}',
            message_template='Custom message for {job_title} at {company_name}',
            is_default=True
        )
        
        # Create job post
        job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Software Engineer',
            description='Python developer position',
            location='New York',
            job_type='full_time',
            experience_level='mid'
        )
        
        # Check that notification uses custom template
        notification = Notification.objects.filter(
            notification_type='job_posted',
            job_post=job_post
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('Custom:', notification.title)
        self.assertIn('Custom message', notification.message)


if __name__ == '__main__':
    pytest.main([__file__])