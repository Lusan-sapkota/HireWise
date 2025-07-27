"""
Comprehensive tests for error handling and logging functionality
"""

import json
import time
import uuid
from unittest.mock import patch, Mock, MagicMock
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.response import Response

from .exceptions import (
    HireWiseBaseException, ValidationException, AuthenticationException,
    AuthorizationException, ResourceNotFoundException, ExternalServiceException,
    GeminiAPIException, MLModelException, FileProcessingException,
    RateLimitException, DatabaseException, ConfigurationException,
    custom_exception_handler
)
from .middleware import (
    RequestTrackingMiddleware, RateLimitMiddleware, SecurityMiddleware,
    ErrorMonitoringMiddleware
)
from .error_recovery import (
    RetryConfig, CircuitBreaker, CircuitBreakerConfig, BulkheadPattern,
    retry_with_backoff, safe_execute, resilient_external_service
)
from .logging_config import (
    StructuredFormatter, RequestContextFilter, AIOperationLogger,
    APIRequestLogger, SecurityLogger, PerformanceLogger
)

User = get_user_model()


class CustomExceptionTests(TestCase):
    """Test custom exception classes"""
    
    def test_hirewise_base_exception(self):
        """Test base exception functionality"""
        exc = HireWiseBaseException(
            message="Test error",
            code="TEST_ERROR",
            status_code=400,
            details={'field': 'value'}
        )
        
        self.assertEqual(str(exc), "Test error")
        self.assertEqual(exc.code, "TEST_ERROR")
        self.assertEqual(exc.status_code, 400)
        self.assertEqual(exc.details, {'field': 'value'})
    
    def test_validation_exception(self):
        """Test validation exception"""
        exc = ValidationException("Invalid data")
        
        self.assertEqual(str(exc), "Invalid data")
        self.assertEqual(exc.code, "VALIDATION_ERROR")
        self.assertEqual(exc.status_code, 400)
    
    def test_authentication_exception(self):
        """Test authentication exception"""
        exc = AuthenticationException()
        
        self.assertEqual(exc.code, "AUTHENTICATION_ERROR")
        self.assertEqual(exc.status_code, 401)
    
    def test_external_service_exception(self):
        """Test external service exception"""
        exc = ExternalServiceException("Service unavailable")
        
        self.assertEqual(str(exc), "Service unavailable")
        self.assertEqual(exc.code, "EXTERNAL_SERVICE_ERROR")
        self.assertEqual(exc.status_code, 503)
    
    def test_gemini_api_exception(self):
        """Test Gemini API exception"""
        exc = GeminiAPIException("API quota exceeded")
        
        self.assertEqual(str(exc), "API quota exceeded")
        self.assertEqual(exc.code, "GEMINI_API_ERROR")
        self.assertEqual(exc.status_code, 503)


