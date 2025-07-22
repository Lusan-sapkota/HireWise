"""
Notification broadcasting utilities for real-time WebSocket notifications.
"""

import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class NotificationBroadcaster:
    """
    Utility class for broadcasting notifications via WebSocket channels.
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return timezone.now().isoformat()
    
    def _send_to_group(self, group_name: str, message_type: str, data: Dict[str, Any]):
        """
        Send message to a specific channel group.
        """
        try:
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    'timestamp': self._get_timestamp(),
                    **data
                }
            )
            logger.info(f"Notification sent to group {group_name}: {message_type}")
        except Exception as e:
            logger.error(f"Failed to send notification to group {group_name}: {e}")
    
    def notify_user(self, user_id: str, message: str, notification_type: str = 'info', 
                   data: Optional[Dict[str, Any]] = None, priority: str = 'normal'):
        """
        Send notification to a specific user.
        
        Args:
            user_id: Target user ID
            message: Notification message
            notification_type: Type of notification (info, success, warning, error)
            data: Additional data to include
            priority: Notification priority (low, normal, high)
        """
        group_name = f"user_{user_id}"
        self._send_to_group(group_name, 'notification_message', {
            'message': message,
            'notification_type': notification_type,
            'data': data or {},
            'priority': priority
        })
    
    def notify_role(self, user_type: str, message: str, notification_type: str = 'info',
                   data: Optional[Dict[str, Any]] = None):
        """
        Send notification to all users of a specific role.
        
        Args:
            user_type: Target user type (job_seeker, recruiter)
            message: Notification message
            notification_type: Type of notification
            data: Additional data to include
        """
        group_name = f"role_{user_type}"
        self._send_to_group(group_name, 'notification_message', {
            'message': message,
            'notification_type': notification_type,
            'data': data or {}
        })
    
    def notify_job_posted(self, job_id: str, job_title: str, company: str, 
                         location: str, skills_required: List[str]):
        """
        Notify relevant job seekers about a new job posting.
        
        Args:
            job_id: Job posting ID
            job_title: Job title
            company: Company name
            location: Job location
            skills_required: List of required skills
        """
        message = f"New job posted: {job_title} at {company}"
        
        # Notify all job seekers
        self._send_to_group('role_job_seeker', 'job_posted_notification', {
            'message': message,
            'job_id': job_id,
            'job_title': job_title,
            'company': company,
            'location': location,
            'data': {
                'skills_required': skills_required
            }
        })
    
    def notify_application_received(self, recruiter_id: str, application_id: str, 
                                  job_id: str, applicant_name: str, job_title: str):
        """
        Notify recruiter about a new job application.
        
        Args:
            recruiter_id: Recruiter user ID
            application_id: Application ID
            job_id: Job posting ID
            applicant_name: Name of the applicant
            job_title: Job title
        """
        message = f"New application received from {applicant_name} for {job_title}"
        
        # Notify specific recruiter
        self._send_to_group(f"user_{recruiter_id}", 'application_received_notification', {
            'message': message,
            'application_id': application_id,
            'job_id': job_id,
            'applicant_name': applicant_name,
            'data': {
                'job_title': job_title
            }
        })
    
    def notify_application_status_changed(self, job_seeker_id: str, application_id: str,
                                        old_status: str, new_status: str, job_title: str):
        """
        Notify job seeker about application status change.
        
        Args:
            job_seeker_id: Job seeker user ID
            application_id: Application ID
            old_status: Previous application status
            new_status: New application status
            job_title: Job title
        """
        status_messages = {
            'pending': 'is under review',
            'reviewed': 'has been reviewed',
            'interview_scheduled': 'has an interview scheduled',
            'accepted': 'has been accepted! Congratulations!',
            'rejected': 'was not selected this time'
        }
        
        status_message = status_messages.get(new_status, f'status changed to {new_status}')
        message = f"Your application for {job_title} {status_message}"
        
        # Determine notification type based on status
        notification_type = 'success' if new_status == 'accepted' else 'info'
        if new_status == 'rejected':
            notification_type = 'warning'
        
        # Notify specific job seeker
        self._send_to_group(f"user_{job_seeker_id}", 'application_status_changed_notification', {
            'message': message,
            'application_id': application_id,
            'old_status': old_status,
            'new_status': new_status,
            'job_title': job_title,
            'notification_type': notification_type
        })
    
    def notify_match_score_calculated(self, job_seeker_id: str, job_id: str, 
                                    job_title: str, match_score: float):
        """
        Notify job seeker about calculated match score.
        
        Args:
            job_seeker_id: Job seeker user ID
            job_id: Job posting ID
            job_title: Job title
            match_score: Calculated match score (0-100)
        """
        # Determine message based on match score
        if match_score >= 80:
            message = f"Excellent match! {match_score:.1f}% compatibility with {job_title}"
            notification_type = 'success'
        elif match_score >= 60:
            message = f"Good match! {match_score:.1f}% compatibility with {job_title}"
            notification_type = 'info'
        else:
            message = f"Match score calculated: {match_score:.1f}% compatibility with {job_title}"
            notification_type = 'info'
        
        # Notify specific job seeker
        self._send_to_group(f"user_{job_seeker_id}", 'match_score_calculated_notification', {
            'message': message,
            'job_id': job_id,
            'job_title': job_title,
            'match_score': match_score,
            'notification_type': notification_type
        })
    
    def notify_interview_scheduled(self, job_seeker_id: str, recruiter_id: str,
                                 application_id: str, job_title: str, 
                                 interview_datetime: str, interview_type: str):
        """
        Notify both job seeker and recruiter about scheduled interview.
        
        Args:
            job_seeker_id: Job seeker user ID
            recruiter_id: Recruiter user ID
            application_id: Application ID
            job_title: Job title
            interview_datetime: Interview date and time
            interview_type: Type of interview (phone, video, in-person)
        """
        # Notify job seeker
        job_seeker_message = f"Interview scheduled for {job_title} on {interview_datetime}"
        self._send_to_group(f"user_{job_seeker_id}", 'notification_message', {
            'message': job_seeker_message,
            'notification_type': 'success',
            'data': {
                'application_id': application_id,
                'job_title': job_title,
                'interview_datetime': interview_datetime,
                'interview_type': interview_type
            }
        })
        
        # Notify recruiter
        recruiter_message = f"Interview scheduled for {job_title} on {interview_datetime}"
        self._send_to_group(f"user_{recruiter_id}", 'notification_message', {
            'message': recruiter_message,
            'notification_type': 'info',
            'data': {
                'application_id': application_id,
                'job_title': job_title,
                'interview_datetime': interview_datetime,
                'interview_type': interview_type
            }
        })
    
    def broadcast_system_message(self, message: str, notification_type: str = 'info',
                               target_roles: Optional[List[str]] = None):
        """
        Broadcast system-wide message to all users or specific roles.
        
        Args:
            message: System message
            notification_type: Type of notification
            target_roles: List of target roles (if None, broadcasts to all)
        """
        if target_roles is None:
            target_roles = ['job_seeker', 'recruiter']
        
        for role in target_roles:
            self._send_to_group(f"role_{role}", 'notification_message', {
                'message': message,
                'notification_type': notification_type,
                'data': {
                    'system_message': True
                }
            })


# Global instance for easy access
notification_broadcaster = NotificationBroadcaster()