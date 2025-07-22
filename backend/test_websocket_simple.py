#!/usr/bin/env python
"""
Simple test script to verify WebSocket functionality.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirewise.settings')
django.setup()

from matcher.notification_utils import NotificationBroadcaster
from matcher.consumers import NotificationConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

def test_notification_broadcaster():
    """Test the notification broadcaster functionality."""
    print("Testing NotificationBroadcaster...")
    
    # Create a test user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
    
    broadcaster = NotificationBroadcaster()
    
    # Test user notification
    try:
        broadcaster.notify_user(
            user_id=str(user.id),
            message="Test notification",
            notification_type="info"
        )
        print("✓ User notification sent successfully")
    except Exception as e:
        print(f"✗ User notification failed: {e}")
    
    # Test job posted notification
    try:
        broadcaster.notify_job_posted(
            job_id="test-123",
            job_title="Test Job",
            company="Test Company",
            location="Remote",
            skills_required=["Python", "Django"]
        )
        print("✓ Job posted notification sent successfully")
    except Exception as e:
        print(f"✗ Job posted notification failed: {e}")
    
    print("NotificationBroadcaster tests completed.\n")

def test_jwt_authentication():
    """Test JWT authentication in WebSocket consumer."""
    print("Testing JWT Authentication...")
    
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
    
    # Create JWT token
    token = str(AccessToken.for_user(user))
    
    # Test consumer authentication
    consumer = NotificationConsumer()
    consumer.scope = {
        'query_string': f'token={token}'.encode(),
        'user': None
    }
    
    import asyncio
    
    try:
        authenticated_user = asyncio.run(consumer.authenticate_user())
        if authenticated_user.id == user.id:
            print("✓ JWT authentication successful")
        else:
            print("✗ JWT authentication failed: wrong user")
    except Exception as e:
        print(f"✗ JWT authentication failed: {e}")
    
    print("JWT Authentication tests completed.\n")

if __name__ == "__main__":
    print("Starting WebSocket functionality tests...\n")
    
    test_notification_broadcaster()
    test_jwt_authentication()
    
    print("All tests completed!")