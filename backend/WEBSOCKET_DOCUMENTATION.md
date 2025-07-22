# WebSocket Real-Time Notifications Documentation

## Overview

The HireWise backend implements real-time notifications using Django Channels and WebSockets. This system provides instant updates for job postings, application status changes, match score calculations, and other important events.

## Architecture

### Components

1. **NotificationConsumer** (`matcher/consumers.py`)
   - Handles WebSocket connections and message routing
   - Supports JWT token authentication
   - Manages user groups and subscriptions

2. **NotificationBroadcaster** (`matcher/notification_utils.py`)
   - Utility class for sending notifications to WebSocket groups
   - Provides methods for different notification types
   - Handles message formatting and delivery

3. **Django Signals** (`matcher/signals.py`)
   - Automatically triggers notifications on model changes
   - Integrates with job posting, application, and match score events

4. **Channel Layers** (Redis)
   - Manages WebSocket connections and message routing
   - Provides scalable real-time communication

## WebSocket Endpoint

### Connection URL
```
ws://localhost:8000/ws/notifications/
```

### Authentication

#### JWT Token Authentication (Recommended)
```
ws://localhost:8000/ws/notifications/?token=<jwt_access_token>
```

#### Session Authentication (Fallback)
Uses Django session authentication if no token is provided.

## Message Types

### Client to Server Messages

#### Ping
```json
{
    "type": "ping",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Subscribe to Notifications
```json
{
    "type": "subscribe",
    "notification_types": ["job_posted", "match_score_calculated"]
}
```

#### Unsubscribe from Notifications
```json
{
    "type": "unsubscribe",
    "notification_types": ["job_posted"]
}
```

### Server to Client Messages

#### Connection Established
```json
{
    "type": "connection_established",
    "user_id": "user-uuid",
    "user_type": "job_seeker",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Pong Response
```json
{
    "type": "pong",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Job Posted Notification
```json
{
    "type": "job_posted",
    "message": "New job posted: Software Engineer at Tech Corp",
    "job_id": "job-uuid",
    "job_title": "Software Engineer",
    "company": "Tech Corp",
    "location": "Remote",
    "timestamp": "2024-01-01T00:00:00Z",
    "data": {
        "skills_required": ["Python", "Django", "React"]
    }
}
```

#### Application Received Notification
```json
{
    "type": "application_received",
    "message": "New application received from John Doe for Software Engineer",
    "application_id": "app-uuid",
    "job_id": "job-uuid",
    "applicant_name": "John Doe",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Application Status Changed Notification
```json
{
    "type": "application_status_changed",
    "message": "Your application for Software Engineer has been accepted! Congratulations!",
    "application_id": "app-uuid",
    "old_status": "pending",
    "new_status": "accepted",
    "job_title": "Software Engineer",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Match Score Calculated Notification
```json
{
    "type": "match_score_calculated",
    "message": "Excellent match! 87.5% compatibility with Software Engineer",
    "job_id": "job-uuid",
    "job_title": "Software Engineer",
    "match_score": 87.5,
    "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Generic Notification
```json
{
    "type": "notification",
    "message": "Your profile has been updated",
    "notification_type": "success",
    "priority": "normal",
    "timestamp": "2024-01-01T00:00:00Z",
    "data": {}
}
```

#### Error Message
```json
{
    "type": "error",
    "message": "Invalid JSON format",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## Group Management

### User Groups
- **user_{user_id}**: User-specific notifications
- **role_{user_type}**: Role-based notifications (job_seeker, recruiter)
- **{notification_type}_{user_type}**: Subscription-based groups

### Automatic Notifications

#### Job Posted (Requirement 5.1)
- Triggered when a new job is created with `is_active=True`
- Sent to all job seekers via `role_job_seeker` group
- Includes job details and required skills

#### Application Received (Requirement 5.2)
- Triggered when a new application is created
- Sent to the specific recruiter who posted the job
- Includes applicant information and job details

#### Application Status Changed (Requirement 5.3)
- Triggered when application status is modified
- Sent to the specific job seeker who applied
- Includes old and new status information

#### Match Score Calculated (Requirement 5.4)
- Triggered via custom signal `match_score_calculated`
- Sent to the specific job seeker
- Includes match score and job information

## Usage Examples

### Frontend JavaScript Client
```javascript
// Connect with JWT token
const token = localStorage.getItem('access_token');
const socket = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);

socket.onopen = function(event) {
    console.log('WebSocket connected');
};

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Notification received:', data);
    
    // Handle different notification types
    switch(data.type) {
        case 'job_posted':
            showJobNotification(data);
            break;
        case 'application_status_changed':
            showStatusNotification(data);
            break;
        case 'match_score_calculated':
            showMatchScoreNotification(data);
            break;
    }
};

// Send ping to keep connection alive
setInterval(() => {
    socket.send(JSON.dumps({
        type: 'ping',
        timestamp: new Date().toISOString()
    }));
}, 30000);
```

### Python Client
```python
import asyncio
import websockets
import json

async def connect_websocket():
    uri = "ws://localhost:8000/ws/notifications/?token=your_jwt_token"
    
    async with websockets.connect(uri) as websocket:
        # Wait for connection confirmation
        response = await websocket.recv()
        print(json.loads(response))
        
        # Subscribe to specific notifications
        await websocket.send(json.dumps({
            'type': 'subscribe',
            'notification_types': ['job_posted', 'match_score_calculated']
        }))
        
        # Listen for notifications
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(connect_websocket())
```

## Broadcasting Notifications Programmatically

### Using NotificationBroadcaster
```python
from matcher.notification_utils import notification_broadcaster

# Send user-specific notification
notification_broadcaster.notify_user(
    user_id="user-uuid",
    message="Your profile has been updated",
    notification_type="success"
)

# Send job posted notification
notification_broadcaster.notify_job_posted(
    job_id="job-uuid",
    job_title="Software Engineer",
    company="Tech Corp",
    location="Remote",
    skills_required=["Python", "Django"]
)

# Send match score notification
notification_broadcaster.notify_match_score_calculated(
    job_seeker_id="user-uuid",
    job_id="job-uuid",
    job_title="Software Engineer",
    match_score=87.5
)
```

### Using Custom Signals
```python
from matcher.signals import match_score_calculated

# Trigger match score notification
match_score_calculated.send(
    sender=None,
    job_seeker_id="user-uuid",
    job_id="job-uuid",
    job_title="Software Engineer",
    match_score=87.5
)
```

## Configuration

### Redis Configuration
```python
# settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": ["redis://localhost:6379/0"],
        },
    },
}
```

### Environment Variables
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## Testing

### Unit Tests
```bash
python manage.py test matcher.tests_websocket
```

### Manual Testing
```bash
# Test notification broadcaster
python test_websocket_simple.py

