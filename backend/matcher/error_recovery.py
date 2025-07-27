"""
Error recovery and retry mechanisms for HireWise application
"""

import time
import functools
import random
from typing import Callable, Any, Optional, Tuple, Type, Union, List
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
import logging

from .exceptions import (
    ExternalServiceException, GeminiAPIException, MLModelException,
    DatabaseException, RateLimitException
)
from .logging_config import ai_logger, performance_logger

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry mechanisms"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, backoff_factor: float = 2.0,
                 jitter: bool = True, exceptions: Tuple[Type[Exception], ...] = (Exception,)):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.exceptions = exceptions


class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception


class CircuitBreakerState:
    """Circuit breaker state management"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.cache_key_prefix = f"circuit_breaker:{name}"
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self._execute(func, *args, **kwargs)
        return wrapper
    
    def _execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        state = self._get_state()
        
        if state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._set_state(CircuitBreakerState.HALF_OPEN)
            else:
                raise ExternalServiceException(
                    message=f"Circuit breaker open for {self.name}",
                    code="CIRCUIT_BREAKER_OPEN"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise e
    
    def _get_state(self) -> str:
        """Get current circuit breaker state"""
        return cache.get(f"{self.cache_key_prefix}:state", CircuitBreakerState.CLOSED)
    
    def _set_state(self, state: str):
        """Set circuit breaker state"""
        cache.set(f"{self.cache_key_prefix}:state", state, 3600)  # 1 hour
        
        if state == CircuitBreakerState.OPEN:
            cache.set(f"{self.cache_key_prefix}:opened_at", timezone.now().timestamp(), 3600)
    
    def _get_failure_count(self) -> int:
        """Get current failure count"""
        return cache.get(f"{self.cache_key_prefix}:failures", 0)
    
    def _increment_failure_count(self):
        """Increment failure count"""
        current_count = self._get_failure_count()
        cache.set(f"{self.cache_key_prefix}:failures", current_count + 1, 300)  # 5 minutes
    
    def _reset_failure_count(self):
        """Reset failure count"""
        cache.delete(f"{self.cache_key_prefix}:failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        opened_at = cache.get(f"{self.cache_key_prefix}:opened_at")
        if not opened_at:
            return True
        
        return (timezone.now().timestamp() - opened_at) >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        state = self._get_state()
        if state == CircuitBreakerState.HALF_OPEN:
            self._set_state(CircuitBreakerState.CLOSED)
            self._reset_failure_count()
            logger.info(f"Circuit breaker {self.name} reset to closed state")
    
    def _on_failure(self):
        """Handle failed execution"""
        self._increment_failure_count()
        failure_count = self._get_failure_count()
        
        if failure_count >= self.config.failure_threshold:
            self._set_state(CircuitBreakerState.OPEN)
            logger.warning(f"Circuit breaker {self.name} opened after {failure_count} failures")


def retry_with_backoff(config: RetryConfig):
    """
    Decorator for retry with exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_retries:
                        logger.error(f"Function {func.__name__} failed after {config.max_retries} retries: {str(e)}")
                        raise e
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.backoff_factor ** attempt),
                        config.max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(f"Retry attempt {attempt + 1} for {func.__name__} after {delay:.2f}s: {str(e)}")
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


