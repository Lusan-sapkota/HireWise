"""
Task monitoring and result tracking utilities for Celery tasks.
"""

from celery import current_app
from celery.result import AsyncResult
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
import logging
import json
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class TaskMonitor:
    """
    Utility class for monitoring Celery task execution and results.
    """
    
    CACHE_PREFIX = 'task_monitor'
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def get_task_status(cls, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a Celery task.
        
        Args:
            task_id: The Celery task ID
            
        Returns:
            Dictionary containing task status information
        """
        try:
            result = AsyncResult(task_id, app=current_app)
            
            status_info = {
                'task_id': task_id,
                'status': result.status,
                'ready': result.ready(),
                'successful': result.successful() if result.ready() else None,
                'failed': result.failed() if result.ready() else None,
                'result': result.result if result.ready() else None,
                'traceback': result.traceback if result.failed() else None,
                'date_done': result.date_done.isoformat() if result.date_done else None,
                'task_name': result.name if hasattr(result, 'name') else None,
            }
            
            # Add additional info from task result if available
            if result.ready() and result.result and isinstance(result.result, dict):
                status_info.update({
                    'processing_time': result.result.get('processing_time'),
                    'error': result.result.get('error'),
                    'confidence_score': result.result.get('confidence_score'),
                })
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {str(e)}")
            return {
                'task_id': task_id,
                'status': 'UNKNOWN',
                'error': str(e)
            }
    
    @classmethod
    def get_batch_task_status(cls, task_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get the status of multiple Celery tasks.
        
        Args:
            task_ids: List of Celery task IDs
            
        Returns:
            Dictionary mapping task IDs to their status information
        """
        results = {}
        
        for task_id in task_ids:
            results[task_id] = cls.get_task_status(task_id)
        
        return results
    
    @classmethod
    def track_task_progress(cls, task_id: str, progress_data: Dict[str, Any]) -> None:
        """
        Track the progress of a long-running task.
        
        Args:
            task_id: The Celery task ID
            progress_data: Dictionary containing progress information
        """
        try:
            cache_key = f"{cls.CACHE_PREFIX}:progress:{task_id}"
            
            progress_info = {
                'task_id': task_id,
                'timestamp': timezone.now().isoformat(),
                **progress_data
            }
            
            cache.set(cache_key, json.dumps(progress_info), cls.CACHE_TIMEOUT)
            logger.info(f"Progress tracked for task {task_id}: {progress_data}")
            
        except Exception as e:
            logger.error(f"Error tracking progress for task {task_id}: {str(e)}")
    
    @classmethod
    def get_task_progress(cls, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the progress of a tracked task.
        
        Args:
            task_id: The Celery task ID
            
        Returns:
            Dictionary containing progress information or None if not found
        """
        try:
            cache_key = f"{cls.CACHE_PREFIX}:progress:{task_id}"
            progress_data = cache.get(cache_key)
            
            if progress_data:
                return json.loads(progress_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting progress for task {task_id}: {str(e)}")
            return None
    
    @classmethod
    def cancel_task(cls, task_id: str) -> Dict[str, Any]:
        """
        Cancel a running Celery task.
        
        Args:
            task_id: The Celery task ID
            
        Returns:
            Dictionary containing cancellation result
        """
        try:
            current_app.control.revoke(task_id, terminate=True)
            
            return {
                'task_id': task_id,
                'status': 'cancelled',
                'message': 'Task cancellation requested'
            }
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return {
                'task_id': task_id,
                'status': 'error',
                'error': str(e)
            }
    
    @classmethod
    def get_active_tasks(cls) -> Dict[str, Any]:
        """
        Get information about currently active tasks.
        
        Returns:
            Dictionary containing active task information
        """
        try:
            inspect = current_app.control.inspect()
            
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            reserved_tasks = inspect.reserved()
            
            return {
                'active': active_tasks or {},
                'scheduled': scheduled_tasks or {},
                'reserved': reserved_tasks or {},
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting active tasks: {str(e)}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    @classmethod
    def get_worker_stats(cls) -> Dict[str, Any]:
        """
        Get Celery worker statistics.
        
        Returns:
            Dictionary containing worker statistics
        """
        try:
            inspect = current_app.control.inspect()
            
            stats = inspect.stats()
            registered_tasks = inspect.registered()
            
            return {
                'stats': stats or {},
                'registered_tasks': registered_tasks or {},
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting worker stats: {str(e)}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }


class TaskResultTracker:
    """
    Utility class for tracking and storing task results.
    """
    
    CACHE_PREFIX = 'task_results'
    CACHE_TIMEOUT = 7200  # 2 hours
    
    @classmethod
    def store_result(cls, task_id: str, result_data: Dict[str, Any]) -> None:
        """
        Store task result in cache for quick access.
        
        Args:
            task_id: The Celery task ID
            result_data: Dictionary containing result data
        """
        try:
            cache_key = f"{cls.CACHE_PREFIX}:{task_id}"
            
            result_info = {
                'task_id': task_id,
                'timestamp': timezone.now().isoformat(),
                'result': result_data
            }
            
            cache.set(cache_key, json.dumps(result_info), cls.CACHE_TIMEOUT)
            logger.info(f"Result stored for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error storing result for task {task_id}: {str(e)}")
    
    @classmethod
    def get_result(cls, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get stored task result from cache.
        
        Args:
            task_id: The Celery task ID
            
        Returns:
            Dictionary containing result data or None if not found
        """
        try:
            cache_key = f"{cls.CACHE_PREFIX}:{task_id}"
            result_data = cache.get(cache_key)
            
            if result_data:
                return json.loads(result_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting result for task {task_id}: {str(e)}")
            return None
    
    @classmethod
    def clear_result(cls, task_id: str) -> None:
        """
        Clear stored task result from cache.
        
        Args:
            task_id: The Celery task ID
        """
        try:
            cache_key = f"{cls.CACHE_PREFIX}:{task_id}"
            cache.delete(cache_key)
            logger.info(f"Result cleared for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error clearing result for task {task_id}: {str(e)}")
    
    @classmethod
    def get_user_task_results(cls, user_id: str, task_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get task results for a specific user.
        
        Args:
            user_id: The user ID
            task_type: Optional task type filter
            
        Returns:
            List of task results for the user
        """
        try:
            from .models import AIAnalysisResult
            
            # Get recent AI analysis results for the user
            query = AIAnalysisResult.objects.filter(
                resume__job_seeker_id=user_id
            ).order_by('-processed_at')[:50]
            
            if task_type:
                query = query.filter(analysis_type=task_type)
            
            results = []
            for analysis in query:
                results.append({
                    'id': str(analysis.id),
                    'task_type': analysis.analysis_type,
                    'confidence_score': analysis.confidence_score,
                    'processing_time': analysis.processing_time,
                    'processed_at': analysis.processed_at.isoformat(),
                    'result': analysis.analysis_result
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting user task results for {user_id}: {str(e)}")
            return []


class TaskNotificationManager:
    """
    Manager for sending task-related notifications.
    """
    
    @classmethod
    def notify_task_completion(cls, task_id: str, user_id: str, task_type: str, result: Dict[str, Any]) -> None:
        """
        Send notification when a task completes.
        
        Args:
            task_id: The Celery task ID
            user_id: The user ID to notify
            task_type: Type of task that completed
            result: Task result data
        """
        try:
            from .tasks import send_notification_task
            
            if result.get('status') == 'completed':
                message = cls._get_success_message(task_type, result)
                notification_type = f'{task_type}_completed'
            else:
                message = cls._get_failure_message(task_type, result)
                notification_type = f'{task_type}_failed'
            
            send_notification_task.delay(
                user_id=user_id,
                notification_type=notification_type,
                message=message,
                data={
                    'task_id': task_id,
                    'task_type': task_type,
                    'result': result
                }
            )
            
            logger.info(f"Task completion notification sent for {task_id} to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending task completion notification: {str(e)}")
    
    @classmethod
    def _get_success_message(cls, task_type: str, result: Dict[str, Any]) -> str:
        """Get success message for task type."""
        messages = {
            'resume_parse': 'Your resume has been successfully parsed and analyzed.',
            'job_match': f'Job match score calculated: {result.get("match_score", "N/A")}%',
            'career_insights': 'Career insights have been generated for your resume.',
            'batch_parse': f'Batch resume parsing completed for {result.get("total_resumes", "N/A")} resumes.',
            'batch_match': f'Batch match scoring completed for {result.get("total_combinations", "N/A")} combinations.',
        }
        
        return messages.get(task_type, f'{task_type.replace("_", " ").title()} completed successfully.')
    
    @classmethod
    def _get_failure_message(cls, task_type: str, result: Dict[str, Any]) -> str:
        """Get failure message for task type."""
        error = result.get('error', 'Unknown error')
        return f'{task_type.replace("_", " ").title()} failed: {error}'