"""
Health Check Views for HireWise Backend
Provides endpoints for monitoring system health and dependencies
"""

import time
import logging
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
import redis
import google.generativeai as genai
import joblib
import os

logger = logging.getLogger(__name__)

@method_decorator([csrf_exempt, never_cache], name='dispatch')
class HealthCheckView(View):
    """
    Basic health check endpoint
    Returns 200 if the service is running
    """
    
    def get(self, request):
        return JsonResponse({
            'status': 'healthy',
            'timestamp': time.time(),
            'service': 'hirewise-backend',
            'version': '1.0.0'
        })

@method_decorator([csrf_exempt, never_cache], name='dispatch')
class DetailedHealthCheckView(View):
    """
    Detailed health check endpoint
    Checks all system dependencies and services
    """
    
    def get(self, request):
        start_time = time.time()
        health_status = {
            'status': 'healthy',
            'timestamp': start_time,
            'service': 'hirewise-backend',
            'version': '1.0.0',
            'checks': {}
        }
        
        # Check database
        db_status = self._check_database()
        health_status['checks']['database'] = db_status
        
        # Check Redis
        redis_status = self._check_redis()
        health_status['checks']['redis'] = redis_status
        
        # Check Gemini API
        if getattr(settings, 'HEALTH_CHECK', {}).get('SERVICES', {}).get('gemini_api', True):
            gemini_status = self._check_gemini_api()
            health_status['checks']['gemini_api'] = gemini_status
        
        # Check ML Model
        if getattr(settings, 'HEALTH_CHECK', {}).get('SERVICES', {}).get('ml_model', True):
            ml_status = self._check_ml_model()
            health_status['checks']['ml_model'] = ml_status
        
        # Check file system
        fs_status = self._check_file_system()
        health_status['checks']['file_system'] = fs_status
        
        # Determine overall status
        failed_checks = [name for name, check in health_status['checks'].items() 
                        if check['status'] != 'healthy']
        
        if failed_checks:
            health_status['status'] = 'unhealthy'
            health_status['failed_checks'] = failed_checks
        
        # Add response time
        health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        # Return appropriate HTTP status
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return JsonResponse(health_status, status=status_code)
    
    def _check_database(self):
        """Check database connectivity"""
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            response_time = round((time.time() - start_time) * 1000, 2)
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'message': 'Database connection successful'
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Database connection failed'
            }
    
    def _check_redis(self):
        """Check Redis connectivity"""
        try:
            start_time = time.time()
            
            # Test cache
            test_key = 'health_check_test'
            test_value = 'test_value'
            cache.set(test_key, test_value, 10)
            retrieved_value = cache.get(test_key)
            
            if retrieved_value != test_value:
                raise Exception("Cache set/get test failed")
            
            cache.delete(test_key)
            
            response_time = round((time.time() - start_time) * 1000, 2)
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'message': 'Redis connection successful'
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Redis connection failed'
            }
    
    def _check_gemini_api(self):
        """Check Google Gemini API connectivity"""
        try:
            start_time = time.time()
            
            api_key = getattr(settings, 'GEMINI_API_KEY', '')
            if not api_key:
                return {
                    'status': 'warning',
                    'message': 'Gemini API key not configured'
                }
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Test with a simple request
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Hello", 
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=10,
                    temperature=0.1
                )
            )
            
            if not response.text:
                raise Exception("Empty response from Gemini API")
            
            response_time = round((time.time() - start_time) * 1000, 2)
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'message': 'Gemini API connection successful'
            }
        except Exception as e:
            logger.error(f"Gemini API health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Gemini API connection failed'
            }
    
    def _check_ml_model(self):
        """Check ML model availability"""
        try:
            start_time = time.time()
            
            model_path = getattr(settings, 'ML_MODEL_PATH', '')
            if not model_path:
                return {
                    'status': 'warning',
                    'message': 'ML model path not configured'
                }
            
            # Check if model file exists
            full_path = os.path.join(settings.BASE_DIR, model_path)
            if not os.path.exists(full_path):
                return {
                    'status': 'unhealthy',
                    'message': f'ML model file not found at {full_path}'
                }
            
            # Try to load the model
            model = joblib.load(full_path)
            
            response_time = round((time.time() - start_time) * 1000, 2)
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'message': 'ML model loaded successfully',
                'model_type': str(type(model).__name__)
            }
        except Exception as e:
            logger.error(f"ML model health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'ML model loading failed'
            }
    
    def _check_file_system(self):
        """Check file system access"""
        try:
            start_time = time.time()
            
            # Check media directory
            media_root = settings.MEDIA_ROOT
            if not os.path.exists(media_root):
                os.makedirs(media_root, exist_ok=True)
            
            # Test write access
            test_file = os.path.join(media_root, 'health_check_test.txt')
            with open(test_file, 'w') as f:
                f.write('health check test')
            
            # Test read access
            with open(test_file, 'r') as f:
                content = f.read()
            
            if content != 'health check test':
                raise Exception("File read/write test failed")
            
            # Clean up
            os.remove(test_file)
            
            response_time = round((time.time() - start_time) * 1000, 2)
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'message': 'File system access successful'
            }
        except Exception as e:
            logger.error(f"File system health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'File system access failed'
            }

@method_decorator([csrf_exempt, never_cache], name='dispatch')
class ReadinessCheckView(View):
    """
    Readiness check endpoint
    Returns 200 when the service is ready to accept traffic
    """
    
    def get(self, request):
        # Check critical dependencies
        checks = {
            'database': self._check_database_ready(),
            'redis': self._check_redis_ready()
        }
        
        all_ready = all(check['ready'] for check in checks.values())
        
        response = {
            'ready': all_ready,
            'timestamp': time.time(),
            'checks': checks
        }
        
        status_code = 200 if all_ready else 503
        return JsonResponse(response, status=status_code)
    
    def _check_database_ready(self):
        """Check if database is ready"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {'ready': True, 'message': 'Database ready'}
        except Exception as e:
            return {'ready': False, 'error': str(e)}
    
    def _check_redis_ready(self):
        """Check if Redis is ready"""
        try:
            cache.get('test')  # Simple cache operation
            return {'ready': True, 'message': 'Redis ready'}
        except Exception as e:
            return {'ready': False, 'error': str(e)}

@method_decorator([csrf_exempt, never_cache], name='dispatch')
class LivenessCheckView(View):
    """
    Liveness check endpoint
    Returns 200 if the service is alive (basic functionality)
    """
    
    def get(self, request):
        return JsonResponse({
            'alive': True,
            'timestamp': time.time(),
            'service': 'hirewise-backend'
        })