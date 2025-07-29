"""
WebSocket utility functions for sending real-time notifications and messages.
"""

import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from django.contrib.auth import get_user_model
from .middleware import websocket_connection_manager

User = get_user_model()
logger = logging.getLogger(__name__)


class WebSocketNotificationService:
    """
    Service for sending real-time notifications via WebSocket.
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_notification_to_user(self, user_id, notification_type, message, data=None, priority='normal'):
        """
        Send a notification to a specific user.
        
        Args:
            user_id (str): Target user ID
            notification_type (str): Type of notification
            message (str): Notification message
            data (dict): Additional notification data
            priority (str): Notification priority (low, normal, high, urgent)
        """
        try:
            # Check if user is online
            if not websocket_connection_manager.is_user_online(str(user_id)):
                logger.debug(f"User {user_id} is not online, skipping real-time notification")
                return False
            
            notification_data = {
                'type': 'notification_message',
                'message': message,
                'notification_type': notification_type,
                'timestamp': timezone.now().isoformat(),
                'data': data or {},
                'priority': priority
            }
            
            # Send to user-specific group
            async_to_sync(self.channel_layer.group_send)(
                f"user_{user_id}",
                notification_data
            )
            
            logger.info(f"Notification sent to user {user_id}: {notification_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            return False
    
    def send_notification_to_role(self, user_type, notification_type, message, data=None, priority='normal'):
        """
        Send a notification to all users of a specific role.
        
        Args:
            user_type (str): Target user type (job_seeker, recruiter)
            notification_type (str): Type of notification
            message (str): Notification message
            data (dict): Additional notification data
            priority (str): Notification priority
        """
        try:
            notification_data = {
                'type': 'notification_message',
                'message': message,
                'notification_type': notification_type,
                'timestamp': timezone.now().isoformat(),
                'data': data or {},
                'priority': priority
            }
            
            # Send to role-specific group
            async_to_sync(self.channel_layer.group_send)(
                f"role_{user_type}",
                notification_data
            )
            
            logger.info(f"Notification sent to role {user_type}: {notification_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification to role {user_type}: {e}")
            return False
    
    def send_job_posted_notification(self, job_post, target_users=None):
        """
        Send job posted notification to relevant users.
        
        Args:
            job_post: JobPost instance
            target_users: List of user IDs to notify (optional)
        """
        try:
            message = f"New job posted: {job_post.title} at {job_post.company_name or 'Company'}"
            
            notification_data = {
                'type': 'job_posted_notification',
                'message': message,
                'job_id': str(job_post.id),
                'job_title': job_post.title,
                'company': job_post.company_name or 'Company',
                'location': job_post.location,
                'timestamp': timezone.now().isoformat(),
                'data': {
                    'job_type': job_post.job_type,
                    'salary_min': job_post.salary_min,
                    'salary_max': job_post.salary_max,
                    'skills_required': job_post.skills_required
                }
            }
            
            if target_users:
                # Send to specific users
                for user_id in target_users:
                    async_to_sync(self.channel_layer.group_send)(
                        f"user_{user_id}",
                        notification_data
                    )
            else:
                # Send to all job seekers
                async_to_sync(self.channel_layer.group_send)(
                    "role_job_seeker",
                    notification_data
                )
            
            logger.info(f"Job posted notification sent for job {job_post.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending job posted notification: {e}")
            return False
    
    def send_application_received_notification(self, application):
        """
        Send application received notification to recruiter.
        
        Args:
            application: Application instance
        """
        try:
            recruiter_id = str(application.job_post.recruiter.id)
            applicant_name = f"{application.job_seeker.first_name} {application.job_seeker.last_name}".strip()
            if not applicant_name:
                applicant_name = application.job_seeker.username
            
            message = f"New application received from {applicant_name} for {application.job_post.title}"
            
            notification_data = {
                'type': 'application_received_notification',
                'message': message,
                'application_id': str(application.id),
                'job_id': str(application.job_post.id),
                'applicant_name': applicant_name,
                'timestamp': timezone.now().isoformat(),
                'data': {
                    'job_title': application.job_post.title,
                    'match_score': application.match_score,
                    'applied_at': application.applied_at.isoformat()
                }
            }
            
            async_to_sync(self.channel_layer.group_send)(
                f"user_{recruiter_id}",
                notification_data
            )
            
            logger.info(f"Application received notification sent for application {application.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending application received notification: {e}")
            return False
    
    def send_application_status_notification(self, application, old_status, new_status):
        """
        Send application status change notification to job seeker.
        
        Args:
            application: Application instance
            old_status (str): Previous status
            new_status (str): New status
        """
        try:
            job_seeker_id = str(application.job_seeker.id)
            
            status_messages = {
                'pending': 'Your application is under review',
                'reviewed': 'Your application has been reviewed',
                'shortlisted': 'Congratulations! You have been shortlisted',
                'interview_scheduled': 'Interview has been scheduled',
                'rejected': 'Your application was not selected',
                'hired': 'Congratulations! You have been hired'
            }
            
            message = f"Application status updated for {application.job_post.title}: {status_messages.get(new_status, new_status)}"
            
            notification_data = {
                'type': 'application_status_changed_notification',
                'message': message,
                'application_id': str(application.id),
                'old_status': old_status,
                'new_status': new_status,
                'job_title': application.job_post.title,
                'timestamp': timezone.now().isoformat(),
                'data': {
                    'job_id': str(application.job_post.id),
                    'company': application.job_post.company_name or 'Company',
                    'match_score': application.match_score
                }
            }
            
            async_to_sync(self.channel_layer.group_send)(
                f"user_{job_seeker_id}",
                notification_data
            )
            
            logger.info(f"Application status notification sent for application {application.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending application status notification: {e}")
            return False
    
    def send_match_score_notification(self, job_seeker_id, job_post, match_score):
        """
        Send job match score notification to job seeker.
        
        Args:
            job_seeker_id (str): Job seeker user ID
            job_post: JobPost instance
            match_score (float): Calculated match score
        """
        try:
            message = f"New job match found: {job_post.title} ({match_score:.1f}% match)"
            
            notification_data = {
                'type': 'match_score_calculated_notification',
                'message': message,
                'job_id': str(job_post.id),
                'job_title': job_post.title,
                'match_score': match_score,
                'timestamp': timezone.now().isoformat(),
                'data': {
                    'company': job_post.company_name or 'Company',
                    'location': job_post.location,
                    'job_type': job_post.job_type,
                    'salary_min': job_post.salary_min,
                    'salary_max': job_post.salary_max
                }
            }
            
            async_to_sync(self.channel_layer.group_send)(
                f"user_{job_seeker_id}",
                notification_data
            )
            
            logger.info(f"Match score notification sent to user {job_seeker_id} for job {job_post.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending match score notification: {e}")
            return False


class WebSocketMessageService:
    """
    Service for sending real-time messages via WebSocket.
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_message_to_conversation(self, conversation_id, sender_id, content, message_type='text'):
        """
        Send a message to all participants in a conversation.
        
        Args:
            conversation_id (str): Conversation ID
            sender_id (str): Sender user ID
            content (str): Message content
            message_type (str): Type of message (text, image, file, etc.)
        """
        try:
            from .models import Conversation, Message
            
            # Get conversation and participants
            conversation = Conversation.objects.prefetch_related('participants').get(id=conversation_id)
            sender = User.objects.get(id=sender_id)
            
            # Create message record
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=content,
                message_type=message_type
            )
            
            sender_name = f"{sender.first_name} {sender.last_name}".strip() or sender.username
            
            # Send to all participants
            for participant in conversation.participants.all():
                message_data = {
                    'type': 'message_received',
                    'message_id': str(message.id),
                    'conversation_id': conversation_id,
                    'sender_id': sender_id,
                    'sender_name': sender_name,
                    'content': content,
                    'message_type': message_type,
                    'timestamp': message.sent_at.isoformat(),
                    'is_read': participant.id == sender.id
                }
                
                async_to_sync(self.channel_layer.group_send)(
                    f"messages_user_{participant.id}",
                    message_data
                )
            
            logger.info(f"Message sent to conversation {conversation_id}")
            return message
            
        except Exception as e:
            logger.error(f"Error sending message to conversation: {e}")
            return None
    
    def send_typing_indicator(self, conversation_id, user_id, is_typing=True):
        """
        Send typing indicator to conversation participants.
        
        Args:
            conversation_id (str): Conversation ID
            user_id (str): User who is typing
            is_typing (bool): Whether user is typing or stopped typing
        """
        try:
            from .models import Conversation
            
            conversation = Conversation.objects.prefetch_related('participants').get(id=conversation_id)
            user = User.objects.get(id=user_id)
            user_name = f"{user.first_name} {user.last_name}".strip() or user.username
            
            # Send to other participants
            for participant in conversation.participants.all():
                if participant.id != user.id:
                    typing_data = {
                        'type': 'typing_indicator',
                        'conversation_id': conversation_id,
                        'user_id': user_id,
                        'user_name': user_name,
                        'is_typing': is_typing,
                        'timestamp': timezone.now().isoformat()
                    }
                    
                    async_to_sync(self.channel_layer.group_send)(
                        f"messages_user_{participant.id}",
                        typing_data
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending typing indicator: {e}")
            return False


class WebSocketUpdateService:
    """
    Service for sending real-time updates via WebSocket.
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_job_match_update(self, user_id, job_post, match_score):
        """
        Send job match update to user.
        
        Args:
            user_id (str): Target user ID
            job_post: JobPost instance
            match_score (float): Match score
        """
        try:
            update_data = {
                'type': 'job_match_update',
                'job_id': str(job_post.id),
                'job_title': job_post.title,
                'match_score': match_score,
                'message': f"New job match: {job_post.title} ({match_score:.1f}% match)",
                'timestamp': timezone.now().isoformat(),
                'data': {
                    'company': job_post.company_name or 'Company',
                    'location': job_post.location,
                    'job_type': job_post.job_type
                }
            }
            
            async_to_sync(self.channel_layer.group_send)(
                f"updates_user_{user_id}",
                update_data
            )
            
            logger.info(f"Job match update sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending job match update: {e}")
            return False
    
    def send_application_status_update(self, user_id, application, old_status, new_status):
        """
        Send application status update to user.
        
        Args:
            user_id (str): Target user ID
            application: Application instance
            old_status (str): Previous status
            new_status (str): New status
        """
        try:
            update_data = {
                'type': 'application_status_update',
                'application_id': str(application.id),
                'job_title': application.job_post.title,
                'old_status': old_status,
                'new_status': new_status,
                'message': f"Application status changed from {old_status} to {new_status}",
                'timestamp': timezone.now().isoformat(),
                'data': {
                    'job_id': str(application.job_post.id),
                    'company': application.job_post.company_name or 'Company',
                    'match_score': application.match_score
                }
            }
            
            async_to_sync(self.channel_layer.group_send)(
                f"updates_user_{user_id}",
                update_data
            )
            
            logger.info(f"Application status update sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending application status update: {e}")
            return False
    
    def send_profile_view_update(self, user_id, viewer_name, viewer_company=None):
        """
        Send profile view update to user.
        
        Args:
            user_id (str): Profile owner user ID
            viewer_name (str): Name of the viewer
            viewer_company (str): Company of the viewer (optional)
        """
        try:
            message = f"Your profile was viewed by {viewer_name}"
            if viewer_company:
                message += f" from {viewer_company}"
            
            update_data = {
                'type': 'profile_view_update',
                'viewer_name': viewer_name,
                'viewer_company': viewer_company,
                'message': message,
                'timestamp': timezone.now().isoformat(),
                'data': {}
            }
            
            async_to_sync(self.channel_layer.group_send)(
                f"updates_user_{user_id}",
                update_data
            )
            
            logger.info(f"Profile view update sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending profile view update: {e}")
            return False
    
    def send_system_update(self, target_group, update_type, message, priority='normal', data=None):
        """
        Send system update to target group.
        
        Args:
            target_group (str): Target group (all, job_seekers, recruiters, admins)
            update_type (str): Type of update
            message (str): Update message
            priority (str): Update priority
            data (dict): Additional data
        """
        try:
            update_data = {
                'type': 'system_update',
                'update_type': update_type,
                'message': message,
                'priority': priority,
                'timestamp': timezone.now().isoformat(),
                'data': data or {}
            }
            
            if target_group == 'all':
                async_to_sync(self.channel_layer.group_send)("role_job_seeker", update_data)
                async_to_sync(self.channel_layer.group_send)("role_recruiter", update_data)
            elif target_group == 'job_seekers':
                async_to_sync(self.channel_layer.group_send)("role_job_seeker", update_data)
            elif target_group == 'recruiters':
                async_to_sync(self.channel_layer.group_send)("role_recruiter", update_data)
            elif target_group == 'admins':
                async_to_sync(self.channel_layer.group_send)("admin_updates", update_data)
            
            logger.info(f"System update sent to {target_group}: {update_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending system update: {e}")
            return False


class WebSocketAdminService:
    """
    Service for admin-specific WebSocket operations.
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_system_alert(self, alert_type, message, severity='info', data=None):
        """
        Send system alert to admin users.
        
        Args:
            alert_type (str): Type of alert
            message (str): Alert message
            severity (str): Alert severity (info, warning, error, critical)
            data (dict): Additional alert data
        """
        try:
            alert_data = {
                'type': 'system_alert',
                'alert_type': alert_type,
                'message': message,
                'severity': severity,
                'timestamp': timezone.now().isoformat(),
                'data': data or {}
            }
            
            async_to_sync(self.channel_layer.group_send)(
                "admin_updates",
                alert_data
            )
            
            logger.info(f"System alert sent to admins: {alert_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending system alert: {e}")
            return False
    
    def send_user_activity_alert(self, user_id, activity_type, message, data=None):
        """
        Send user activity alert to admin users.
        
        Args:
            user_id (str): User ID related to the activity
            activity_type (str): Type of activity
            message (str): Activity message
            data (dict): Additional activity data
        """
        try:
            alert_data = {
                'type': 'user_activity_alert',
                'user_id': user_id,
                'activity_type': activity_type,
                'message': message,
                'timestamp': timezone.now().isoformat(),
                'data': data or {}
            }
            
            async_to_sync(self.channel_layer.group_send)(
                "admin_updates",
                alert_data
            )
            
            logger.info(f"User activity alert sent to admins: {activity_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending user activity alert: {e}")
            return False


# Global service instances
websocket_notification_service = WebSocketNotificationService()
websocket_message_service = WebSocketMessageService()
websocket_update_service = WebSocketUpdateService()
websocket_admin_service = WebSocketAdminService()