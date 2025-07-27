"""
API response caching strategies for HireWise backend.
Provides comprehensive caching for REST API endpoints.
"""

import json
import hashlib
import logging
from typing import Any, Dict, Optional, List, Callable
from functools import wraps
from datetime import timedelta

from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.utils.decorators import method_decorator

from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request

from .cache_utils import cache_manager, CACHE_TIMEOUTS, CACHE_PREFIXES

logger = logging.getLogger(__name__)


class APICacheManager:
    """
    Specialized cache manager for API responses.
    """
    
    @staticmethod
    def generate_api_cache_key(
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        query_params: Optional[Dict] = None,
        path_params: Optional[Dict] = None
    ) -> str:
        """
        Generate consistent cache key for API endpoints.
        """
        key_parts = ['api', endpoint, method.lower()]
        
        if user_id:
            key_parts.append(f"user:{user_id}")
        
        if path_params:
            for key, value in sorted(path_params.items()):
                key_parts.append(f"{key}:{value}")
        
        if query_params:
            # Sort and filter query params for consistent keys
            filtered_params = {
                k: v for k, v in query_params.items()
                if k not in ['timestamp', '_', 'cache_bust']  # Ignore cache-busting params
            }
            if filtered_params:
                params_str = json.dumps(filtered_params, sort_keys=True)
                params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
                key_parts.append(f"params:{params_hash}")
        
        return ':'.join(key_parts)
    
    @staticmethod
    def cache_api_response(
        cache_key: str,
        response_data: Any,
        timeout: int = CACHE_TIMEOUTS['medium'],
        headers: Optional[Dict] = None
    ) -> bool:
        """
        Cache API response with metadata.
        """
        cache_data = {
            'data': response_data,
            'cached_at': timezone.now().isoformat(),
            'headers': headers or {},
        }
        
        return cache.set(cache_key, cache_data, timeout)
    
    @staticmethod
    def get_cached_api_response(cache_key: str) -> Optional[Dict]:
        """
        Get cached API response with metadata.
        """
        return cache.get(cache_key)
    
    @staticmethod
    def invalidate_api_cache_pattern(pattern: str) -> int:
        """
        Invalidate API cache entries matching pattern.
        """
        return cache_manager.delete_pattern(f"api:{pattern}")


def api_cache(
    timeout: int = CACHE_TIMEOUTS['medium'],
    key_func: Optional[Callable] = None,
    vary_on_user: bool = True,
    vary_on_params: List[str] = None,
    cache_anonymous_only: bool = False,
    cache_authenticated_only: bool = False
):
    """
    Decorator for caching API responses.
    
    Args:
        timeout: Cache timeout in seconds
        key_func: Custom function to generate cache key
        vary_on_user: Include user ID in cache key
        vary_on_params: List of query parameters to include in cache key
        cache_anonymous_only: Only cache for anonymous users
        cache_authenticated_only: Only cache for authenticated users
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check caching conditions
            if cache_anonymous_only and request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            if cache_authenticated_only and not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                user_id = str(request.user.id) if vary_on_user and request.user.is_authenticated else None
                
                query_params = dict(request.GET)
                if vary_on_params:
                    query_params = {k: v for k, v in query_params.items() if k in vary_on_params}
                
                cache_key = APICacheManager.generate_api_cache_key(
                    endpoint=request.resolver_match.url_name or 'unknown',
                    method=request.method,
                    user_id=user_id,
                    query_params=query_params,
                    path_params=kwargs
                )
            
            # Try to get from cache
            cached_response = APICacheManager.get_cached_api_response(cache_key)
            if cached_response:
                response = Response(cached_response['data'])
                
                # Add cache headers
                response['X-Cache'] = 'HIT'
                response['X-Cache-Key'] = cache_key
                response['X-Cached-At'] = cached_response['cached_at']
                
                # Add any custom headers
                for header, value in cached_response.get('headers', {}).items():
                    response[header] = value
                
                return response
            
            # Execute view and cache response
            response = view_func(request, *args, **kwargs)
            
            # Only cache successful responses
            if response.status_code == 200:
                headers = {
                    'Content-Type': response.get('Content-Type', 'application/json'),
                }
                
                APICacheManager.cache_api_response(
                    cache_key,
                    response.data,
                    timeout,
                    headers
                )
                
                response['X-Cache'] = 'MISS'
                response['X-Cache-Key'] = cache_key
            
            return response
        
        return wrapper
    return decorator


def conditional_cache(condition_func: Callable):
    """
    Decorator for conditional caching based on custom logic.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not condition_func(request, *args, **kwargs):
                return view_func(request, *args, **kwargs)
            
            # Apply default caching
            return api_cache()(view_func)(request, *args, **kwargs)
        
        return wrapper
    return decorator


