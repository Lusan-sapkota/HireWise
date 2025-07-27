"""
Celery configuration for HireWise backend.
"""

import os
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, worker_ready
from django.conf import settings
import logging

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirewise.settings')

app = Celery('hirewise')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Enhanced Celery configuration
app.conf.update(
    # Task execution settings
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,
    timezone=settings.TIME_ZONE,
    enable_utc=True,
    
    # Task routing and queues
    task_routes={
        'matcher.tasks.parse_resume_task': {'queue': 'ai_processing'},
        'matcher.tasks.batch_parse_resumes_task': {'queue': 'ai_processing'},
        'matcher.tasks.calculate_match_score_task': {'queue': 'ai_processing'},
        'matcher.tasks.batch_calculate_match_scores_task': {'queue': 'ai_processing'},
        'matcher.tasks.generate_resume_insights_task': {'queue': 'ai_processing'},
        'matcher.tasks.cleanup_old_analysis_results_task': {'queue': 'maintenance'},
        'matcher.tasks.cleanup_old_files_task': {'queue': 'maintenance'},
        'matcher.tasks.send_notification_task': {'queue': 'notifications'},
        'matcher.tasks.batch_send_notifications_task': {'queue': 'notifications'},
    },
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task time limits
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    
    # Result backend settings
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },
    
    # Task retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Monitoring and logging
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-old-analysis-results': {
            'task': 'matcher.tasks.cleanup_old_analysis_results_task',
            'schedule': 24 * 60 * 60,  # Run daily
            'args': (30,),  # Clean up results older than 30 days
        },
        'cleanup-old-files': {
            'task': 'matcher.tasks.cleanup_old_files_task',
            'schedule': 24 * 60 * 60,  # Run daily
            'args': (365,),  # Clean up files older than 365 days
        },
        'health-check': {
            'task': 'matcher.tasks.health_check_task',
            'schedule': 5 * 60,  # Run every 5 minutes
        },
    },
)

# Set up logging
logger = logging.getLogger(__name__)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    logger.info(f'Debug task executed with request: {self.request!r}')
    return {
        'task_id': self.request.id,
        'message': 'Debug task completed successfully',
        'request_info': str(self.request)
    }


# Celery signal handlers for monitoring and logging
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Log task start."""
    logger.info(f'Task {task.name} [{task_id}] started with args: {args}, kwargs: {kwargs}')


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Log task completion."""
    logger.info(f'Task {task.name} [{task_id}] completed with state: {state}')


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Log task failures."""
    logger.error(f'Task {sender.name} [{task_id}] failed with exception: {exception}')
    logger.error(f'Traceback: {traceback}')


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Log when worker is ready."""
    logger.info(f'Celery worker {sender.hostname} is ready')


# Custom task base class for enhanced error handling
class BaseTask(app.Task):
    """Base task class with enhanced error handling and logging."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f'Task {self.name} [{task_id}] failed: {exc}')
        
        # Send notification about task failure if critical
        if hasattr(self, 'is_critical') and self.is_critical:
            from matcher.tasks import send_notification_task
            send_notification_task.delay(
                user_id=kwargs.get('user_id'),
                notification_type='task_failure',
                message=f'Critical task {self.name} failed: {str(exc)}'
            )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(f'Task {self.name} [{task_id}] retrying due to: {exc}')
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(f'Task {self.name} [{task_id}] completed successfully')


# Set the custom base task class
app.Task = BaseTask