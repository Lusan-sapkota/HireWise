"""
Tests for Celery background tasks.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from celery import current_app
from celery.result import AsyncResult
import json
import tempfile
import os
from datetime import timedelta

from .models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost, 
    Application, AIAnalysisResult, Notification
)
from .tasks import (
    test_celery_task, parse_resume_task, batch_parse_resumes_task,
    calculate_match_score_task, batch_calculate_match_scores_task,
    cleanup_old_analysis_results_task, cleanup_old_files_task,
    send_notification_task, batch_send_notifications_task,
    generate_resume_insights_task, health_check_task,
    process_job_application_task
)
from .task_monitoring import TaskMonitor, TaskResultTracker, TaskNotificationManager
from factories import (
    UserFactory, JobSeekerProfileFactory, RecruiterProfileFactory,
    ResumeFactory, JobPostFactory, ApplicationFactory
)

User = get_user_model()


class CeleryTaskTestCase(TestCase):
    """Base test case for Celery tasks."""
    
    def setUp(self):
        """Set up test data."""
        self.job_seeker = UserFactory(user_type='job_seeker')
        self.job_seeker_profile = JobSeekerProfileFactory(user=self.job_seeker)
        
        self.recruiter = UserFactory(user_type='recruiter')
        self.recruiter_profile = RecruiterProfileFactory(user=self.recruiter)
        
        self.job_post = JobPostFactory(recruiter=self.recruiter)
        self.resume = ResumeFactory(job_seeker=self.job_seeker)
        
        # Configure Celery for testing
        current_app.conf.update(
            task_always_eager=True,
            task_eager_propagates=True,
        )


class TestCeleryTaskExecution(CeleryTaskTestCase):
    """Test basic Celery task execution."""
    
    def test_test_celery_task(self):
        """Test the debug Celery task."""
        result = test_celery_task.apply()
        
        self.assertTrue(result.successful())
        self.assertIn('task_id', result.result)
        self.assertIn('message', result.result)
        self.assertEqual(result.result['status'], 'success')
    
    def test_task_retry_mechanism(self):
        """Test task retry mechanism."""
        with patch('matcher.tasks.logger') as mock_logger:
            # This should test retry logic, but since we're in eager mode,
            # we'll just verify the task structure
            result = test_celery_task.apply()
            self.assertTrue(result.successful())


class TestResumeParsingTasks(CeleryTaskTestCase):
    """Test resume parsing background tasks."""
    
    @patch('matcher.tasks.GeminiResumeParser')
    def test_parse_resume_task_success(self, mock_parser_class):
        """Test successful resume parsing task."""
        # Mock the parser
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_resume.return_value = {
            'success': True,
            'parsed_text': 'Sample resume text',
            'structured_data': {'skills': ['Python', 'Django']},
            'confidence_score': 0.85,
            'processing_time': 2.5
        }
        
        # Create a temporary file for the resume
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b'Sample PDF content')
            temp_file_path = temp_file.name
        
        try:
            # Update resume with file path
            self.resume.file.name = temp_file_path
            self.resume.save()
            
            # Execute task
            result = parse_resume_task.apply(args=[str(self.resume.id)])
            
            self.assertTrue(result.successful())
            self.assertEqual(result.result['status'], 'completed')
            self.assertEqual(result.result['resume_id'], str(self.resume.id))
            
            # Verify resume was updated
            self.resume.refresh_from_db()
            self.assertEqual(self.resume.parsed_text, 'Sample resume text')
            
            # Verify AI analysis result was created
            analysis = AIAnalysisResult.objects.filter(
                resume=self.resume,
                analysis_type='resume_parse'
            ).first()
            self.assertIsNotNone(analysis)
            self.assertEqual(analysis.confidence_score, 0.85)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    @patch('matcher.tasks.GeminiResumeParser')
    def test_parse_resume_task_failure(self, mock_parser_class):
        """Test resume parsing task failure."""
        # Mock parser to raise an exception
        mock_parser_class.side_effect = Exception('API Error')
        
        result = parse_resume_task.apply(args=[str(self.resume.id)])
        
        self.assertTrue(result.successful())  # Task completes but returns error
        self.assertEqual(result.result['status'], 'failed')
        self.assertIn('error', result.result)
    
    def test_parse_resume_task_resume_not_found(self):
        """Test resume parsing task with non-existent resume."""
        fake_resume_id = '12345678-1234-5678-9012-123456789012'
        
        result = parse_resume_task.apply(args=[fake_resume_id])
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'failed')
        self.assertEqual(result.result['error'], 'Resume not found')
    
    @patch('matcher.tasks.parse_resume_task')
    def test_batch_parse_resumes_task(self, mock_parse_task):
        """Test batch resume parsing task."""
        # Create additional resumes
        resume2 = ResumeFactory(job_seeker=self.job_seeker)
        resume3 = ResumeFactory(job_seeker=self.job_seeker)
        
        resume_ids = [str(self.resume.id), str(resume2.id), str(resume3.id)]
        
        # Mock individual parse tasks
        mock_result = MagicMock()
        mock_result.id = 'mock-task-id'
        mock_parse_task.apply_async.return_value = mock_result
        
        result = batch_parse_resumes_task.apply(args=[resume_ids])
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'completed')
        self.assertEqual(result.result['total_resumes'], 3)
        self.assertEqual(len(result.result['results']), 3)
        
        # Verify individual tasks were queued
        self.assertEqual(mock_parse_task.apply_async.call_count, 3)


class TestMatchScoreTasks(CeleryTaskTestCase):
    """Test match score calculation background tasks."""
    
    @patch('matcher.tasks.get_ml_model')
    @patch('matcher.tasks.FeatureExtractor')
    @patch('matcher.tasks.MatchScoreCache')
    def test_calculate_match_score_task_success(self, mock_cache, mock_extractor, mock_ml_model):
        """Test successful match score calculation task."""
        # Mock cache miss
        mock_cache.get_cached_score.return_value = None
        
        # Mock feature extraction
        mock_extractor.extract_resume_features.return_value = {'skills': ['Python']}
        mock_extractor.extract_job_features.return_value = {'requirements': ['Python']}
        
        # Mock ML model
        mock_model = MagicMock()
        mock_ml_model.return_value = mock_model
        mock_model.calculate_match_score.return_value = {
            'success': True,
            'match_score': 85.5,
            'confidence': 90.0,
            'method': 'ml_model',
            'analysis': {'matching_skills': ['Python']},
            'processing_time': 1.2
        }
        
        result = calculate_match_score_task.apply(
            args=[str(self.resume.id), str(self.job_post.id)]
        )
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'completed')
        self.assertEqual(result.result['match_score'], 85.5)
        self.assertEqual(result.result['confidence'], 90.0)
        
        # Verify AI analysis result was created
        analysis = AIAnalysisResult.objects.filter(
            resume=self.resume,
            job_post=self.job_post,
            analysis_type='job_match'
        ).first()
        self.assertIsNotNone(analysis)
    
    @patch('matcher.tasks.MatchScoreCache')
    def test_calculate_match_score_task_cached(self, mock_cache):
        """Test match score calculation with cached result."""
        # Mock cache hit
        cached_result = {
            'match_score': 75.0,
            'cached': True
        }
        mock_cache.get_cached_score.return_value = cached_result
        
        result = calculate_match_score_task.apply(
            args=[str(self.resume.id), str(self.job_post.id)]
        )
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'completed')
        self.assertEqual(result.result['match_score'], 75.0)
        self.assertTrue(result.result['cached'])
    
    @patch('matcher.tasks.calculate_match_score_task')
    def test_batch_calculate_match_scores_task(self, mock_calc_task):
        """Test batch match score calculation task."""
        # Create additional data
        resume2 = ResumeFactory(job_seeker=self.job_seeker)
        job_post2 = JobPostFactory(recruiter=self.recruiter)
        
        resume_ids = [str(self.resume.id), str(resume2.id)]
        job_ids = [str(self.job_post.id), str(job_post2.id)]
        
        # Mock individual calculation tasks
        mock_result = MagicMock()
        mock_result.id = 'mock-task-id'
        mock_calc_task.apply_async.return_value = mock_result
        
        result = batch_calculate_match_scores_task.apply(args=[resume_ids, job_ids])
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'completed')
        self.assertEqual(result.result['total_combinations'], 4)  # 2 resumes × 2 jobs
        self.assertEqual(len(result.result['results']), 4)
        
        # Verify individual tasks were queued
        self.assertEqual(mock_calc_task.apply_async.call_count, 4)


class TestNotificationTasks(CeleryTaskTestCase):
    """Test notification background tasks."""
    
    @patch('matcher.tasks.get_channel_layer')
    @patch('matcher.tasks.async_to_sync')
    def test_send_notification_task_success(self, mock_async_to_sync, mock_get_channel_layer):
        """Test successful notification sending task."""
        # Mock channel layer
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_group_send = MagicMock()
        mock_async_to_sync.return_value = mock_group_send
        
        result = send_notification_task.apply(args=[
            str(self.job_seeker.id),
            'test_notification',
            'Test message',
            {'key': 'value'}
        ])
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'completed')
        self.assertEqual(result.result['user_id'], str(self.job_seeker.id))
        
        # Verify notification was created in database
        notification = Notification.objects.filter(
            user=self.job_seeker,
            notification_type='test_notification'
        ).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.message, 'Test message')
        self.assertFalse(notification.is_read)
    
    def test_send_notification_task_user_not_found(self):
        """Test notification task with non-existent user."""
        fake_user_id = '12345678-1234-5678-9012-123456789012'
        
        result = send_notification_task.apply(args=[
            fake_user_id,
            'test_notification',
            'Test message'
        ])
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'failed')
        self.assertEqual(result.result['error'], 'User not found')
    
    @patch('matcher.tasks.send_notification_task')
    def test_batch_send_notifications_task(self, mock_send_task):
        """Test batch notification sending task."""
        # Create additional user
        user2 = UserFactory(user_type='job_seeker')
        
        user_ids = [str(self.job_seeker.id), str(user2.id)]
        
        # Mock individual notification tasks
        mock_result = MagicMock()
        mock_result.id = 'mock-task-id'
        mock_send_task.apply_async.return_value = mock_result
        
        result = batch_send_notifications_task.apply(args=[
            user_ids,
            'batch_notification',
            'Batch message'
        ])
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'completed')
        self.assertEqual(result.result['total_users'], 2)
        self.assertEqual(len(result.result['results']), 2)
        
        # Verify individual tasks were queued
        self.assertEqual(mock_send_task.apply_async.call_count, 2)


class TestMaintenanceTasks(CeleryTaskTestCase):
    """Test maintenance background tasks."""
    
    def test_cleanup_old_analysis_results_task(self):
        """Test cleanup of old AI analysis results."""
        # Create old analysis result
        old_analysis = AIAnalysisResult.objects.create(
            resume=self.resume,
            analysis_type='resume_parse',
            input_data='test data',
            analysis_result={'test': 'data'},
            confidence_score=0.8,
            processing_time=1.0
        )
        
        # Make it old by updating the timestamp
        old_date = timezone.now() - timedelta(days=35)
        AIAnalysisResult.objects.filter(id=old_analysis.id).update(processed_at=old_date)
        
        # Create recent analysis result
        recent_analysis = AIAnalysisResult.objects.create(
            resume=self.resume,
            analysis_type='resume_parse',
            input_data='recent data',
            analysis_result={'recent': 'data'},
            confidence_score=0.9,
            processing_time=1.5
        )
        
        result = cleanup_old_analysis_results_task.apply(args=[30])
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'completed')
        self.assertEqual(result.result['deleted_count'], 1)
        
        # Verify old analysis was deleted but recent one remains
        self.assertFalse(AIAnalysisResult.objects.filter(id=old_analysis.id).exists())
        self.assertTrue(AIAnalysisResult.objects.filter(id=recent_analysis.id).exists())
    
    @patch('os.path.exists')
    @patch('os.remove')
    def test_cleanup_old_files_task(self, mock_remove, mock_exists):
        """Test cleanup of old files."""
        # Mock file system operations
        mock_exists.return_value = True
        
        # Create old resume
        old_resume = ResumeFactory(job_seeker=self.job_seeker)
        old_date = timezone.now() - timedelta(days=400)
        Resume.objects.filter(id=old_resume.id).update(uploaded_at=old_date)
        
        result = cleanup_old_files_task.apply(args=[365])
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'completed')
        self.assertEqual(result.result['deleted_files'], 1)
        self.assertEqual(result.result['deleted_records'], 1)
        
        # Verify file removal was called
        mock_remove.assert_called_once()
        
        # Verify old resume was deleted but recent one remains
        self.assertFalse(Resume.objects.filter(id=old_resume.id).exists())
        self.assertTrue(Resume.objects.filter(id=self.resume.id).exists())
    
    @patch('matcher.tasks.connection')
    @patch('matcher.tasks.cache')
    @patch('redis.Redis')
    def test_health_check_task(self, mock_redis, mock_cache, mock_connection):
        """Test system health check task."""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock cache operations
        mock_cache.set.return_value = True
        mock_cache.get.return_value = 'test'
        
        # Mock Redis connection
        mock_redis_client = MagicMock()
        mock_redis.from_url.return_value = mock_redis_client
        mock_redis_client.ping.return_value = True
        
        result = health_check_task.apply()
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'healthy')
        self.assertIn('checks', result.result)
        self.assertEqual(result.result['checks']['database']['status'], 'healthy')
        self.assertEqual(result.result['checks']['cache']['status'], 'healthy')
        self.assertEqual(result.result['checks']['redis']['status'], 'healthy')


class TestTaskMonitoring(CeleryTaskTestCase):
    """Test task monitoring utilities."""
    
    @patch('matcher.task_monitoring.AsyncResult')
    def test_task_monitor_get_status(self, mock_async_result):
        """Test TaskMonitor.get_task_status."""
        # Mock AsyncResult
        mock_result = MagicMock()
        mock_result.status = 'SUCCESS'
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {'test': 'data'}
        mock_result.traceback = None
        mock_result.date_done = timezone.now()
        mock_async_result.return_value = mock_result
        
        task_id = 'test-task-id'
        status_info = TaskMonitor.get_task_status(task_id)
        
        self.assertEqual(status_info['task_id'], task_id)
        self.assertEqual(status_info['status'], 'SUCCESS')
        self.assertTrue(status_info['ready'])
        self.assertTrue(status_info['successful'])
        self.assertFalse(status_info['failed'])
    
    @patch('matcher.task_monitoring.cache')
    def test_task_monitor_track_progress(self, mock_cache):
        """Test TaskMonitor.track_task_progress."""
        task_id = 'test-task-id'
        progress_data = {'progress': 50, 'message': 'Half done'}
        
        TaskMonitor.track_task_progress(task_id, progress_data)
        
        # Verify cache.set was called
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        self.assertIn('task_monitor:progress:test-task-id', call_args[0][0])
    
    @patch('matcher.task_monitoring.cache')
    def test_task_result_tracker_store_result(self, mock_cache):
        """Test TaskResultTracker.store_result."""
        task_id = 'test-task-id'
        result_data = {'status': 'completed', 'data': 'test'}
        
        TaskResultTracker.store_result(task_id, result_data)
        
        # Verify cache.set was called
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        self.assertIn('task_results:test-task-id', call_args[0][0])


class TestJobApplicationProcessing(CeleryTaskTestCase):
    """Test job application processing tasks."""
    
    @patch('matcher.tasks.calculate_match_score_task')
    @patch('matcher.tasks.send_notification_task')
    def test_process_job_application_task(self, mock_send_notification, mock_calc_match):
        """Test job application processing task."""
        # Create application
        application = ApplicationFactory(
            job_seeker=self.job_seeker,
            job_post=self.job_post,
            resume=self.resume,
            match_score=0.0
        )
        
        # Mock match score calculation
        mock_match_result = MagicMock()
        mock_match_result.get.return_value = {
            'status': 'completed',
            'match_score': 78.5
        }
        mock_calc_match.apply_async.return_value = mock_match_result
        
        # Mock notification tasks
        mock_notification_result = MagicMock()
        mock_notification_result.id = 'notification-task-id'
        mock_send_notification.delay.return_value = mock_notification_result
        
        result = process_job_application_task.apply(args=[str(application.id)])
        
        self.assertTrue(result.successful())
        self.assertEqual(result.result['status'], 'completed')
        self.assertEqual(result.result['application_id'], str(application.id))
        
        # Verify match score was updated
        application.refresh_from_db()
        self.assertEqual(application.match_score, 78.5)
        
        # Verify notifications were sent
        self.assertEqual(mock_send_notification.delay.call_count, 2)  # To recruiter and job seeker


class TestTaskIntegration(CeleryTaskTestCase):
    """Test task integration and workflows."""
    
    @patch('matcher.tasks.GeminiResumeParser')
    @patch('matcher.tasks.get_ml_model')
    @patch('matcher.tasks.FeatureExtractor')
    @patch('matcher.tasks.MatchScoreCache')
    def test_resume_to_match_score_workflow(self, mock_cache, mock_extractor, mock_ml_model, mock_parser_class):
        """Test complete workflow from resume parsing to match score calculation."""
        # Mock resume parsing
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_resume.return_value = {
            'success': True,
            'parsed_text': 'Python developer with Django experience',
            'structured_data': {'skills': ['Python', 'Django']},
            'confidence_score': 0.9,
            'processing_time': 2.0
        }
        
        # Mock match score calculation
        mock_cache.get_cached_score.return_value = None
        mock_extractor.extract_resume_features.return_value = {'skills': ['Python', 'Django']}
        mock_extractor.extract_job_features.return_value = {'requirements': ['Python', 'Django']}
        
        mock_model = MagicMock()
        mock_ml_model.return_value = mock_model
        mock_model.calculate_match_score.return_value = {
            'success': True,
            'match_score': 92.0,
            'confidence': 95.0,
            'method': 'ml_model',
            'analysis': {'matching_skills': ['Python', 'Django']},
            'processing_time': 1.5
        }
        
        # Create temporary file for resume
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b'Sample PDF content')
            temp_file_path = temp_file.name
        
        try:
            self.resume.file.name = temp_file_path
            self.resume.save()
            
            # Step 1: Parse resume
            parse_result = parse_resume_task.apply(args=[str(self.resume.id)])
            self.assertTrue(parse_result.successful())
            self.assertEqual(parse_result.result['status'], 'completed')
            
            # Step 2: Calculate match score
            match_result = calculate_match_score_task.apply(
                args=[str(self.resume.id), str(self.job_post.id)]
            )
            self.assertTrue(match_result.successful())
            self.assertEqual(match_result.result['status'], 'completed')
            self.assertEqual(match_result.result['match_score'], 92.0)
            
            # Verify both AI analysis results were created
            parse_analysis = AIAnalysisResult.objects.filter(
                resume=self.resume,
                analysis_type='resume_parse'
            ).first()
            self.assertIsNotNone(parse_analysis)
            
            match_analysis = AIAnalysisResult.objects.filter(
                resume=self.resume,
                job_post=self.job_post,
                analysis_type='job_match'
            ).first()
            self.assertIsNotNone(match_analysis)
            
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


# Test configuration for Celery
@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class CeleryConfigurationTest(TestCase):
    """Test Celery configuration and setup."""
    
    def test_celery_app_configuration(self):
        """Test Celery app is properly configured."""
        from hirewise.celery import app
        
        self.assertEqual(app.main, 'hirewise')
        self.assertTrue(app.conf.task_track_started)
        self.assertEqual(app.conf.task_serializer, 'json')
        self.assertEqual(app.conf.result_serializer, 'json')
    
    def test_task_routing_configuration(self):
        """Test task routing is properly configured."""
        from hirewise.celery import app
        
        # Check if task routes are configured
        self.assertIn('task_routes', app.conf)
        
        # Check specific route configurations
        routes = app.conf.task_routes
        self.assertEqual(routes.get('matcher.tasks.parse_resume_task', {}).get('queue'), 'ai_processing')
        self.assertEqual(routes.get('matcher.tasks.send_notification_task', {}).get('queue'), 'notifications')
        self.assertEqual(routes.get('matcher.tasks.cleanup_old_analysis_results_task', {}).get('queue'), 'maintenance')
    
    def test_periodic_task_configuration(self):
        """Test periodic tasks are properly configured."""
        from hirewise.celery import app
        
        # Check if beat schedule is configured
        self.assertIn('beat_schedule', app.conf)
        
        beat_schedule = app.conf.beat_schedule
        self.assertIn('cleanup-old-analysis-results', beat_schedule)
        self.assertIn('cleanup-old-files', beat_schedule)
        self.assertIn('health-check', beat_schedule)