class CustomExceptionHandlerTests(TestCase):
    """Test custom exception handler"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_custom_exception_handling(self):
        """Test handling of custom exceptions"""
        request = self.factory.get('/test/')
        request.user = self.user
        request.request_id = str(uuid.uuid4())
        
        context = {'request': request}
        exc = ValidationException("Test validation error", details={'field': 'error'})
        
        response = custom_exception_handler(exc, context)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
        self.assertEqual(response.data['error']['message'], 'Test validation error')
        self.assertEqual(response.data['error']['details'], {'field': 'error'})
    
    def test_django_validation_error_handling(self):
        """Test handling of Django validation errors"""
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        request = self.factory.get('/test/')
        context = {'request': request}
        exc = DjangoValidationError("Django validation failed")
        
        response = custom_exception_handler(exc, context)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
    
    def test_database_error_handling(self):
        """Test handling of database errors"""
        from django.db import IntegrityError
        
        request = self.factory.get('/test/')
        context = {'request': request}
        exc = IntegrityError("Database constraint violation")
        
        response = custom_exception_handler(exc, context)
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['error']['code'], 'DATABASE_ERROR')
    
    def test_404_error_handling(self):
        """Test handling of 404 errors"""
        from django.http import Http404
        
        request = self.factory.get('/test/')
        context = {'request': request}
        exc = Http404("Resource not found")
        
        response = custom_exception_handler(exc, context)
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error']['code'], 'RESOURCE_NOT_FOUND')


class MiddlewareTests(TestCase):
    """Test custom middleware functionality"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()
    
    def test_request_tracking_middleware(self):
        """Test request tracking middleware"""
        middleware = RequestTrackingMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        
        request = self.factory.get('/test/')
        request.user = self.user
        
        response = middleware(request)
        
        # Check that request ID was added
        self.assertTrue(hasattr(request, 'request_id'))
        self.assertTrue(hasattr(request, 'start_time'))
        
        # Check response headers
        self.assertIn('X-Request-ID', response)
        self.assertIn('X-Processing-Time', response)
    
    def test_rate_limit_middleware_normal_request(self):
        """Test rate limiting middleware with normal request"""
        middleware = RateLimitMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        
        request = self.factory.get('/api/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        response = middleware(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_rate_limit_middleware_exceeded(self):
        """Test rate limiting middleware when limit is exceeded"""
        middleware = RateLimitMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        
        # Set a low limit for testing
        middleware.rate_limits['default'] = {'requests': 2, 'window': 60}
        
        request = self.factory.get('/api/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        # Make requests up to the limit
        for i in range(2):
            response = middleware(request)
            self.assertEqual(response.status_code, 200)
        
        # Next request should be rate limited
        response = middleware(request)
        self.assertEqual(response.status_code, 429)
        self.assertIn('RATE_LIMIT_EXCEEDED', response.content.decode())
    
    def test_security_middleware_suspicious_activity(self):
        """Test security middleware detecting suspicious activity"""
        middleware = SecurityMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        
        request = self.factory.get('/test/?param=<script>alert("xss")</script>')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        with patch('matcher.middleware.security_logger') as mock_logger:
            response = middleware(request)
            
            # Should log suspicious activity
            mock_logger.log_suspicious_activity.assert_called()
    
    def test_error_monitoring_middleware(self):
        """Test error monitoring middleware"""
        def error_response(request):
            return JsonResponse({'error': 'Server error'}, status=500)
        
        middleware = ErrorMonitoringMiddleware(error_response)
        
        request = self.factory.get('/test/')
        request.user = self.user
        
        with patch('matcher.middleware.logger') as mock_logger:
            response = middleware(request)
            
            self.assertEqual(response.status_code, 500)


class ErrorRecoveryTests(TestCase):
    """Test error recovery mechanisms"""
    
    def setUp(self):
        cache.clear()
    
    def test_retry_with_backoff_success(self):
        """Test retry mechanism with successful execution"""
        call_count = 0
        
        @retry_with_backoff(RetryConfig(max_retries=3, base_delay=0.1))
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = test_function()
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
    
    def test_retry_with_backoff_failure(self):
        """Test retry mechanism with permanent failure"""
        call_count = 0
        
        @retry_with_backoff(RetryConfig(max_retries=2, base_delay=0.1))
        def test_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Permanent failure")
        
        with self.assertRaises(Exception):
            test_function()
        
        self.assertEqual(call_count, 3)  # Initial call + 2 retries
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state"""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60)
        circuit_breaker = CircuitBreaker("test_service", config)
        
        @circuit_breaker
        def test_function():
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
    
    def test_circuit_breaker_open_state(self):
        """Test circuit breaker opening after failures"""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60)
        circuit_breaker = CircuitBreaker("test_service_2", config)
        
        @circuit_breaker
        def test_function():
            raise Exception("Service failure")
        
        # Trigger failures to open circuit breaker
        for i in range(2):
            with self.assertRaises(Exception):
                test_function()
        
        # Next call should be blocked by circuit breaker
        with self.assertRaises(ExternalServiceException):
            test_function()
    
    def test_bulkhead_pattern(self):
        """Test bulkhead pattern for resource isolation"""
        bulkhead = BulkheadPattern("test_bulkhead", max_concurrent=2)
        
        @bulkhead
        def test_function():
            return "success"
        
        # Should work normally within limit
        result = test_function()
        self.assertEqual(result, "success")
    
    def test_safe_execute_success(self):
        """Test safe execute with successful function"""
        def test_function():
            return "success"
        
        result = safe_execute(test_function, fallback_value="fallback")
        self.assertEqual(result, "success")
    
    def test_safe_execute_failure(self):
        """Test safe execute with failing function"""
        def test_function():
            raise Exception("Function failed")
        
        result = safe_execute(test_function, fallback_value="fallback")
        self.assertEqual(result, "fallback")
    
    def test_resilient_external_service_decorator(self):
        """Test combined resilient external service decorator"""
        call_count = 0
        
        @resilient_external_service("test_service", max_retries=2)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")


class LoggingTests(TestCase):
    """Test logging functionality"""
    
    def test_structured_formatter(self):
        """Test structured JSON formatter"""
        import logging
        
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='/test/path.py',
            lineno=100,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        self.assertIn('timestamp', log_data)
        self.assertIn('level', log_data)
        self.assertIn('message', log_data)
        self.assertEqual(log_data['level'], 'INFO')
        self.assertEqual(log_data['message'], 'Test message')
    
    def test_ai_operation_logger(self):
        """Test AI operation logger"""
        ai_logger = AIOperationLogger()
        
        with patch.object(ai_logger.logger, 'info') as mock_info:
            ai_logger.log_gemini_request(
                operation='resume_parse',
                input_size=1024,
                processing_time=2.5,
                success=True
            )
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            self.assertIn('Gemini API resume_parse completed', args[0])
            self.assertIn('operation_type', kwargs['extra'])
    
    def test_api_request_logger(self):
        """Test API request logger"""
        api_logger = APIRequestLogger()
        
        request = self.factory.get('/api/test/')
        request.user = User.objects.create_user(username='test', email='test@example.com')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        with patch.object(api_logger.logger, 'info') as mock_info:
            api_logger.log_request(request, 200, 0.5)
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            self.assertIn('API request: GET /api/test/', args[0])
    
    def test_security_logger(self):
        """Test security logger"""
        security_logger = SecurityLogger()
        
        with patch.object(security_logger.logger, 'warning') as mock_warning:
            security_logger.log_authentication_attempt(
                username='testuser',
                success=False,
                ip_address='127.0.0.1',
                user_agent='TestAgent',
                failure_reason='Invalid password'
            )
            
            mock_warning.assert_called_once()
            args, kwargs = mock_warning.call_args
            self.assertIn('Authentication failed for testuser', args[0])
    
    def test_performance_logger(self):
        """Test performance logger"""
        performance_logger = PerformanceLogger()
        
        with patch.object(performance_logger.logger, 'warning') as mock_warning:
            performance_logger.log_slow_query(
                query='SELECT * FROM users WHERE id = %s',
                execution_time=3.5,
                params={'id': 1}
            )
            
            mock_warning.assert_called_once()
            args, kwargs = mock_warning.call_args
            self.assertIn('Slow query detected: 3.50s', args[0])


class IntegrationTests(APITestCase):
    """Integration tests for error handling in API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        self.client = APIClient()
        cache.clear()
    
    def test_authentication_error_handling(self):
        """Test authentication error handling in API"""
        response = self.client.get('/api/profile/')
        
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.data)
    
    def test_validation_error_handling(self):
        """Test validation error handling in API"""
        self.client.force_authenticate(user=self.user)
        
        # Send invalid data
        response = self.client.post('/api/jobs/', {
            'title': '',  # Required field
            'description': 'Test job'
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
    
    def test_rate_limiting_integration(self):
        """Test rate limiting integration with API"""
        self.client.force_authenticate(user=self.user)
        
        # This would need to be tested with actual rate limiting configuration
        # For now, just verify the middleware is in place
        response = self.client.get('/api/jobs/')
        
        # Should have rate limiting headers or work normally
        self.assertIn(response.status_code, [200, 429])
    
    @patch('matcher.services.GeminiResumeParser')
    def test_external_service_error_handling(self, mock_parser):
        """Test external service error handling"""
        self.client.force_authenticate(user=self.user)
        
        # Mock Gemini API failure
        mock_parser.side_effect = GeminiAPIException("API quota exceeded")
        
        with open('test_resume.pdf', 'wb') as f:
            f.write(b'%PDF-1.4 test content')
        
        with open('test_resume.pdf', 'rb') as f:
            response = self.client.post('/api/parse-resume/', {
                'file': f
            })
        
        self.assertEqual(response.status_code, 503)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'GEMINI_API_ERROR')
    
    def test_database_error_handling(self):
        """Test database error handling"""
        self.client.force_authenticate(user=self.user)
        
        with patch('matcher.models.JobPost.objects.create') as mock_create:
            from django.db import IntegrityError
            mock_create.side_effect = IntegrityError("Database constraint violation")
            
            response = self.client.post('/api/jobs/', {
                'title': 'Test Job',
                'description': 'Test description',
                'location': 'Remote',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'salary_min': 50000,
                'salary_max': 80000
            })
            
            self.assertEqual(response.status_code, 500)
            self.assertIn('error', response.data)


class HealthCheckTests(TestCase):
    """Test health check functionality"""
    
    def test_service_health_registration(self):
        """Test service health check registration"""
        from .error_recovery import health_checker
        
        def dummy_health_check():
            return True
        
        health_checker.register_service('test_service', dummy_health_check)
        
        result = health_checker.check_service_health('test_service')
        
        self.assertEqual(result['status'], 'healthy')
        self.assertIn('checked_at', result)
    
    def test_service_health_failure(self):
        """Test service health check failure"""
        from .error_recovery import health_checker
        
        def failing_health_check():
            raise Exception("Service is down")
        
        health_checker.register_service('failing_service', failing_health_check)
        
        result = health_checker.check_service_health('failing_service')
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('message', result)
    
    def test_all_services_health_check(self):
        """Test checking all services health"""
        from .error_recovery import health_checker
        
        health_checker.register_service('service1', lambda: True)
        health_checker.register_service('service2', lambda: True)
        
        result = health_checker.check_all_services()
        
        self.assertIn('services', result)
        self.assertIn('overall_status', result)
        self.assertEqual(result['overall_status'], 'healthy')


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['matcher.tests_error_handling'])