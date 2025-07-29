"""
Comprehensive notification service for handling real-time notifications,
queuing, user preferences, and delivery management.
"""

import json
import logging
from typing import List, Dict, Optional, Any
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Notification, NotificationPreference, NotificationTemplate
from .websocket_utils import websocket_notification_service
from .middleware import websocket_connection_manager

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Comprehensive service for managing notifications with real-time delivery,
    queuing, user preferences, and acknowledgment tracking.
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def create_notification(
        self,
        recipient_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        priority: str = 'normal',
        expires_at: Optional[timezone.datetime] = None,
        send_real_time: bool = True
    ) -> Optional[Notification]:
        """
        Create a new notification and handle delivery based on user preferences.
        
        Args:
            recipient_id: Target user ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional notification data
            priority: Notification priority (low, normal, high, urgent)
            expires_at: Expiration datetime for temporary notifications
            send_real_time: Whether to send real-time notification
        
        Returns:
            Created Notification instance or None if failed
        """
        try:
            with transaction.atomic():
                # Get recipient user
                recipient = User.objects.get(id=recipient_id)
                
                # Check user preferences
                preferences = self.get_user_preferences(recipient)
                if not preferences.is_notification_enabled(notification_type):
                    logger.debug(f"Notification {notification_type} disabled for user {recipient_id}")
                    return None
                
                # Create notification record
                notification = Notification.objects.create(
                    recipient=recipient,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    data=data or {},
                    priority=priority,
                    expires_at=expires_at
                )
                
                # Handle delivery based on preferences and user status
                delivery_method = preferences.get_delivery_method(notification_type)
                self._handle_notification_delivery(notification, delivery_method, send_real_time)
                
                logger.info(f"Notification created and delivered: {notification.id}")
                return notification
                
        except User.DoesNotExist:
            logger.error(f"User not found: {recipient_id}")
            return None
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    def create_bulk_notifications(
        self,
        recipient_ids: List[str],
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        priority: str = 'normal',
        expires_at: Optional[timezone.datetime] = None
    ) -> List[Notification]:
        """
        Create notifications for multiple recipients efficiently.
        
        Args:
            recipient_ids: List of target user IDs
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional notification data
            priority: Notification priority
            expires_at: Expiration datetime
        
        Returns:
            List of created Notification instances
        """
        created_notifications = []
        
        try:
            with transaction.atomic():
                # Get all recipients and their preferences
                recipients = User.objects.filter(id__in=recipient_ids).select_related('notification_preferences')
                
                notifications_to_create = []
                real_time_deliveries = []
                
                for recipient in recipients:
                    # Check user preferences
                    preferences = self.get_user_preferences(recipient)
                    if not preferences.is_notification_enabled(notification_type):
                        continue
                    
                    # Prepare notification for bulk creation
                    notification_data = {
                        'recipient': recipient,
                        'notification_type': notification_type,
                        'title': title,
                        'message': message,
                        'data': data or {},
                        'priority': priority,
                        'expires_at': expires_at
                    }
                    notifications_to_create.append(Notification(**notification_data))
                    
                    # Prepare real-time delivery info
                    delivery_method = preferences.get_delivery_method(notification_type)
                    real_time_deliveries.append({
                        'recipient': recipient,
                        'delivery_method': delivery_method,
                        'notification_data': notification_data
                    })
                
                # Bulk create notifications
                created_notifications = Notification.objects.bulk_create(notifications_to_create)
                
                # Handle real-time deliveries
                for i, delivery_info in enumerate(real_time_deliveries):
                    if i < len(created_notifications):
                        self._handle_notification_delivery(
                            created_notifications[i],
                            delivery_info['delivery_method'],
                            send_real_time=True
                        )
                
                logger.info(f"Bulk created {len(created_notifications)} notifications")
                return created_notifications
                
        except Exception as e:
            logger.error(f"Error creating bulk notifications: {e}")
            return []
    
    def send_job_posted_notification(self, job_post, target_user_ids: Optional[List[str]] = None):
        """
        Send job posted notification to relevant users.
        
        Args:
            job_post: JobPost instance
            target_user_ids: Specific user IDs to notify (optional)
        """
        try:
            # Get notification template
            template = self.get_notification_template('job_posted', 'websocket')
            
            # Prepare context for template rendering
            context = {
                'job_title': job_post.title,
                'company_name': job_post.company_name or 'Company',
                'location': job_post.location,
                'job_type': job_post.job_type,
                'salary_range': self._format_salary_range(job_post.salary_min, job_post.salary_max)
            }
            
            # Render title and message
            title = template.render_title(context) if template else f"New Job: {job_post.title}"
            message = template.render_message(context) if template else f"New job posted: {job_post.title} at {context['company_name']}"
            
            # Prepare notification data
            notification_data = {
                'job_id': str(job_post.id),
                'job_title': job_post.title,
                'company': context['company_name'],
                'location': job_post.location,
                'job_type': job_post.job_type,
                'salary_min': job_post.salary_min,
                'salary_max': job_post.salary_max,
                'skills_required': job_post.skills_required
            }
            
            if target_user_ids:
                # Send to specific users
                self.create_bulk_notifications(
                    recipient_ids=target_user_ids,
                    notification_type='job_posted',
                    title=title,
                    message=message,
                    data=notification_data,
                    priority='normal'
                )
            else:
                # Send to all job seekers
                job_seeker_ids = list(
                    User.objects.filter(user_type='job_seeker', is_active=True)
                    .values_list('id', flat=True)
                )
                
                self.create_bulk_notifications(
                    recipient_ids=job_seeker_ids,
                    notification_type='job_posted',
                    title=title,
                    message=message,
                    data=notification_data,
                    priority='normal'
                )
            
            logger.info(f"Job posted notifications sent for job {job_post.id}")
            
        except Exception as e:
            logger.error(f"Error sending job posted notification: {e}")
    
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
            
            # Get notification template
            template = self.get_notification_template('application_received', 'websocket')
            
            # Prepare context
            context = {
                'applicant_name': applicant_name,
                'job_title': application.job_post.title,
                'match_score': application.match_score,
                'application_date': application.applied_at.strftime('%B %d, %Y')
            }
            
            # Render title and message
            title = template.render_title(context) if template else f"New Application: {application.job_post.title}"
            message = template.render_message(context) if template else f"New application from {applicant_name} for {application.job_post.title}"
            
            # Prepare notification data
            notification_data = {
                'application_id': str(application.id),
                'job_id': str(application.job_post.id),
                'applicant_name': applicant_name,
                'applicant_id': str(application.job_seeker.id),
                'job_title': application.job_post.title,
                'match_score': application.match_score,
                'applied_at': application.applied_at.isoformat()
            }
            
            self.create_notification(
                recipient_id=recruiter_id,
                notification_type='application_received',
                title=title,
                message=message,
                data=notification_data,
                priority='high'
            )
            
            logger.info(f"Application received notification sent for application {application.id}")
            
        except Exception as e:
            logger.error(f"Error sending application received notification: {e}")
    
    def send_application_status_notification(self, application, old_status, new_status):
        """
        Send application status change notification to job seeker.
        
        Args:
            application: Application instance
            old_status: Previous status
            new_status: New status
        """
        try:
            job_seeker_id = str(application.job_seeker.id)
            
            # Get notification template
            template = self.get_notification_template('application_status_changed', 'websocket')
            
            # Prepare context
            context = {
                'job_title': application.job_post.title,
                'company_name': application.job_post.company_name or 'Company',
                'old_status': old_status.replace('_', ' ').title(),
                'new_status': new_status.replace('_', ' ').title(),
                'status_date': timezone.now().strftime('%B %d, %Y')
            }
            
            # Render title and message
            title = template.render_title(context) if template else f"Application Update: {application.job_post.title}"
            message = template.render_message(context) if template else f"Your application status for {application.job_post.title} has been updated to {context['new_status']}"
            
            # Determine priority based on status
            priority_map = {
                'shortlisted': 'high',
                'interview_scheduled': 'high',
                'hired': 'urgent',
                'rejected': 'normal'
            }
            priority = priority_map.get(new_status, 'normal')
            
            # Prepare notification data
            notification_data = {
                'application_id': str(application.id),
                'job_id': str(application.job_post.id),
                'job_title': application.job_post.title,
                'company': context['company_name'],
                'old_status': old_status,
                'new_status': new_status,
                'match_score': application.match_score
            }
            
            self.create_notification(
                recipient_id=job_seeker_id,
                notification_type='application_status_changed',
                title=title,
                message=message,
                data=notification_data,
                priority=priority
            )
            
            logger.info(f"Application status notification sent for application {application.id}")
            
        except Exception as e:
            logger.error(f"Error sending application status notification: {e}")
    
    def send_match_score_notification(self, job_seeker_id, job_post, match_score):
        """
        Send job match score notification to job seeker.
        
        Args:
            job_seeker_id: Job seeker user ID
            job_post: JobPost instance
            match_score: Calculated match score
        """
        try:
            # Get notification template
            template = self.get_notification_template('match_score_calculated', 'websocket')
            
            # Prepare context
            context = {
                'job_title': job_post.title,
                'company_name': job_post.company_name or 'Company',
                'match_score': f"{match_score:.1f}",
                'location': job_post.location,
                'salary_range': self._format_salary_range(job_post.salary_min, job_post.salary_max)
            }
            
            # Render title and message
            title = template.render_title(context) if template else f"Job Match: {job_post.title}"
            message = template.render_message(context) if template else f"New job match found: {job_post.title} ({match_score:.1f}% match)"
            
            # Determine priority based on match score
            if match_score >= 90:
                priority = 'urgent'
            elif match_score >= 75:
                priority = 'high'
            else:
                priority = 'normal'
            
            # Prepare notification data
            notification_data = {
                'job_id': str(job_post.id),
                'job_title': job_post.title,
                'company': context['company_name'],
                'location': job_post.location,
                'job_type': job_post.job_type,
                'match_score': match_score,
                'salary_min': job_post.salary_min,
                'salary_max': job_post.salary_max
            }
            
            self.create_notification(
                recipient_id=str(job_seeker_id),
                notification_type='match_score_calculated',
                title=title,
                message=message,
                data=notification_data,
                priority=priority
            )
            
            logger.info(f"Match score notification sent to user {job_seeker_id} for job {job_post.id}")
            
        except Exception as e:
            logger.error(f"Error sending match score notification: {e}")
    
    def mark_notification_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        Mark a notification as read and send acknowledgment.
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for security check)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient_id=user_id
            )
            
            if not notification.is_read:
                notification.mark_as_read()
                
                # Send read acknowledgment via WebSocket
                self._send_read_acknowledgment(notification)
                
                logger.info(f"Notification {notification_id} marked as read")
                return True
            
            return True
            
        except Notification.DoesNotExist:
            logger.warning(f"Notification not found or access denied: {notification_id}")
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    def mark_all_notifications_read(self, user_id: str, notification_type: Optional[str] = None) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: User ID
            notification_type: Specific notification type (optional)
        
        Returns:
            Number of notifications marked as read
        """
        try:
            query = Q(recipient_id=user_id, is_read=False)
            
            if notification_type:
                query &= Q(notification_type=notification_type)
            
            updated_count = Notification.objects.filter(query).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            # Send bulk read acknowledgment
            if updated_count > 0:
                self._send_bulk_read_acknowledgment(user_id, notification_type, updated_count)
            
            logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return 0
    
    def get_user_notifications(
        self,
        user_id: str,
        notification_type: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get notifications for a user with filtering and pagination.
        
        Args:
            user_id: User ID
            notification_type: Filter by notification type
            is_read: Filter by read status
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
        
        Returns:
            Dictionary with notifications and metadata
        """
        try:
            query = Q(recipient_id=user_id)
            
            if notification_type:
                query &= Q(notification_type=notification_type)
            
            if is_read is not None:
                query &= Q(is_read=is_read)
            
            # Get total count
            total_count = Notification.objects.filter(query).count()
            
            # Get notifications with pagination (order by priority then creation date)
            # Define priority order: urgent=4, high=3, normal=2, low=1
            priority_order = {
                'urgent': 4,
                'high': 3,
                'normal': 2,
                'low': 1
            }
            
            notifications = Notification.objects.filter(query).order_by('-created_at')[offset:offset + limit]
            
            # Sort by priority in Python since we can't do it easily in the database
            notifications = sorted(
                notifications, 
                key=lambda n: (priority_order.get(n.priority, 2), n.created_at), 
                reverse=True
            )
            
            # Serialize notifications
            notification_data = []
            for notification in notifications:
                notification_data.append({
                    'id': str(notification.id),
                    'notification_type': notification.notification_type,
                    'title': notification.title,
                    'message': notification.message,
                    'data': notification.data,
                    'priority': notification.priority,
                    'is_read': notification.is_read,
                    'is_sent': notification.is_sent,
                    'created_at': notification.created_at.isoformat(),
                    'read_at': notification.read_at.isoformat() if notification.read_at else None,
                    'expires_at': notification.expires_at.isoformat() if notification.expires_at else None,
                    'is_expired': notification.is_expired,
                    'age_in_hours': notification.age_in_hours
                })
            
            return {
                'notifications': notification_data,
                'total_count': total_count,
                'unread_count': Notification.objects.filter(
                    recipient_id=user_id, is_read=False
                ).count(),
                'has_more': (offset + limit) < total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return {
                'notifications': [],
                'total_count': 0,
                'unread_count': 0,
                'has_more': False,
                'limit': limit,
                'offset': offset
            }
    
    def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of unread notifications
        """
        try:
            return Notification.objects.filter(
                recipient_id=user_id,
                is_read=False
            ).count()
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    def cleanup_expired_notifications(self) -> int:
        """
        Clean up expired notifications.
        
        Returns:
            Number of notifications cleaned up
        """
        try:
            now = timezone.now()
            expired_count = Notification.objects.filter(
                expires_at__lt=now
            ).delete()[0]
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired notifications")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired notifications: {e}")
            return 0
    
    def queue_notification_for_offline_user(self, notification: Notification):
        """
        Queue notification for offline user delivery when they come online.
        
        Args:
            notification: Notification instance
        """
        try:
            # Use Redis to queue notifications for offline users
            cache_key = f"offline_notifications:{notification.recipient.id}"
            
            # Get existing queued notifications
            queued_notifications = cache.get(cache_key, [])
            
            # Add new notification to queue
            notification_data = {
                'id': str(notification.id),
                'notification_type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'data': notification.data,
                'priority': notification.priority,
                'created_at': notification.created_at.isoformat(),
                'queued_at': timezone.now().isoformat()
            }
            
            queued_notifications.append(notification_data)
            
            # Keep only the latest 100 notifications per user
            if len(queued_notifications) > 100:
                queued_notifications = queued_notifications[-100:]
            
            # Store back in cache with 7 days expiration
            cache.set(cache_key, queued_notifications, 7 * 24 * 3600)
            
            logger.info(f"Notification queued for offline user {notification.recipient.id}")
            
        except Exception as e:
            logger.error(f"Error queuing notification for offline user: {e}")
    
    def deliver_queued_notifications(self, user_id: str):
        """
        Deliver queued notifications when user comes online.
        
        Args:
            user_id: User ID
        """
        try:
            cache_key = f"offline_notifications:{user_id}"
            queued_notifications = cache.get(cache_key, [])
            
            if not queued_notifications:
                return
            
            # Send queued notifications via WebSocket
            for notification_data in queued_notifications:
                websocket_notification_service.send_notification_to_user(
                    user_id=user_id,
                    notification_type=notification_data['notification_type'],
                    message=notification_data['message'],
                    data={
                        **notification_data['data'],
                        'queued': True,
                        'queued_at': notification_data['queued_at']
                    },
                    priority=notification_data['priority']
                )
            
            # Clear the queue
            cache.delete(cache_key)
            
            logger.info(f"Delivered {len(queued_notifications)} queued notifications to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error delivering queued notifications: {e}")
    
    def get_user_preferences(self, user: User) -> NotificationPreference:
        """
        Get or create notification preferences for a user.
        
        Args:
            user: User instance
        
        Returns:
            NotificationPreference instance
        """
        try:
            preferences, created = NotificationPreference.objects.get_or_create(
                user=user,
                defaults={
                    'job_posted_enabled': True,
                    'application_received_enabled': True,
                    'application_status_changed_enabled': True,
                    'match_score_calculated_enabled': True,
                    'interview_scheduled_enabled': True,
                    'message_received_enabled': True,
                    'system_update_enabled': True
                }
            )
            
            if created:
                logger.info(f"Created default notification preferences for user {user.id}")
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            # Return a default preferences object
            return NotificationPreference(user=user)
    
    def get_notification_template(self, notification_type: str, delivery_method: str) -> Optional[NotificationTemplate]:
        """
        Get notification template for specific type and delivery method.
        
        Args:
            notification_type: Type of notification
            delivery_method: Delivery method (websocket, email, push)
        
        Returns:
            NotificationTemplate instance or None
        """
        try:
            return NotificationTemplate.objects.filter(
                notification_type=notification_type,
                delivery_method=delivery_method,
                is_active=True
            ).first()
        except Exception as e:
            logger.error(f"Error getting notification template: {e}")
            return None
    
    def _handle_notification_delivery(self, notification: Notification, delivery_method: str, send_real_time: bool):
        """
        Handle notification delivery based on method and user status.
        
        Args:
            notification: Notification instance
            delivery_method: Delivery method
            send_real_time: Whether to send real-time notification
        """
        try:
            user_id = str(notification.recipient.id)
            
            # Check if user is online
            is_online = websocket_connection_manager.is_user_online(user_id)
            
            if send_real_time and delivery_method in ['websocket', 'both'] and is_online:
                # Send real-time notification
                websocket_notification_service.send_notification_to_user(
                    user_id=user_id,
                    notification_type=notification.notification_type,
                    message=notification.message,
                    data=notification.data,
                    priority=notification.priority
                )
                
                # Mark as sent
                notification.mark_as_sent()
                
            elif not is_online:
                # Queue for offline user
                self.queue_notification_for_offline_user(notification)
            
            # Handle email delivery if specified
            if delivery_method in ['email', 'both']:
                self._send_email_notification(notification)
            
        except Exception as e:
            logger.error(f"Error handling notification delivery: {e}")
    
    def _send_email_notification(self, notification: Notification):
        """
        Send email notification (placeholder for email implementation).
        
        Args:
            notification: Notification instance
        """
        # This would integrate with email service
        # For now, just log that email would be sent
        logger.info(f"Email notification would be sent for {notification.id}")
    
    def _send_read_acknowledgment(self, notification: Notification):
        """
        Send read acknowledgment via WebSocket.
        
        Args:
            notification: Notification instance
        """
        try:
            user_id = str(notification.recipient.id)
            
            if websocket_connection_manager.is_user_online(user_id):
                async_to_sync(self.channel_layer.group_send)(
                    f"user_{user_id}",
                    {
                        'type': 'notification_read_acknowledgment',
                        'notification_id': str(notification.id),
                        'read_at': notification.read_at.isoformat() if notification.read_at else timezone.now().isoformat(),
                        'timestamp': timezone.now().isoformat()
                    }
                )
        except Exception as e:
            logger.error(f"Error sending read acknowledgment: {e}")
    
    def _send_bulk_read_acknowledgment(self, user_id: str, notification_type: Optional[str], count: int):
        """
        Send bulk read acknowledgment via WebSocket.
        
        Args:
            user_id: User ID
            notification_type: Notification type (optional)
            count: Number of notifications marked as read
        """
        try:
            if websocket_connection_manager.is_user_online(user_id):
                async_to_sync(self.channel_layer.group_send)(
                    f"user_{user_id}",
                    {
                        'type': 'bulk_read_acknowledgment',
                        'notification_type': notification_type,
                        'count': count,
                        'timestamp': timezone.now().isoformat()
                    }
                )
        except Exception as e:
            logger.error(f"Error sending bulk read acknowledgment: {e}")
    
    def _format_salary_range(self, salary_min: Optional[int], salary_max: Optional[int]) -> str:
        """
        Format salary range for display.
        
        Args:
            salary_min: Minimum salary
            salary_max: Maximum salary
        
        Returns:
            Formatted salary range string
        """
        if salary_min and salary_max:
            return f"${salary_min:,} - ${salary_max:,}"
        elif salary_min:
            return f"${salary_min:,}+"
        elif salary_max:
            return f"Up to ${salary_max:,}"
        else:
            return "Salary not specified"


# Global notification service instance
notification_service = NotificationService()