class CacheInvalidationManager:
    """
    Manages cache invalidation for different types of data changes.
    """
    
    @staticmethod
    def invalidate_job_caches(job_id: Optional[str] = None, recruiter_id: Optional[str] = None):
        """
        Invalidate job-related API caches.
        """
        patterns = [
            'jobs:*',
            'job-list:*',
            'job-search:*',
            'recommendations:*',
        ]
        
        if job_id:
            patterns.extend([
                f'job-detail:*:{job_id}',
                f'job-analytics:*:{job_id}',
            ])
        
        if recruiter_id:
            patterns.extend([
                f'recruiter-jobs:*:user:{recruiter_id}',
                f'dashboard:*:user:{recruiter_id}',
            ])
        
        for pattern in patterns:
            APICacheManager.invalidate_api_cache_pattern(pattern)
    
    @staticmethod
    def invalidate_user_caches(user_id: str):
        """
        Invalidate user-related API caches.
        """
        patterns = [
            f'*:user:{user_id}',
            f'profile:*:{user_id}',
            f'applications:*:user:{user_id}',
            f'dashboard:*:user:{user_id}',
        ]
        
        for pattern in patterns:
            APICacheManager.invalidate_api_cache_pattern(pattern)
    
    @staticmethod
    def invalidate_application_caches(application_id: str, job_seeker_id: str, recruiter_id: str):
        """
        Invalidate application-related API caches.
        """
        patterns = [
            f'applications:*:user:{job_seeker_id}',
            f'applications:*:user:{recruiter_id}',
            f'dashboard:*:user:{job_seeker_id}',
            f'dashboard:*:user:{recruiter_id}',
            f'analytics:*',
        ]
        
        for pattern in patterns:
            APICacheManager.invalidate_api_cache_pattern(pattern)
    
    @staticmethod
    def invalidate_ai_caches(resume_id: Optional[str] = None, job_id: Optional[str] = None):
        """
        Invalidate AI-related API caches.
        """
        patterns = [
            'match-score:*',
            'recommendations:*',
        ]
        
        if resume_id:
            patterns.append(f'resume-parse:*:{resume_id}')
        
        if job_id:
            patterns.append(f'job-match:*:{job_id}')
        
        for pattern in patterns:
            APICacheManager.invalidate_api_cache_pattern(pattern)


# Specific caching strategies for different endpoints

def cache_job_list(timeout: int = CACHE_TIMEOUTS['short']):
    """
    Cache job list responses with search and filter parameters.
    """
    return api_cache(
        timeout=timeout,
        vary_on_user=False,  # Job lists can be shared
        vary_on_params=['search', 'location', 'job_type', 'experience_level', 'page'],
        cache_anonymous_only=False
    )


def cache_job_detail(timeout: int = CACHE_TIMEOUTS['medium']):
    """
    Cache individual job detail responses.
    """
    return api_cache(
        timeout=timeout,
        vary_on_user=False,  # Job details can be shared
        vary_on_params=[],
    )


def cache_user_profile(timeout: int = CACHE_TIMEOUTS['medium']):
    """
    Cache user profile responses.
    """
    return api_cache(
        timeout=timeout,
        vary_on_user=True,
        cache_authenticated_only=True
    )


def cache_dashboard_data(timeout: int = CACHE_TIMEOUTS['short']):
    """
    Cache dashboard data responses.
    """
    return api_cache(
        timeout=timeout,
        vary_on_user=True,
        cache_authenticated_only=True
    )


def cache_analytics_data(timeout: int = CACHE_TIMEOUTS['medium']):
    """
    Cache analytics data responses.
    """
    return api_cache(
        timeout=timeout,
        vary_on_user=True,
        cache_authenticated_only=True
    )


def cache_skills_list(timeout: int = CACHE_TIMEOUTS['very_long']):
    """
    Cache skills list (rarely changes).
    """
    return api_cache(
        timeout=timeout,
        vary_on_user=False,
        vary_on_params=['category', 'search']
    )