class BulkheadPattern:
    """
    Bulkhead pattern implementation for resource isolation
    """
    
    def __init__(self, name: str, max_concurrent: int = 10):
        self.name = name
        self.max_concurrent = max_concurrent
        self.cache_key = f"bulkhead:{name}:active"
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self._execute(func, *args, **kwargs)
        return wrapper
    
    def _execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead protection"""
        # Check current active count
        active_count = cache.get(self.cache_key, 0)
        
        if active_count >= self.max_concurrent:
            raise ExternalServiceException(
                message=f"Bulkhead limit exceeded for {self.name}",
                code="BULKHEAD_LIMIT_EXCEEDED"
            )
        
        # Increment active count
        cache.set(self.cache_key, active_count + 1, 300)  # 5 minutes
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Decrement active count
            current_count = cache.get(self.cache_key, 1)
            if current_count > 0:
                cache.set(self.cache_key, current_count - 1, 300)


class TimeoutHandler:
    """
    Timeout handler for long-running operations
    """
    
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {self.timeout_seconds} seconds")
            
            # Set timeout signal
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout_seconds)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Reset signal
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper


class FallbackHandler:
    """
    Fallback handler for graceful degradation
    """
    
    def __init__(self, fallback_func: Callable, exceptions: Tuple[Type[Exception], ...] = (Exception,)):
        self.fallback_func = fallback_func
        self.exceptions = exceptions
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except self.exceptions as e:
                logger.warning(f"Function {func.__name__} failed, using fallback: {str(e)}")
                return self.fallback_func(*args, **kwargs)
        
        return wrapper


# Pre-configured decorators for common use cases
gemini_retry_config = RetryConfig(
    max_retries=3,
    base_delay=2.0,
    max_delay=30.0,
    backoff_factor=2.0,
    exceptions=(GeminiAPIException, ExternalServiceException)
)

ml_model_retry_config = RetryConfig(
    max_retries=2,
    base_delay=1.0,
    max_delay=10.0,
    backoff_factor=2.0,
    exceptions=(MLModelException, ExternalServiceException)
)

database_retry_config = RetryConfig(
    max_retries=3,
    base_delay=0.5,
    max_delay=5.0,
    backoff_factor=1.5,
    exceptions=(DatabaseException,)
)

# Circuit breakers for external services
gemini_circuit_breaker = CircuitBreaker(
    "gemini_api",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=GeminiAPIException
    )
)

ml_model_circuit_breaker = CircuitBreaker(
    "ml_model",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        expected_exception=MLModelException
    )
)

# Bulkheads for resource isolation
gemini_bulkhead = BulkheadPattern("gemini_api", max_concurrent=5)
ml_model_bulkhead = BulkheadPattern("ml_model", max_concurrent=10)
file_processing_bulkhead = BulkheadPattern("file_processing", max_concurrent=3)


class HealthChecker:
    """
    Health checker for external services
    """
    
    def __init__(self):
        self.services = {}
    
    def register_service(self, name: str, health_check_func: Callable[[], bool]):
        """Register a service health check"""
        self.services[name] = health_check_func
    
    def check_service_health(self, service_name: str) -> dict:
        """Check health of a specific service"""
        if service_name not in self.services:
            return {'status': 'unknown', 'message': 'Service not registered'}
        
        try:
            is_healthy = self.services[service_name]()
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'checked_at': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'checked_at': timezone.now().isoformat()
            }
    
    def check_all_services(self) -> dict:
        """Check health of all registered services"""
        results = {}
        for service_name in self.services:
            results[service_name] = self.check_service_health(service_name)
        
        return {
            'services': results,
            'overall_status': 'healthy' if all(
                result['status'] == 'healthy' for result in results.values()
            ) else 'degraded',
            'checked_at': timezone.now().isoformat()
        }


# Global health checker instance
health_checker = HealthChecker()


def safe_execute(func: Callable, fallback_value: Any = None, 
                log_errors: bool = True, error_message: str = None) -> Any:
    """
    Execute function safely with fallback value
    """
    try:
        return func()
    except Exception as e:
        if log_errors:
            error_msg = error_message or f"Safe execution failed for {func.__name__}"
            logger.error(f"{error_msg}: {str(e)}")
        return fallback_value


def with_performance_monitoring(func: Callable) -> Callable:
    """
    Decorator to monitor function performance
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log performance metrics
            performance_logger.log_memory_usage(
                operation=func.__name__,
                memory_usage_mb=0,  # Would need psutil for actual memory monitoring
                peak_memory_mb=0
            )
            
            # Log slow operations
            if execution_time > 5.0:  # Log operations taking more than 5 seconds
                logger.warning(f"Slow operation detected: {func.__name__} took {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {execution_time:.2f}s: {str(e)}")
            raise e
    
    return wrapper


# Convenience decorators combining multiple patterns
def resilient_external_service(service_name: str, max_retries: int = 3, 
                             circuit_breaker_threshold: int = 5):
    """
    Decorator combining retry, circuit breaker, and bulkhead patterns for external services
    """
    def decorator(func: Callable) -> Callable:
        # Apply patterns in order: timeout -> bulkhead -> circuit breaker -> retry -> performance monitoring
        decorated_func = func
        decorated_func = with_performance_monitoring(decorated_func)
        decorated_func = retry_with_backoff(RetryConfig(max_retries=max_retries))(decorated_func)
        decorated_func = CircuitBreaker(
            service_name,
            CircuitBreakerConfig(failure_threshold=circuit_breaker_threshold)
        )(decorated_func)
        decorated_func = BulkheadPattern(service_name)(decorated_func)
        decorated_func = TimeoutHandler(30)(decorated_func)  # 30 second timeout
        
        return decorated_func
    
    return decorator