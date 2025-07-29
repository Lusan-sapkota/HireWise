"""
WebSocket routing configuration for the matcher app.
Handles real-time notifications, messaging, and other WebSocket connections.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Notifications WebSocket - user-specific notifications
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    
    # Messaging WebSocket - real-time chat and messaging
    re_path(r'ws/messages/$', consumers.MessageConsumer.as_asgi()),
    
    # General updates WebSocket - job matches, application status, etc.
    re_path(r'ws/updates/$', consumers.UpdateConsumer.as_asgi()),
    
    # Interview WebSocket - AI interview sessions
    re_path(r'ws/interview/(?P<session_id>[0-9a-f-]+)/$', consumers.InterviewConsumer.as_asgi()),
    
    # Admin WebSocket - admin-specific real-time updates
    re_path(r'ws/admin/$', consumers.AdminConsumer.as_asgi()),
]