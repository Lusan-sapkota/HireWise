"""
Celery tasks for the matcher app.
"""

from celery import shared_task
from django.conf import settings
from django.utils import timezone
import logging
import time

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def test_celery_task(self):
    """
    Test task to verify Celery is working correctly.
    """
    logger.info(f"Test Celery task executed with task ID: {self.request.id}")
    return {
        'task_id': self.request.id,
        'message': 'Celery is working correctly!',
        'status': 'success'
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def parse_resume_task(self, resume_id):
    """
    Background task for parsing resumes using Google Gemini API.
    """
    logger.info(f"Starting resume parsing for resume ID: {resume_id}")
    
    try:
        from .models import Resume, AIAnalysisResult
        from .services import GeminiResumeParser, GeminiAPIError
        
        # Get the resume
        try:
            resume = Resume.objects.get(id=resume_id)
        except Resume.DoesNotExist:
            logger.error(f"Resume {resume_id} not found")
            return {
                'resume_id': resume_id,
                'status': 'failed',
                'error': 'Resume not found'
            }
        
        # Initialize Gemini parser
        try:
            parser = GeminiResumeParser()
        except GeminiAPIError as e:
            logger.error(f"Gemini API initialization error: {str(e)}")
            # Retry the task
            raise self.retry(exc=e, countdown=60)
        
        # Parse the resume
        try:
            parsing_result = parser.parse_resume(resume.file.path)
        except GeminiAPIError as e:
            logger.error(f"Resume parsing error for {resume_id}: {str(e)}")
            # Retry the task
            raise self.retry(exc=e, countdown=60)
        except Exception as e:
            logger.error(f"Unexpected error parsing resume {resume_id}: {str(e)}")
            return {
                'resume_id': resume_id,
                'status': 'failed',
                'error': str(e)
            }
        
        if not parsing_result['success']:
            logger.error(f"Resume parsing failed for {resume_id}: {parsing_result.get('error', 'Unknown error')}")
            return {
                'resume_id': resume_id,
                'status': 'failed',
                'error': parsing_result.get('error', 'Unknown error')
            }
        
        # Update resume with parsed text
        resume.parsed_text = parsing_result['parsed_text']
        resume.save()
        
        # Create AI analysis result
        AIAnalysisResult.objects.create(
            resume=resume,
            analysis_type='resume_parse',
            input_data=parsing_result['parsed_text'][:1000],  # Truncate for storage
            analysis_result=parsing_result['structured_data'],
            confidence_score=parsing_result['confidence_score'],
            processing_time=parsing_result['processing_time']
        )
        
        logger.info(f"Resume parsing completed for {resume_id}")
        
        return {
            'resume_id': resume_id,
            'status': 'completed',
            'confidence_score': parsing_result['confidence_score'],
            'processing_time': parsing_result['processing_time'],
            'structured_data_keys': list(parsing_result['structured_data'].keys())
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in parse_resume_task for {resume_id}: {str(e)}")
        return {
            'resume_id': resume_id,
            'status': 'failed',
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def batch_parse_resumes_task(self, resume_ids):
    """
    Background task for batch parsing multiple resumes.
    """
    logger.info(f"Starting batch resume parsing for {len(resume_ids)} resumes")
    
    results = []
    
    for resume_id in resume_ids:
        try:
            # Call individual parsing task
            result = parse_resume_task.apply_async(args=[resume_id])
            results.append({
                'resume_id': resume_id,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            logger.error(f"Error queuing parse task for resume {resume_id}: {str(e)}")
            results.append({
                'resume_id': resume_id,
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'batch_id': self.request.id,
        'total_resumes': len(resume_ids),
        'results': results,
        'status': 'completed'
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def calculate_match_score_task(self, resume_id, job_id):
    """
    Background task for calculating job match scores using ML model.
    """
    logger.info(f"Starting match score calculation for resume {resume_id} and job {job_id}")
    
    try:
        from .models import Resume, JobPost, AIAnalysisResult
        from .ml_services import get_ml_model, FeatureExtractor, MatchScoreCache, MLModelError
        
        # Get the resume
        try:
            resume = Resume.objects.get(id=resume_id)
        except Resume.DoesNotExist:
            logger.error(f"Resume {resume_id} not found")
            return {
                'resume_id': resume_id,
                'job_id': job_id,
                'status': 'failed',
                'error': 'Resume not found'
            }
        
        # Get the job post
        try:
            job_post = JobPost.objects.get(id=job_id)
        except JobPost.DoesNotExist:
            logger.error(f"Job post {job_id} not found")
            return {
                'resume_id': resume_id,
                'job_id': job_id,
                'status': 'failed',
                'error': 'Job post not found'
            }
        
        # Check cache first
        cached_score = MatchScoreCache.get_cached_score(str(resume_id), str(job_id))
        if cached_score:
            logger.info(f"Returning cached match score for resume {resume_id} and job {job_id}")
            return {
                'resume_id': resume_id,
                'job_id': job_id,
                'status': 'completed',
                'match_score': cached_score['match_score'],
                'cached': True
            }
        
        # Extract features
        resume_features = FeatureExtractor.extract_resume_features({
            'parsed_text': resume.parsed_text,
            'skills': resume.job_seeker.job_seeker_profile.skills if hasattr(resume.job_seeker, 'job_seeker_profile') else '',
            'structured_data': None
        })
        
        # Get structured data from latest AI analysis if available
        latest_analysis = AIAnalysisResult.objects.filter(
            resume=resume, 
            analysis_type='resume_parse'
        ).order_by('-processed_at').first()
        
        if latest_analysis and latest_analysis.analysis_result:
            resume_features['structured_data'] = latest_analysis.analysis_result
            resume_features = FeatureExtractor.extract_resume_features(resume_features)
        
        job_features = FeatureExtractor.extract_job_features({
            'title': job_post.title,
            'description': job_post.description,
            'requirements': job_post.requirements,
            'skills_required': job_post.skills_required,
            'experience_level': job_post.experience_level,
            'location': job_post.location,
            'remote_work_allowed': job_post.remote_work_allowed,
            'salary_min': job_post.salary_min,
            'salary_max': job_post.salary_max
        })
        
        # Calculate match score using ML model
        try:
            ml_model = get_ml_model()
            score_result = ml_model.calculate_match_score(resume_features, job_features)
        except MLModelError as e:
            logger.error(f"ML model error for resume {resume_id} and job {job_id}: {str(e)}")
            # Retry the task
            raise self.retry(exc=e, countdown=60)
        except Exception as e:
            logger.error(f"Unexpected error calculating match score: {str(e)}")
            return {
                'resume_id': resume_id,
                'job_id': job_id,
                'status': 'failed',
                'error': str(e)
            }
        
        if not score_result['success']:
            logger.error(f"Match score calculation failed for resume {resume_id} and job {job_id}: {score_result.get('error', 'Unknown error')}")
            return {
                'resume_id': resume_id,
                'job_id': job_id,
                'status': 'failed',
                'error': score_result.get('error', 'Unknown error')
            }
        
        # Prepare response data
        response_data = {
            'success': True,
            'resume_id': str(resume_id),
            'job_id': str(job_id),
            'match_score': score_result['match_score'],
            'confidence': score_result['confidence'],
            'method': score_result['method'],
            'analysis': score_result['analysis'],
            'processing_time': score_result['processing_time'],
            'cached': False
        }
        
        # Cache the result
        MatchScoreCache.cache_score(str(resume_id), str(job_id), response_data)
        
        # Create AI analysis result for match score
        AIAnalysisResult.objects.create(
            resume=resume,
            job_post=job_post,
            analysis_type='job_match',
            input_data=f"Resume: {resume.original_filename}, Job: {job_post.title}",
            analysis_result={
                'match_score': score_result['match_score'],
                'analysis': score_result['analysis'],
                'method': score_result['method']
            },
            confidence_score=score_result['confidence'] / 100,  # Convert to 0-1 scale
            processing_time=score_result['processing_time']
        )
        
        logger.info(f"Match score calculation completed for resume {resume_id} and job {job_id}: {score_result['match_score']}")
        
        return {
            'resume_id': resume_id,
            'job_id': job_id,
            'status': 'completed',
            'match_score': score_result['match_score'],
            'confidence': score_result['confidence'],
            'method': score_result['method'],
            'processing_time': score_result['processing_time']
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in calculate_match_score_task for resume {resume_id} and job {job_id}: {str(e)}")
        return {
            'resume_id': resume_id,
            'job_id': job_id,
            'status': 'failed',
            'error': str(e)
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def batch_calculate_match_scores_task(self, resume_ids, job_ids):
    """
    Background task for batch calculating match scores for multiple resume-job combinations.
    """
    logger.info(f"Starting batch match score calculation for {len(resume_ids)} resumes and {len(job_ids)} jobs")
    
    results = []
    total_combinations = len(resume_ids) * len(job_ids)
    completed = 0
    failed = 0
    
    for resume_id in resume_ids:
        for job_id in job_ids:
            try:
                # Call individual match score calculation task
                result = calculate_match_score_task.apply_async(args=[resume_id, job_id])
                results.append({
                    'resume_id': resume_id,
                    'job_id': job_id,
                    'task_id': result.id,
                    'status': 'queued'
                })
                completed += 1
            except Exception as e:
                logger.error(f"Error queuing match score task for resume {resume_id} and job {job_id}: {str(e)}")
                results.append({
                    'resume_id': resume_id,
                    'job_id': job_id,
                    'status': 'failed',
                    'error': str(e)
                })
                failed += 1
    
    logger.info(f"Batch match score calculation queued: {completed} successful, {failed} failed out of {total_combinations} total")
    
    return {
        'batch_id': self.request.id,
        'total_combinations': total_combinations,
        'completed': completed,
        'failed': failed,
        'results': results,
        'status': 'completed'
    }


@shared_task(bind=True)
def cleanup_old_analysis_results_task(self, days_old=30):
    """
    Background task to clean up old AI analysis results.
    """
    logger.info(f"Starting cleanup of AI analysis results older than {days_old} days")
    
    try:
        from .models import AIAnalysisResult
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Delete old analysis results
        deleted_count, _ = AIAnalysisResult.objects.filter(
            processed_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old AI analysis results")
        
        return {
            'task_id': self.request.id,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat(),
            'status': 'completed'
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        return {
            'task_id': self.request.id,
            'status': 'failed',
            'error': str(e)
        }


@shared_task(bind=True)
def generate_resume_insights_task(self, resume_id):
    """
    Background task to generate additional insights for a parsed resume.
    """
    logger.info(f"Generating insights for resume {resume_id}")
    
    try:
        from .models import Resume, AIAnalysisResult
        from .services import GeminiResumeParser, GeminiAPIError
        
        # Get the resume
        try:
            resume = Resume.objects.get(id=resume_id)
        except Resume.DoesNotExist:
            logger.error(f"Resume {resume_id} not found")
            return {
                'resume_id': resume_id,
                'status': 'failed',
                'error': 'Resume not found'
            }
        
        if not resume.parsed_text:
            logger.error(f"Resume {resume_id} has no parsed text")
            return {
                'resume_id': resume_id,
                'status': 'failed',
                'error': 'Resume not parsed yet'
            }
        
        # Initialize Gemini parser for insights
        try:
            parser = GeminiResumeParser()
        except GeminiAPIError as e:
            logger.error(f"Gemini API initialization error: {str(e)}")
            return {
                'resume_id': resume_id,
                'status': 'failed',
                'error': str(e)
            }
        
        # Generate insights using a custom prompt
        insights_prompt = f"""
        Analyze the following resume and provide career insights and recommendations:
        
        {resume.parsed_text}
        
        Please provide:
        1. Career strengths and highlights
        2. Areas for improvement
        3. Recommended career paths
        4. Skills to develop
        5. Industry fit analysis
        
        Format as JSON with these keys: strengths, improvements, career_paths, skills_to_develop, industry_fit
        """
        
        try:
            response = parser.model.generate_content(insights_prompt)
            
            if response and hasattr(response, 'text'):
                # Try to parse as JSON, fallback to text
                try:
                    import json
                    insights_data = json.loads(response.text)
                except json.JSONDecodeError:
                    insights_data = {'raw_insights': response.text}
                
                # Create AI analysis result for insights
                AIAnalysisResult.objects.create(
                    resume=resume,
                    analysis_type='career_insights',
                    input_data=resume.parsed_text[:1000],
                    analysis_result=insights_data,
                    confidence_score=0.8,
                    processing_time=2.0
                )
                
                logger.info(f"Insights generated for resume {resume_id}")
                
                return {
                    'resume_id': resume_id,
                    'status': 'completed',
                    'insights': insights_data
                }
            else:
                return {
                    'resume_id': resume_id,
                    'status': 'failed',
                    'error': 'No response from AI service'
                }
                
        except Exception as e:
            logger.error(f"Error generating insights for resume {resume_id}: {str(e)}")
            return {
                'resume_id': resume_id,
                'status': 'failed',
                'error': str(e)
            }
        
    except Exception as e:
        logger.error(f"Unexpected error in generate_resume_insights_task for {resume_id}: {str(e)}")
        return {
            'resume_id': resume_id,
            'status': 'failed',
            'error': str(e)
        }


@shared_task(bind=True)
def cleanup_old_files_task(self, days_old=365):
    """
    Background task to clean up old uploaded files.
    """
    logger.info(f"Starting cleanup of files older than {days_old} days")
    
    try:
        from .models import Resume
        from datetime import timedelta
        import os
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Get old resumes
        old_resumes = Resume.objects.filter(uploaded_at__lt=cutoff_date)
        deleted_files = 0
        deleted_records = 0
        
        for resume in old_resumes:
            try:
                # Delete the physical file
                if resume.file and os.path.exists(resume.file.path):
                    os.remove(resume.file.path)
                    deleted_files += 1
                
                # Delete the database record
                resume.delete()
                deleted_records += 1
                
            except Exception as e:
                logger.error(f"Error deleting resume {resume.id}: {str(e)}")
        
        logger.info(f"Cleaned up {deleted_files} files and {deleted_records} records")
        
        return {
            'task_id': self.request.id,
            'deleted_files': deleted_files,
            'deleted_records': deleted_records,
            'cutoff_date': cutoff_date.isoformat(),
            'status': 'completed'
        }
        
    except Exception as e:
        logger.error(f"Error in file cleanup task: {str(e)}")
        return {
            'task_id': self.request.id,
            'status': 'failed',
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification_task(self, user_id, notification_type, message, data=None):
    """
    Background task to send notifications to users via WebSocket.
    """
    logger.info(f"Sending notification to user {user_id}: {notification_type}")
    
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from .models import User, Notification
        import json
        
        # Get the user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return {
                'user_id': user_id,
                'status': 'failed',
                'error': 'User not found'
            }
        
        # Create notification record
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            message=message,
            data=data or {},
            is_read=False
        )
        
        # Send via WebSocket
        channel_layer = get_channel_layer()
        group_name = f"user_{user_id}"
        
        notification_data = {
            'type': 'send_notification',
            'notification': {
                'id': str(notification.id),
                'type': notification_type,
                'message': message,
                'data': data or {},
                'created_at': notification.created_at.isoformat(),
                'is_read': False
            }
        }
        
        async_to_sync(channel_layer.group_send)(group_name, notification_data)
        
        logger.info(f"Notification sent to user {user_id}")
        
        return {
            'user_id': user_id,
            'notification_id': str(notification.id),
            'notification_type': notification_type,
            'status': 'completed'
        }
        
    except Exception as e:
        logger.error(f"Error sending notification to user {user_id}: {str(e)}")
        # Retry the task
        raise self.retry(exc=e, countdown=30)


@shared_task(bind=True)
def batch_send_notifications_task(self, user_ids, notification_type, message, data=None):
    """
    Background task to send notifications to multiple users.
    """
    logger.info(f"Sending batch notifications to {len(user_ids)} users: {notification_type}")
    
    results = []
    
    for user_id in user_ids:
        try:
            # Queue individual notification task
            result = send_notification_task.apply_async(
                args=[user_id, notification_type, message, data]
            )
            results.append({
                'user_id': user_id,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            logger.error(f"Error queuing notification for user {user_id}: {str(e)}")
            results.append({
                'user_id': user_id,
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'batch_id': self.request.id,
        'total_users': len(user_ids),
        'results': results,
        'status': 'completed'
    }


@shared_task(bind=True)
def health_check_task(self):
    """
    Background task for system health checks.
    """
    logger.info("Running system health check")
    
    try:
        from django.db import connection
        from django.core.cache import cache
        import redis
        from django.conf import settings
        
        health_status = {
            'task_id': self.request.id,
            'timestamp': timezone.now().isoformat(),
            'status': 'healthy',
            'checks': {}
        }
        
        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['checks']['database'] = {'status': 'healthy'}
        except Exception as e:
            health_status['checks']['database'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'unhealthy'
        
        # Cache check
        try:
            cache.set('health_check', 'test', 30)
            cache.get('health_check')
            health_status['checks']['cache'] = {'status': 'healthy'}
        except Exception as e:
            health_status['checks']['cache'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'unhealthy'
        
        # Redis check
        try:
            redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
            redis_client.ping()
            health_status['checks']['redis'] = {'status': 'healthy'}
        except Exception as e:
            health_status['checks']['redis'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'unhealthy'
        
        # AI service check (Gemini API)
        try:
            from .services import GeminiResumeParser
            parser = GeminiResumeParser()
            # Simple test to check if API key is configured
            if settings.GEMINI_API_KEY:
                health_status['checks']['gemini_api'] = {'status': 'configured'}
            else:
                health_status['checks']['gemini_api'] = {'status': 'not_configured'}
        except Exception as e:
            health_status['checks']['gemini_api'] = {'status': 'unhealthy', 'error': str(e)}
        
        # ML model check
        try:
            from .ml_services import get_ml_model
            ml_model = get_ml_model()
            health_status['checks']['ml_model'] = {'status': 'healthy'}
        except Exception as e:
            health_status['checks']['ml_model'] = {'status': 'unhealthy', 'error': str(e)}
        
        logger.info(f"Health check completed with status: {health_status['status']}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in health check task: {str(e)}")
        return {
            'task_id': self.request.id,
            'timestamp': timezone.now().isoformat(),
            'status': 'failed',
            'error': str(e)
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def process_job_application_task(self, application_id):
    """
    Background task to process job applications and calculate match scores.
    """
    logger.info(f"Processing job application {application_id}")
    
    try:
        from .models import Application, AIAnalysisResult
        
        # Get the application
        try:
            application = Application.objects.get(id=application_id)
        except Application.DoesNotExist:
            logger.error(f"Application {application_id} not found")
            return {
                'application_id': application_id,
                'status': 'failed',
                'error': 'Application not found'
            }
        
        # Calculate match score if not already done
        if application.match_score == 0.0 and application.resume:
            match_result = calculate_match_score_task.apply_async(
                args=[str(application.resume.id), str(application.job_post.id)]
            )
            
            # Wait for match score calculation (with timeout)
            try:
                match_score_result = match_result.get(timeout=300)  # 5 minutes timeout
                if match_score_result['status'] == 'completed':
                    application.match_score = match_score_result['match_score']
                    application.save()
            except Exception as e:
                logger.warning(f"Match score calculation failed for application {application_id}: {str(e)}")
        
        # Send notification to recruiter
        send_notification_task.delay(
            user_id=str(application.job_post.recruiter.id),
            notification_type='new_application',
            message=f'New application received for {application.job_post.title}',
            data={
                'application_id': str(application.id),
                'job_title': application.job_post.title,
                'applicant_name': f"{application.job_seeker.first_name} {application.job_seeker.last_name}",
                'match_score': application.match_score
            }
        )
        
        # Send confirmation to job seeker
        send_notification_task.delay(
            user_id=str(application.job_seeker.id),
            notification_type='application_submitted',
            message=f'Your application for {application.job_post.title} has been submitted',
            data={
                'application_id': str(application.id),
                'job_title': application.job_post.title,
                'company': application.job_post.recruiter.recruiter_profile.company_name if hasattr(application.job_post.recruiter, 'recruiter_profile') else 'Company'
            }
        )
        
        logger.info(f"Job application {application_id} processed successfully")
        
        return {
            'application_id': application_id,
            'status': 'completed',
            'match_score': application.match_score
        }
        
    except Exception as e:
        logger.error(f"Error processing job application {application_id}: {str(e)}")
        return {
            'application_id': application_id,
            'status': 'failed',
            'error': str(e)
        }