# Cache warming utilities

class APICacheWarmer:
    """
    Utilities for warming up API caches.
    """
    
    @staticmethod
    def warm_job_list_cache():
        """
        Warm up job list cache with common queries.
        """
        from django.test import RequestFactory
        from .views import JobPostViewSet
        
        factory = RequestFactory()
        view = JobPostViewSet()
        
        # Common job list queries to warm up
        common_queries = [
            {},  # Default list
            {'job_type': 'full_time'},
            {'experience_level': 'mid'},
            {'location': 'remote'},
            {'job_type': 'full_time', 'experience_level': 'senior'},
        ]
        
        for query_params in common_queries:
            try:
                request = factory.get('/api/jobs/', query_params)
                request.user = None  # Anonymous request
                
                # This would trigger cache population
                # view.list(request)
                
            except Exception as e:
                logger.error(f"Error warming job list cache: {e}")
    
    @staticmethod
    def warm_skills_cache():
        """
        Warm up skills cache.
        """
        from .models import Skill
        
        try:
            skills = list(Skill.objects.filter(is_verified=True).values(
                'id', 'name', 'category'
            ))
            
            cache_key = APICacheManager.generate_api_cache_key(
                'skills', 'GET'
            )
            
            APICacheManager.cache_api_response(
                cache_key,
                skills,
                CACHE_TIMEOUTS['very_long']
            )
            
        except Exception as e:
            logger.error(f"Error warming skills cache: {e}")


# Cache monitoring and statistics

class APICacheMonitor:
    """
    Monitor API cache performance and statistics.
    """
    
    @staticmethod
    def get_cache_hit_rate(endpoint: str, time_period: timedelta = timedelta(hours=1)) -> float:
        """
        Calculate cache hit rate for specific endpoint.
        """
        # This would require storing cache hit/miss statistics
        # Implementation depends on monitoring infrastructure
        return 0.0
    
    @staticmethod
    def get_most_cached_endpoints() -> List[Dict]:
        """
        Get list of most frequently cached endpoints.
        """
        # This would require cache access statistics
        return []
    
    @staticmethod
    def log_cache_performance():
        """
        Log API cache performance metrics.
        """
        try:
            # Get Redis info if available
            if hasattr(cache, '_cache'):
                info = cache._cache.get_client().info()
                hit_rate = info.get('keyspace_hits', 0) / max(
                    info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1
                ) * 100
                
                logger.info(f"API Cache Performance - Hit Rate: {hit_rate:.2f}%")
        
        except Exception as e:
            logger.error(f"Error logging cache performance: {e}")


# Middleware for automatic cache invalidation

class CacheInvalidationMiddleware:
    """
    Middleware to automatically invalidate caches on data changes.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Invalidate caches on write operations
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and response.status_code < 400:
            self._invalidate_caches_for_request(request, response)
        
        return response
    
    def _invalidate_caches_for_request(self, request, response):
        """
        Invalidate relevant caches based on the request.
        """
        path = request.path
        
        try:
            if '/api/jobs/' in path:
                # Extract job ID if present
                job_id = self._extract_id_from_path(path, 'jobs')
                user_id = str(request.user.id) if request.user.is_authenticated else None
                
                CacheInvalidationManager.invalidate_job_caches(job_id, user_id)
            
            elif '/api/applications/' in path:
                application_id = self._extract_id_from_path(path, 'applications')
                user_id = str(request.user.id) if request.user.is_authenticated else None
                
                if user_id:
                    CacheInvalidationManager.invalidate_application_caches(
                        application_id, user_id, user_id
                    )
            
            elif '/api/profile/' in path or '/api/users/' in path:
                user_id = str(request.user.id) if request.user.is_authenticated else None
                if user_id:
                    CacheInvalidationManager.invalidate_user_caches(user_id)
        
        except Exception as e:
            logger.error(f"Error in cache invalidation middleware: {e}")
    
    def _extract_id_from_path(self, path: str, resource: str) -> Optional[str]:
        """
        Extract resource ID from URL path.
        """
        try:
            parts = path.split('/')
            resource_index = parts.index(resource)
            if resource_index + 1 < len(parts):
                return parts[resource_index + 1]
        except (ValueError, IndexError):
            pass
        
        return None