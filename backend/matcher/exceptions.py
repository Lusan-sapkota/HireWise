"""
Custom exception classes for the HireWise application
"""

from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.db import IntegrityError, DatabaseError
import logging
import traceback

logger = logging.getLogger(__name__)


# Custom Exception Classes
class HireWiseBaseException(Exception):
    """Base exception class for HireWise application"""
    default_message = "An error occurred"
    default_code = "HIREWISE_ERROR"
    default_status = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(self, message=None, code=None, status_code=None, details=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.status_code = status_code or self.default_status
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(HireWiseBaseException):
    """Exception for validation errors"""
    default_message = "Validation failed"
    default_code = "VALIDATION_ERROR"
    default_status = status.HTTP_400_BAD_REQUEST


class AuthenticationException(HireWiseBaseException):
    """Exception for authentication errors"""
    default_message = "Authentication failed"
    default_code = "AUTHENTICATION_ERROR"
    default_status = status.HTTP_401_UNAUTHORIZED


class AuthorizationException(HireWiseBaseException):
    """Exception for authorization errors"""
    default_message = "Access denied"
    default_code = "AUTHORIZATION_ERROR"
    default_status = status.HTTP_403_FORBIDDEN


class ResourceNotFoundException(HireWiseBaseException):
    """Exception for resource not found errors"""
    default_message = "Resource not found"
    default_code = "RESOURCE_NOT_FOUND"
    default_status = status.HTTP_404_NOT_FOUND


class ExternalServiceException(HireWiseBaseException):
    """Exception for external service errors"""
    default_message = "External service unavailable"
    default_code = "EXTERNAL_SERVICE_ERROR"
    default_status = status.HTTP_503_SERVICE_UNAVAILABLE


class GeminiAPIException(ExternalServiceException):
    """Exception for Google Gemini API errors"""
    default_message = "AI service temporarily unavailable"
    default_code = "GEMINI_API_ERROR"


class MLModelException(ExternalServiceException):
    """Exception for ML model errors"""
    default_message = "ML model service unavailable"
    default_code = "ML_MODEL_ERROR"


class FileProcessingException(HireWiseBaseException):
    """Exception for file processing errors"""
    default_message = "File processing failed"
    default_code = "FILE_PROCESSING_ERROR"
    default_status = status.HTTP_400_BAD_REQUEST


class RateLimitException(HireWiseBaseException):
    """Exception for rate limiting"""
    default_message = "Rate limit exceeded"
    default_code = "RATE_LIMIT_EXCEEDED"
    default_status = status.HTTP_429_TOO_MANY_REQUESTS


class DatabaseException(HireWiseBaseException):
    """Exception for database errors"""
    default_message = "Database operation failed"
    default_code = "DATABASE_ERROR"
    default_status = status.HTTP_500_INTERNAL_SERVER_ERROR


class ConfigurationException(HireWiseBaseException):
    """Exception for configuration errors"""
    default_message = "Configuration error"
    default_code = "CONFIGURATION_ERROR"
    default_status = status.HTTP_500_INTERNAL_SERVER_ERROR


# Custom Exception Handler
def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    """
    # Get the standard DRF response
    response = exception_handler(exc, context)
    
    # Get request information for logging
    request = context.get('request')
    view = context.get('view')
    
    # Log the exception
    log_exception(exc, request, view)
    
    # Handle custom exceptions
    if isinstance(exc, HireWiseBaseException):
        custom_response_data = {
            'error': {
                'code': exc.code,
                'message': exc.message,
                'details': exc.details,
                'timestamp': timezone.now().isoformat(),
                'request_id': getattr(request, 'request_id', None) if request else None
            }
        }
        
        return Response(custom_response_data, status=exc.status_code)
    
    # Handle Django validation errors
    elif isinstance(exc, DjangoValidationError):
        custom_response_data = {
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Validation failed',
                'details': {'validation_errors': exc.messages if hasattr(exc, 'messages') else [str(exc)]},
                'timestamp': timezone.now().isoformat(),
                'request_id': getattr(request, 'request_id', None) if request else None
            }
        }
        
        return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle database errors
    elif isinstance(exc, (IntegrityError, DatabaseError)):
        custom_response_data = {
            'error': {
                'code': 'DATABASE_ERROR',
                'message': 'Database operation failed',
                'details': {'database_error': str(exc)} if hasattr(exc, '__str__') else {},
                'timestamp': timezone.now().isoformat(),
                'request_id': getattr(request, 'request_id', None) if request else None
            }
        }
        
        return Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Handle 404 errors
    elif isinstance(exc, Http404):
        custom_response_data = {
            'error': {
                'code': 'RESOURCE_NOT_FOUND',
                'message': 'Resource not found',
                'details': {'resource_error': str(exc)},
                'timestamp': timezone.now().isoformat(),
                'request_id': getattr(request, 'request_id', None) if request else None
            }
        }
        
        return Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)
    
    # Modify standard DRF responses
    if response is not None:
        custom_response_data = {
            'error': {
                'code': get_error_code_from_status(response.status_code),
                'message': get_error_message_from_response(response),
                'details': response.data if isinstance(response.data, dict) else {'error_data': response.data},
                'timestamp': timezone.now().isoformat(),
                'request_id': getattr(request, 'request_id', None) if request else None
            }
        }
        
        response.data = custom_response_data
    
    return response


def log_exception(exc, request=None, view=None):
    """
    Log exception details for monitoring and debugging
    """
    try:
        # Prepare log context
        log_context = {
            'exception_type': type(exc).__name__,
            'exception_message': str(exc),
            'traceback': traceback.format_exc(),
        }
        
        if request:
            log_context.update({
                'request_method': request.method,
                'request_path': request.path,
                'request_user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
                'request_id': getattr(request, 'request_id', None),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'remote_addr': get_client_ip(request),
            })
        
        if view:
            log_context.update({
                'view_class': view.__class__.__name__,
                'view_action': getattr(view, 'action', None),
            })
        
        # Log based on exception type
        if isinstance(exc, HireWiseBaseException):
            if exc.status_code >= 500:
                logger.error(f"HireWise Exception: {exc.message}", extra=log_context)
            else:
                logger.warning(f"HireWise Exception: {exc.message}", extra=log_context)
        else:
            logger.error(f"Unhandled Exception: {str(exc)}", extra=log_context)
            
    except Exception as log_exc:
        # Fallback logging if structured logging fails
        logger.error(f"Exception logging failed: {str(log_exc)}")
        logger.error(f"Original exception: {str(exc)}")


def get_error_code_from_status(status_code):
    """
    Get error code from HTTP status code
    """
    error_codes = {
        400: 'BAD_REQUEST',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        406: 'NOT_ACCEPTABLE',
        409: 'CONFLICT',
        410: 'GONE',
        413: 'PAYLOAD_TOO_LARGE',
        415: 'UNSUPPORTED_MEDIA_TYPE',
        422: 'UNPROCESSABLE_ENTITY',
        429: 'TOO_MANY_REQUESTS',
        500: 'INTERNAL_SERVER_ERROR',
        501: 'NOT_IMPLEMENTED',
        502: 'BAD_GATEWAY',
        503: 'SERVICE_UNAVAILABLE',
        504: 'GATEWAY_TIMEOUT',
    }
    
    return error_codes.get(status_code, 'UNKNOWN_ERROR')


def get_error_message_from_response(response):
    """
    Extract error message from DRF response
    """
    if hasattr(response, 'data'):
        if isinstance(response.data, dict):
            # Try to get detail message
            if 'detail' in response.data:
                return str(response.data['detail'])
            # Try to get first error message
            for key, value in response.data.items():
                if isinstance(value, list) and value:
                    return str(value[0])
                elif isinstance(value, str):
                    return value
        elif isinstance(response.data, list) and response.data:
            return str(response.data[0])
        elif isinstance(response.data, str):
            return response.data
    
    # Fallback to status text
    return getattr(response, 'status_text', 'An error occurred')


def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Error Recovery Utilities
class ErrorRecovery:
    """
    Utilities for error recovery and retry mechanisms
    """
    
    @staticmethod
    def retry_with_backoff(func, max_retries=3, backoff_factor=2, exceptions=(Exception,)):
        """
        Retry function with exponential backoff
        """
        import time
        
        for attempt in range(max_retries):
            try:
                return func()
            except exceptions as e:
                if attempt == max_retries - 1:
                    raise e
                
                wait_time = backoff_factor ** attempt
                logger.warning(f"Retry attempt {attempt + 1} failed, waiting {wait_time}s: {str(e)}")
                time.sleep(wait_time)
    
    @staticmethod
    def safe_execute(func, fallback_value=None, log_errors=True):
        """
        Execute function safely with fallback value
        """
        try:
            return func()
        except Exception as e:
            if log_errors:
                logger.error(f"Safe execution failed: {str(e)}")
            return fallback_value
    
    @staticmethod
    def circuit_breaker(func, failure_threshold=5, recovery_timeout=60):
        """
        Simple circuit breaker pattern implementation
        """
        if not hasattr(circuit_breaker, 'failures'):
            circuit_breaker.failures = {}
            circuit_breaker.last_failure_time = {}
        
        func_name = func.__name__
        current_time = timezone.now().timestamp()
        
        # Check if circuit is open
        if func_name in circuit_breaker.failures:
            if circuit_breaker.failures[func_name] >= failure_threshold:
                last_failure = circuit_breaker.last_failure_time.get(func_name, 0)
                if current_time - last_failure < recovery_timeout:
                    raise ExternalServiceException(
                        message=f"Circuit breaker open for {func_name}",
                        code="CIRCUIT_BREAKER_OPEN"
                    )
                else:
                    # Reset circuit breaker
                    circuit_breaker.failures[func_name] = 0
        
        try:
            result = func()
            # Reset failure count on success
            circuit_breaker.failures[func_name] = 0
            return result
        except Exception as e:
            # Increment failure count
            circuit_breaker.failures[func_name] = circuit_breaker.failures.get(func_name, 0) + 1
            circuit_breaker.last_failure_time[func_name] = current_time
            raise e