# Test WebSocket client connection
python test_websocket_client.py
```

## Error Handling

### Connection Errors
- **4001**: Authentication failed
- **4003**: Invalid token format
- **4004**: Token expired

### Message Errors
- Invalid JSON format
- Unknown message type
- Missing required fields

## Security Considerations

1. **JWT Token Validation**: All WebSocket connections validate JWT tokens
2. **User Isolation**: Users only receive notifications intended for them
3. **Rate Limiting**: Consider implementing rate limiting for message sending
4. **Input Validation**: All incoming messages are validated for format and content

## Performance Considerations

1. **Redis Connection Pooling**: Use Redis connection pooling for better performance
2. **Message Batching**: Consider batching notifications for high-volume scenarios
3. **Connection Management**: Implement proper connection cleanup and monitoring
4. **Scaling**: Use Redis Cluster for horizontal scaling

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure Django server is running with ASGI support
2. **Authentication Failed**: Check JWT token validity and format
3. **Messages Not Received**: Verify user is in correct groups
4. **Redis Connection**: Check Redis server status and configuration

### Debugging

1. Enable Django logging for WebSocket events
2. Monitor Redis connections and memory usage
3. Check channel layer configuration
4. Verify signal handlers are properly registered

## Requirements Compliance

This implementation satisfies the following requirements:

- **5.1**: ✅ Job posted notifications sent to relevant job seekers via WebSocket
- **5.2**: ✅ Application received notifications sent to employers via WebSocket  
- **5.3**: ✅ Application status change notifications sent to job seekers via WebSocket
- **5.4**: ✅ Match score calculation notifications sent to users via WebSocket
- **5.5**: ✅ WebSocket connection established at ws/notifications/ endpoint