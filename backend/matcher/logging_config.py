"""
Advanced logging configuration for HireWise application
"""

import logging
import logging.handlers
import json
import uuid
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from typing import Dict, Any, Optional


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs
    """
    
    def format(self, record):
        # Create base log structure
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, default=str)


class RequestContextFilter(logging.Filter):
    """
    Filter that adds request context to log records
    """
    
    def filter(self, record):
        # Try to get current request from thread local storage
        try:
            from threading import current_thread
            thread = current_thread()
            
            if hasattr(thread, 'request'):
                request = thread.request
                record.request_id = getattr(request, 'request_id', None)
                record.user_id = str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None
                record.user_type = getattr(request.user, 'user_type', None) if hasattr(request, 'user') and request.user.is_authenticated else None
                record.request_method = request.method
                record.request_path = request.path
                record.remote_addr = self._get_client_ip(request)
                record.user_agent = request.META.get('HTTP_USER_AGENT', '')[:200]  # Truncate long user agents
        except Exception:
            # If we can't get request context, continue without it
            pass
        
        return True
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AIOperationLogger:
    """
    Specialized logger for AI operations (Gemini API, ML model calls)
    """
    
    def __init__(self):
        self.logger = logging.getLogger('hirewise.ai_operations')
    
    def log_gemini_request(self, operation: str, input_size: int, processing_time: float, 
                          success: bool, error: Optional[str] = None, **kwargs):
        """Log Gemini API request"""
        log_data = {
            'operation_type': 'gemini_api',
            'operation': operation,
            'input_size_bytes': input_size,
            'processing_time_seconds': processing_time,
            'success': success,
            'timestamp': timezone.now().isoformat()
        }
        
        if error:
            log_data['error'] = error
        
        log_data.update(kwargs)
        
        if success:
            self.logger.info(f"Gemini API {operation} completed", extra=log_data)
        else:
            self.logger.error(f"Gemini API {operation} failed", extra=log_data)
    
    def log_ml_model_request(self, model_name: str, operation: str, input_features: int,
                           processing_time: float, success: bool, confidence: Optional[float] = None,
                           error: Optional[str] = None, **kwargs):
        """Log ML model request"""
        log_data = {
            'operation_type': 'ml_model',
            'model_name': model_name,
            'operation': operation,
            'input_features_count': input_features,
            'processing_time_seconds': processing_time,
            'success': success,
            'timestamp': timezone.now().isoformat()
        }
        
        if confidence is not None:
            log_data['confidence_score'] = confidence
        
        if error:
            log_data['error'] = error
        
        log_data.update(kwargs)
        
        if success:
            self.logger.info(f"ML model {operation} completed", extra=log_data)
        else:
            self.logger.error(f"ML model {operation} failed", extra=log_data)
    
    def log_file_processing(self, operation: str, file_name: str, file_size: int,
                          processing_time: float, success: bool, error: Optional[str] = None, **kwargs):
        """Log file processing operations"""
        log_data = {
            'operation_type': 'file_processing',
            'operation': operation,
            'file_name': file_name,
            'file_size_bytes': file_size,
            'processing_time_seconds': processing_time,
            'success': success,
            'timestamp': timezone.now().isoformat()
        }
        
        if error:
            log_data['error'] = error
        
        log_data.update(kwargs)
        
        if success:
            self.logger.info(f"File processing {operation} completed", extra=log_data)
        else:
            self.logger.error(f"File processing {operation} failed", extra=log_data)


class APIRequestLogger:
    """
    Specialized logger for API requests and responses
    """
    
    def __init__(self):
        self.logger = logging.getLogger('hirewise.api_requests')
    
    def log_request(self, request, response_status: int, processing_time: float, **kwargs):
        """Log API request and response"""
        log_data = {
            'request_method': request.method,
            'request_path': request.path,
            'request_query_params': dict(request.GET),
            'response_status': response_status,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'request_id': getattr(request, 'request_id', None),
            'user_id': str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
            'user_type': getattr(request.user, 'user_type', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
            'remote_addr': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
        }
        
        # Add request body size for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            log_data['request_body_size'] = len(request.body) if hasattr(request, 'body') else 0
        
        log_data.update(kwargs)
        
        # Log level based on response status
        if response_status >= 500:
            self.logger.error(f"API request failed: {request.method} {request.path}", extra=log_data)
        elif response_status >= 400:
            self.logger.warning(f"API request error: {request.method} {request.path}", extra=log_data)
        else:
            self.logger.info(f"API request: {request.method} {request.path}", extra=log_data)
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityLogger:
    """
    Specialized logger for security events
    """
    
    def __init__(self):
        self.logger = logging.getLogger('hirewise.security')
    
    def log_authentication_attempt(self, username: str, success: bool, ip_address: str,
                                 user_agent: str, failure_reason: Optional[str] = None):
        """Log authentication attempts"""
        log_data = {
            'event_type': 'authentication_attempt',
            'username': username,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent[:200],
            'timestamp': timezone.now().isoformat()
        }
        
        if failure_reason:
            log_data['failure_reason'] = failure_reason
        
        if success:
            self.logger.info(f"Authentication successful for {username}", extra=log_data)
        else:
            self.logger.warning(f"Authentication failed for {username}", extra=log_data)
    
    def log_authorization_failure(self, user_id: str, resource: str, action: str,
                                ip_address: str, reason: str):
        """Log authorization failures"""
        log_data = {
            'event_type': 'authorization_failure',
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'ip_address': ip_address,
            'reason': reason,
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger.warning(f"Authorization denied for user {user_id}", extra=log_data)
    
    def log_suspicious_activity(self, user_id: Optional[str], activity_type: str,
                              description: str, ip_address: str, severity: str = 'medium'):
        """Log suspicious activities"""
        log_data = {
            'event_type': 'suspicious_activity',
            'user_id': user_id,
            'activity_type': activity_type,
            'description': description,
            'ip_address': ip_address,
            'severity': severity,
            'timestamp': timezone.now().isoformat()
        }
        
        if severity == 'high':
            self.logger.error(f"High severity suspicious activity: {activity_type}", extra=log_data)
        else:
            self.logger.warning(f"Suspicious activity detected: {activity_type}", extra=log_data)
    
    def log_rate_limit_exceeded(self, user_id: Optional[str], endpoint: str, ip_address: str,
                              limit_type: str, current_count: int, limit: int):
        """Log rate limit violations"""
        log_data = {
            'event_type': 'rate_limit_exceeded',
            'user_id': user_id,
            'endpoint': endpoint,
            'ip_address': ip_address,
            'limit_type': limit_type,
            'current_count': current_count,
            'limit': limit,
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger.warning(f"Rate limit exceeded for {endpoint}", extra=log_data)


class PerformanceLogger:
    """
    Logger for performance metrics and monitoring
    """
    
    def __init__(self):
        self.logger = logging.getLogger('hirewise.performance')
    
    def log_slow_query(self, query: str, execution_time: float, params: Optional[Dict] = None):
        """Log slow database queries"""
        log_data = {
            'event_type': 'slow_query',
            'query': query[:500],  # Truncate long queries
            'execution_time_seconds': execution_time,
            'timestamp': timezone.now().isoformat()
        }
        
        if params:
            log_data['query_params'] = params
        
        self.logger.warning(f"Slow query detected: {execution_time:.2f}s", extra=log_data)
    
    def log_memory_usage(self, operation: str, memory_usage_mb: float, peak_memory_mb: float):
        """Log memory usage for operations"""
        log_data = {
            'event_type': 'memory_usage',
            'operation': operation,
            'memory_usage_mb': memory_usage_mb,
            'peak_memory_mb': peak_memory_mb,
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger.info(f"Memory usage for {operation}: {memory_usage_mb:.2f}MB", extra=log_data)
    
    def log_cache_performance(self, cache_key: str, hit: bool, operation_time: float):
        """Log cache hit/miss performance"""
        log_data = {
            'event_type': 'cache_performance',
            'cache_key': cache_key,
            'cache_hit': hit,
            'operation_time_seconds': operation_time,
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger.debug(f"Cache {'hit' if hit else 'miss'} for {cache_key}", extra=log_data)


# Singleton instances for easy access
ai_logger = AIOperationLogger()
api_logger = APIRequestLogger()
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()


def setup_logging():
    """
    Setup logging configuration for the application
    """
    # Ensure log directory exists
    import os
    log_dir = os.path.dirname(settings.LOGGING['handlers']['file']['filename'])
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure structured logging for production
    if not settings.DEBUG:
        # Add structured formatter to file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=settings.LOGGING['handlers']['file']['filename'],
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(StructuredFormatter())
        file_handler.addFilter(RequestContextFilter())
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        
        # Configure application loggers
        for logger_name in ['hirewise.ai_operations', 'hirewise.api_requests', 
                           'hirewise.security', 'hirewise.performance']:
            logger = logging.getLogger(logger_name)
            logger.addHandler(file_handler)
            logger.setLevel(logging.INFO)


# Initialize logging on module import
setup_logging()