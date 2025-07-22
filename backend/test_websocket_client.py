#!/usr/bin/env python
"""
Simple WebSocket client test to verify real-time notifications.
"""

import asyncio
import websockets
import json
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirewise.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

async def test_websocket_connection():
    """Test WebSocket connection and basic functionality."""
    
    # Create or get test user
    try:
        user = User.objects.get(username='websocket_test_user')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='websocket_test_user',
            email='websocket_test@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
    
    # Generate JWT token
    token = str(AccessToken.for_user(user))
    
    # WebSocket URL with JWT token
    uri = f"ws://localhost:8000/ws/notifications/?token={token}"
    
    try:
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connection established")
            
            # Wait for connection confirmation
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✓ Connection confirmed: {data}")
            
            # Send ping
            ping_message = {
                'type': 'ping',
                'timestamp': '2024-01-01T00:00:00Z'
            }
            await websocket.send(json.dumps(ping_message))
            print("✓ Ping sent")
            
            # Wait for pong
            response = await websocket.recv()
            pong_data = json.loads(response)
            print(f"✓ Pong received: {pong_data}")
            
            # Test subscription
            subscribe_message = {
                'type': 'subscribe',
                'notification_types': ['job_posted', 'match_score_calculated']
            }
            await websocket.send(json.dumps(subscribe_message))
            print("✓ Subscription request sent")
            
            # Wait for subscription confirmation
            response = await websocket.recv()
            sub_data = json.loads(response)
            print(f"✓ Subscription confirmed: {sub_data}")
            
            print("✓ All WebSocket tests passed!")
            
    except websockets.exceptions.ConnectionRefused:
        print("✗ Connection refused. Make sure the Django development server is running with ASGI support.")
        print("  Run: python manage.py runserver")
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")

if __name__ == "__main__":
    print("Starting WebSocket client test...\n")
    asyncio.run(test_websocket_connection())
    print("\nWebSocket client test completed!")