"""
Custom middleware for error handling, logging, and rate limiting
"""

import time
import uuid
import json
from threading import current_thread
from django.utils import timezone
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from rest_framework import status
import logging

from .logging_config import api_logger, security_logger, performance_logger
from .exceptions import RateLimitException

logger = logging.getLogger(__name__)


class RequestTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track requests and add request ID for logging
    """
    
    def process_request(self, request):
        # Generate unique request ID
        request.request_id = str(uuid.uuid4())
        
        # Store request start time
        request.start_time = time.time()
        
        # Store request in thread local for logging
        current_thread().request = request
        
        return None
    
    def process_response(self, request, response):
        # Calculate processing time
        if hasattr(request, 'start_time'):
            processing_time = time.time() - request.start_time
            
            # Add processing time to response headers
            response['X-Processing-Time'] = f"{processing_time:.3f}s"
            response['X-Request-ID'] = getattr(request, 'request_id', '')
            
            # Log API request
            try:
                api_logger.log_request(
                    request=request,
                    response_status=response.status_code,
                    processing_time=processing_time,
                    response_size=len(response.content) if hasattr(response, 'content') else 0
                )
                
                # Log slow requests
                if processing_time > 2.0:  # Log requests taking more than 2 seconds
                    performance_logger.log_slow_query(
                        query=f"{request.method} {request.path}",
                        execution_time=processing_time,
                        params={'query_params': dict(request.GET)}
                    )
                    
            except Exception as e:
                logger.error(f"Error logging API request: {str(e)}")
        
        # Clean up thread local
        if hasattr(current_thread(), 'request'):
            delattr(current_thread(), 'request')
        
        return response
    
    def process_exception(self, request, exception):
        # Log exception with request context
        if hasattr(request, 'start_time'):
            processing_time = time.time() - request.start_time
            
            logger.error(
                f"Request exception: {str(exception)}",
                extra={
                    'request_id': getattr(request, 'request_id', None),
                    'request_method': request.method,
                    'request_path': request.path,
                    'processing_time': processing_time,
                    'user_id': str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
                    'exception_type': type(exception).__name__
                }
            )
        
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware for rate limiting API requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rate limit configurations
        self.rate_limits = {
            'default': {'requests': 100, 'window': 60},  # 100 requests per minute
            'auth': {'requests': 10, 'window': 60},      # 10 auth requests per minute
            'upload': {'requests': 20, 'window': 60},    # 20 upload requests per minute
            'ai': {'requests': 30, 'window': 60},        # 30 AI requests per minute
        }
        
        # Paths that require special rate limiting
        self.special_paths = {
            '/api/auth/': 'auth',
            '/api/parse-resume/': 'upload',
            '/api/match-score/': 'ai',
            '/api/recommendations/': 'ai',
        }
        
        super().__init__(get_response)
    
    def __call__(self, request):
        # Check rate limit before processing request
        rate_limit_result = self.check_rate_limit(request)
        if rate_limit_result:
            return rate_limit_result
        
        response = self.get_response(request)
        return response
    
    def check_rate_limit(self, request):
        """
        Check if request exceeds rate limit
        """
        try:
            # Skip rate limiting for certain conditions
            if self.should_skip_rate_limiting(request):
                return None
            
            # Determine rate limit type
            limit_type = self.get_rate_limit_type(request)
            limit_config = self.rate_limits.get(limit_type, self.rate_limits['default'])
            
            # Generate cache key
            cache_key = self.generate_cache_key(request, limit_type)
            
            # Get current count from cache
            current_count = cache.get(cache_key, 0)
            
            # Check if limit exceeded
            if current_count >= limit_config['requests']:
                # Log rate limit violation
                security_logger.log_rate_limit_exceeded(
                    user_id=str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
                    endpoint=request.path,
                    ip_address=self.get_client_ip(request),
                    limit_type=limit_type,
                    current_count=current_count,
                    limit=limit_config['requests']
                )
                
                # Return rate limit error response
                return JsonResponse({
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': f'Rate limit exceeded. Maximum {limit_config["requests"]} requests per {limit_config["window"]} seconds.',
                        'details': {
                            'limit': limit_config['requests'],
                            'window_seconds': limit_config['window'],
                            'current_count': current_count,
                            'retry_after': limit_config['window']
                        },
                        'timestamp': timezone.now().isoformat(),
                        'request_id': getattr(request, 'request_id', None)
                    }
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Increment counter
            cache.set(cache_key, current_count + 1, limit_config['window'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error in rate limiting: {str(e)}")
            # Don't block requests if rate limiting fails
            return None
    
    def should_skip_rate_limiting(self, request):
        """
        Determine if rate limiting should be skipped for this request
        """
        # Skip for health checks
        if request.path in ['/health/', '/api/health/']:
            return True
        
        # Skip for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return True
        
        # Skip for admin users in development
        if settings.DEBUG and hasattr(request, 'user') and request.user.is_superuser:
            return True
        
        return False
    
    def get_rate_limit_type(self, request):
        """
        Determine the rate limit type for the request
        """
        for path_prefix, limit_type in self.special_paths.items():
            if request.path.startswith(path_prefix):
                return limit_type
        
        return 'default'
    
    def generate_cache_key(self, request, limit_type):
        """
        Generate cache key for rate limiting
        """
        # Use user ID if authenticated, otherwise use IP address
        if hasattr(request, 'user') and request.user.is_authenticated:
            identifier = f"user:{request.user.id}"
        else:
            identifier = f"ip:{self.get_client_ip(request)}"
        
        return f"rate_limit:{limit_type}:{identifier}"
    
    def get_client_ip(self, request):
        """
        Get client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware for security monitoring and protection
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Suspicious patterns to monitor
        self.suspicious_patterns = [
            'script',
            'javascript:',
            '<script',
            'eval(',
            'document.cookie',
            'union select',
            'drop table',
            '../',
            '..\\',
        ]
        
        super().__init__(get_response)
    
    def __call__(self, request):
        # Check for suspicious activity before processing
        self.check_suspicious_activity(request)
        
        response = self.get_response(request)
        
        # Add security headers
        self.add_security_headers(response)
        
        return response
    
    def check_suspicious_activity(self, request):
        """
        Check for suspicious activity in the request
        """
        try:
            # Check query parameters
            for key, value in request.GET.items():
                if self.contains_suspicious_pattern(value):
                    security_logger.log_suspicious_activity(
                        user_id=str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
                        activity_type='suspicious_query_param',
                        description=f'Suspicious pattern in query parameter {key}: {value[:100]}',
                        ip_address=self.get_client_ip(request),
                        severity='medium'
                    )
            
            # Check POST data
            if request.method == 'POST' and hasattr(request, 'body'):
                try:
                    if request.content_type == 'application/json':
                        body_str = request.body.decode('utf-8')
                        if self.contains_suspicious_pattern(body_str):
                            security_logger.log_suspicious_activity(
                                user_id=str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
                                activity_type='suspicious_post_data',
                                description=f'Suspicious pattern in POST data: {body_str[:100]}',
                                ip_address=self.get_client_ip(request),
                                severity='high'
                            )
                except Exception:
                    pass  # Skip if body can't be decoded
            
            # Check for unusual request patterns
            self.check_unusual_patterns(request)
            
        except Exception as e:
            logger.error(f"Error in security check: {str(e)}")
    
    def contains_suspicious_pattern(self, text):
        """
        Check if text contains suspicious patterns
        """
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in self.suspicious_patterns)
    
    def check_unusual_patterns(self, request):
        """
        Check for unusual request patterns
        """
        # Check for excessive header size
        total_header_size = sum(len(k) + len(v) for k, v in request.META.items())
        if total_header_size > 8192:  # 8KB header limit
            security_logger.log_suspicious_activity(
                user_id=str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
                activity_type='excessive_headers',
                description=f'Request with excessive header size: {total_header_size} bytes',
                ip_address=self.get_client_ip(request),
                severity='medium'
            )
        
        # Check for unusual user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if len(user_agent) > 500 or not user_agent:
            security_logger.log_suspicious_activity(
                user_id=str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
                activity_type='unusual_user_agent',
                description=f'Unusual user agent: {user_agent[:100]}',
                ip_address=self.get_client_ip(request),
                severity='low'
            )
    
    def add_security_headers(self, response):
        """
        Add security headers to response
        """
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Other security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Remove server information
        if 'Server' in response:
            del response['Server']
    
    def get_client_ip(self, request):
        """
        Get client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ErrorMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware for error monitoring and alerting
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Error thresholds for alerting
        self.error_thresholds = {
            'error_rate_5min': 10,    # 10 errors in 5 minutes
            'error_rate_1hour': 50,   # 50 errors in 1 hour
            'critical_errors_5min': 3  # 3 critical errors in 5 minutes
        }
        
        super().__init__(get_response)
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Monitor response for errors
        if response.status_code >= 400:
            self.track_error(request, response)
        
        return response
    
    def process_exception(self, request, exception):
        """
        Process unhandled exceptions
        """
        self.track_exception(request, exception)
        return None
    
    def track_error(self, request, response):
        """
        Track error responses
        """
        try:
            error_key = f"error_tracking:{response.status_code}"
            
            # Increment error counter
            current_count = cache.get(error_key, 0)
            cache.set(error_key, current_count + 1, 300)  # 5 minutes
            
            # Check if we need to alert
            if response.status_code >= 500:
                self.check_critical_error_threshold(request, response)
            else:
                self.check_error_rate_threshold(request, response)
                
        except Exception as e:
            logger.error(f"Error in error tracking: {str(e)}")
    
    def track_exception(self, request, exception):
        """
        Track unhandled exceptions
        """
        try:
            exception_key = f"exception_tracking:{type(exception).__name__}"
            
            # Increment exception counter
            current_count = cache.get(exception_key, 0)
            cache.set(exception_key, current_count + 1, 300)  # 5 minutes
            
            # Always treat unhandled exceptions as critical
            self.send_critical_error_alert(request, exception)
            
        except Exception as e:
            logger.error(f"Error in exception tracking: {str(e)}")
    
    def check_error_rate_threshold(self, request, response):
        """
        Check if error rate exceeds threshold
        """
        error_key = f"error_tracking:{response.status_code}"
        current_count = cache.get(error_key, 0)
        
        if current_count >= self.error_thresholds['error_rate_5min']:
            self.send_error_rate_alert(response.status_code, current_count)
    
    def check_critical_error_threshold(self, request, response):
        """
        Check if critical error rate exceeds threshold
        """
        critical_key = "critical_error_tracking"
        current_count = cache.get(critical_key, 0)
        cache.set(critical_key, current_count + 1, 300)  # 5 minutes
        
        if current_count >= self.error_thresholds['critical_errors_5min']:
            self.send_critical_error_alert(request, f"HTTP {response.status_code}")
    
    def send_error_rate_alert(self, status_code, count):
        """
        Send alert for high error rate
        """
        logger.critical(
            f"High error rate detected: {count} errors with status {status_code} in 5 minutes",
            extra={
                'alert_type': 'high_error_rate',
                'status_code': status_code,
                'error_count': count,
                'threshold': self.error_thresholds['error_rate_5min'],
                'timestamp': timezone.now().isoformat()
            }
        )
    
    def send_critical_error_alert(self, request, error_info):
        """
        Send alert for critical errors
        """
        logger.critical(
            f"Critical error detected: {error_info}",
            extra={
                'alert_type': 'critical_error',
                'error_info': str(error_info),
                'request_path': request.path if request else 'Unknown',
                'request_method': request.method if request else 'Unknown',
                'user_id': str(request.user.id) if request and hasattr(request, 'user') and request.user.is_authenticated else None,
                'timestamp': timezone.now().isoformat()
            }
        )