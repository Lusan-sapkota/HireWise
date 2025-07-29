"""
Django signals for real-time notifications.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import JobPost, Application, Notification, NotificationPreference, NotificationTemplate
from .notification_service import notification_service

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=JobPost)
def job_posted_notification(sender, instance, created, **kwargs):
    """
    Send notification when a new job is posted.
    Requirement 5.1: WHEN a job is posted THEN the system SHALL send real-time notifications to relevant job seekers via WebSocket
    """
    if created and instance.is_active:
        try:
            # Parse skills from the skills_required field
            skills_required = []
            if instance.skills_required:
                # Assuming skills are stored as comma-separated or JSON
                if isinstance(instance.skills_required, str):
                    skills_required = [skill.strip() for skill in instance.skills_required.split(',')]
                elif isinstance(instance.skills_required, list):
                    skills_required = instance.skills_required
            
            # Get company name from recruiter profile
            company_name = "Unknown Company"
            if hasattr(instance.recruiter, 'recruiter_profile'):
                company_name = instance.recruiter.recruiter_profile.company_name
            
            # Use the new notification service to send job posted notifications
            notification_service.send_job_posted_notification(instance)
            
            logger.info(f"Job posted notification sent for job {instance.id}: {instance.title}")
            
        except Exception as e:
            logger.error(f"Failed to send job posted notification for job {instance.id}: {e}")


@receiver(post_save, sender=Application)
def application_notification(sender, instance, created, **kwargs):
    """
    Send notifications for application events.
    Requirement 5.2: WHEN an application is received THEN the system SHALL notify the employer via WebSocket
    Requirement 5.3: WHEN an application status changes THEN the system SHALL notify the job seeker via WebSocket
    """
    try:
        if created:
            # Use the new notification service to send application received notification
            notification_service.send_application_received_notification(instance)
            logger.info(f"Application received notification sent for application {instance.id}")
            
        else:
            # Application status might have changed - check if status actually changed
            if hasattr(instance, '_original_status'):
                old_status = instance._original_status
                new_status = instance.status
                
                if old_status != new_status:
                    # Use the new notification service to send status change notification
                    notification_service.send_application_status_notification(instance, old_status, new_status)
                    logger.info(f"Application status change notification sent for application {instance.id}: {old_status} -> {new_status}")
    
    except Exception as e:
        logger.error(f"Failed to send application notification for application {instance.id}: {e}")


@receiver(pre_save, sender=Application)
def store_original_application_status(sender, instance, **kwargs):
    """
    Store the original status before saving to detect changes.
    """
    if instance.pk:
        try:
            original = Application.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Application.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None


# Custom signal for match score calculation
from django.dispatch import Signal

match_score_calculated = Signal()


@receiver(match_score_calculated)
def match_score_notification(sender, job_seeker_id, job_id, job_title, match_score, **kwargs):
    """
    Send notification when a match score is calculated.
    Requirement 5.4: WHEN an AI match score is calculated THEN the system SHALL notify the user via WebSocket
    """
    try:
        from .models import JobPost
        
        # Get the job post
        job_post = JobPost.objects.get(id=job_id)
        
        # Use the new notification service to send match score notification
        notification_service.send_match_score_notification(job_seeker_id, job_post, match_score)
        
        logger.info(f"Match score notification sent for job seeker {job_seeker_id}, job {job_id}: {match_score}%")
        
    except Exception as e:
        logger.error(f"Failed to send match score notification: {e}")


# Helper functions for creating persistent notifications

def _get_notification_template(template_type: str, delivery_channel: str = 'websocket') -> NotificationTemplate:
    """Get notification template for given type and channel."""
    try:
        return NotificationTemplate.objects.filter(
            template_type=template_type,
            delivery_channel=delivery_channel,
            is_active=True
        ).first()
    except NotificationTemplate.DoesNotExist:
        return None


def _create_job_posted_notifications(job_post, company_name, skills_required):
    """Create persistent notifications for job posting."""
    try:
        # Get all job seekers who have notifications enabled
        job_seekers = User.objects.filter(user_type='job_seeker')
        template = _get_notification_template('job_posted')
        
        notifications_to_create = []
        
        for job_seeker in job_seekers:
            # Check user preferences
            preferences, created = NotificationPreference.objects.get_or_create(
                user=job_seeker,
                defaults={
                    'job_posted_enabled': True,
                    'job_posted_delivery': 'websocket'
                }
            )
            
            if not preferences.is_notification_enabled('job_posted'):
                continue
            
            # Skip if in quiet hours
            if preferences.is_in_quiet_hours():
                continue
            
            # Create notification context
            context = {
                'job_title': job_post.title,
                'company_name': company_name,
                'location': job_post.location or "Not specified",
                'job_type': job_post.get_job_type_display(),
                'skills_required': ', '.join(skills_required) if skills_required else 'Not specified',
                'user_name': job_seeker.first_name or job_seeker.username
            }
            
            # Render notification content
            if template:
                title = template.render_title(context)
                message = template.render_message(context)
            else:
                title = f"New Job: {job_post.title}"
                message = f"A new {job_post.get_job_type_display().lower()} position at {company_name} has been posted."
            
            notifications_to_create.append(Notification(
                recipient=job_seeker,
                notification_type='job_posted',
                title=title,
                message=message,
                job_post=job_post,
                data={
                    'job_id': str(job_post.id),
                    'company_name': company_name,
                    'location': job_post.location,
                    'skills_required': skills_required
                },
                priority='normal'
            ))
        
        # Bulk create notifications
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)
            logger.info(f"Created {len(notifications_to_create)} job posted notifications")
            
    except Exception as e:
        logger.error(f"Failed to create job posted notifications: {e}")


def _create_application_received_notification(application):
    """Create persistent notification for application received."""
    try:
        recruiter = application.job_post.recruiter
        
        # Check user preferences
        preferences, created = NotificationPreference.objects.get_or_create(
            user=recruiter,
            defaults={
                'application_received_enabled': True,
                'application_received_delivery': 'websocket'
            }
        )
        
        if not preferences.is_notification_enabled('application_received'):
            return
        
        # Skip if in quiet hours
        if preferences.is_in_quiet_hours():
            return
        
        template = _get_notification_template('application_received')
        applicant_name = f"{application.job_seeker.first_name} {application.job_seeker.last_name}".strip()
        if not applicant_name:
            applicant_name = application.job_seeker.username
        
        context = {
            'applicant_name': applicant_name,
            'job_title': application.job_post.title,
            'company_name': getattr(recruiter.recruiter_profile, 'company_name', 'Your Company'),
            'application_date': application.applied_at.strftime('%B %d, %Y'),
            'recruiter_name': recruiter.first_name or recruiter.username
        }
        
        if template:
            title = template.render_title(context)
            message = template.render_message(context)
        else:
            title = f"New Application: {application.job_post.title}"
            message = f"{applicant_name} has applied for the {application.job_post.title} position."
        
        Notification.objects.create(
            recipient=recruiter,
            notification_type='application_received',
            title=title,
            message=message,
            job_post=application.job_post,
            application=application,
            data={
                'application_id': str(application.id),
                'applicant_name': applicant_name,
                'job_id': str(application.job_post.id)
            },
            priority='high'
        )
        
        logger.info(f"Created application received notification for recruiter {recruiter.id}")
        
    except Exception as e:
        logger.error(f"Failed to create application received notification: {e}")


def _create_application_status_notification(application, old_status, new_status):
    """Create persistent notification for application status change."""
    try:
        job_seeker = application.job_seeker
        
        # Check user preferences
        preferences, created = NotificationPreference.objects.get_or_create(
            user=job_seeker,
            defaults={
                'application_status_changed_enabled': True,
                'application_status_changed_delivery': 'both'
            }
        )
        
        if not preferences.is_notification_enabled('application_status_changed'):
            return
        
        # Skip if in quiet hours for non-urgent updates
        if preferences.is_in_quiet_hours() and new_status not in ['hired', 'interview_scheduled']:
            return
        
        template = _get_notification_template('application_status_changed')
        
        # Status-specific messaging
        status_messages = {
            'pending': 'is under review',
            'reviewed': 'has been reviewed',
            'shortlisted': 'has been shortlisted',
            'interview_scheduled': 'has an interview scheduled',
            'interviewed': 'interview has been completed',
            'hired': 'has been accepted! Congratulations!',
            'rejected': 'was not selected this time'
        }
        
        status_message = status_messages.get(new_status, f'status changed to {new_status}')
        
        context = {
            'job_title': application.job_post.title,
            'company_name': getattr(application.job_post.recruiter.recruiter_profile, 'company_name', 'the company'),
            'old_status': old_status.replace('_', ' ').title(),
            'new_status': new_status.replace('_', ' ').title(),
            'status_message': status_message,
            'user_name': job_seeker.first_name or job_seeker.username
        }
        
        if template:
            title = template.render_title(context)
            message = template.render_message(context)
        else:
            title = f"Application Update: {application.job_post.title}"
            message = f"Your application for {application.job_post.title} {status_message}."
        
        # Determine priority based on status
        priority = 'urgent' if new_status in ['hired', 'interview_scheduled'] else 'normal'
        if new_status == 'rejected':
            priority = 'high'
        
        Notification.objects.create(
            recipient=job_seeker,
            notification_type='application_status_changed',
            title=title,
            message=message,
            job_post=application.job_post,
            application=application,
            data={
                'application_id': str(application.id),
                'old_status': old_status,
                'new_status': new_status,
                'job_id': str(application.job_post.id)
            },
            priority=priority
        )
        
        logger.info(f"Created application status notification for job seeker {job_seeker.id}")
        
    except Exception as e:
        logger.error(f"Failed to create application status notification: {e}")


def _create_match_score_notification(job_seeker_id, job_id, job_title, match_score):
    """Create persistent notification for match score calculation."""
    try:
        job_seeker = User.objects.get(id=job_seeker_id)
        job_post = JobPost.objects.get(id=job_id)
        
        # Check user preferences
        preferences, created = NotificationPreference.objects.get_or_create(
            user=job_seeker,
            defaults={
                'match_score_calculated_enabled': True,
                'match_score_calculated_delivery': 'websocket'
            }
        )
        
        if not preferences.is_notification_enabled('match_score_calculated'):
            return
        
        # Skip if in quiet hours
        if preferences.is_in_quiet_hours():
            return
        
        template = _get_notification_template('match_score_calculated')
        
        context = {
            'job_title': job_title,
            'match_score': match_score,
            'company_name': getattr(job_post.recruiter.recruiter_profile, 'company_name', 'the company'),
            'user_name': job_seeker.first_name or job_seeker.username
        }
        
        if template:
            title = template.render_title(context)
            message = template.render_message(context)
        else:
            if match_score >= 80:
                title = f"Excellent Match: {job_title}"
                message = f"Great news! You have a {match_score:.1f}% compatibility with {job_title}."
            elif match_score >= 60:
                title = f"Good Match: {job_title}"
                message = f"You have a {match_score:.1f}% compatibility with {job_title}."
            else:
                title = f"Match Score: {job_title}"
                message = f"Your compatibility score with {job_title} is {match_score:.1f}%."
        
        # Determine priority based on match score
        priority = 'high' if match_score >= 80 else 'normal'
        
        Notification.objects.create(
            recipient=job_seeker,
            notification_type='match_score_calculated',
            title=title,
            message=message,
            job_post=job_post,
            data={
                'job_id': str(job_id),
                'match_score': match_score,
                'job_title': job_title
            },
            priority=priority
        )
        
        logger.info(f"Created match score notification for job seeker {job_seeker_id}")
        
    except Exception as e:
        logger.error(f"Failed to create match score notification: {e}")


# Update existing signals to create persistent notifications
@receiver(post_save, sender=Application)
def application_notification_enhanced(sender, instance, created, **kwargs):
    """
    Enhanced application notification handler with persistence.
    """
    try:
        if created:
            # Create persistent notification for recruiter
            _create_application_received_notification(instance)
            
        else:
            # Check for status changes
            if hasattr(instance, '_original_status'):
                old_status = instance._original_status
                new_status = instance.status
                
                if old_status != new_status:
                    # Create persistent notification for job seeker
                    _create_application_status_notification(instance, old_status, new_status)
                    
    except Exception as e:
        logger.error(f"Failed to create persistent application notification: {e}")


# Signal to create default notification preferences for new users
@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create default notification preferences for new users."""
    if created:
        try:
            NotificationPreference.objects.create(
                user=instance,
                job_posted_enabled=True if instance.user_type == 'job_seeker' else False,
                application_received_enabled=True if instance.user_type == 'recruiter' else False,
                application_status_changed_enabled=True if instance.user_type == 'job_seeker' else False,
                match_score_calculated_enabled=True if instance.user_type == 'job_seeker' else False,
                interview_scheduled_enabled=True,
                system_message_enabled=True
            )
            logger.info(f"Created notification preferences for user {instance.id}")
        except Exception as e:
            logger.error(f"Failed to create notification preferences for user {instance.id}: {e}")