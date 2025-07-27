"""
Cache utilities for HireWise backend performance optimization.
Provides Redis-based caching for frequently accessed data.
"""

import json
import hashlib
import logging
from typing import Any, Optional, Dict, List, Union
from functools import wraps
from datetime import timedelta

from django.core.cache import cache
from django.conf import settings
from django.db.models import QuerySet
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

logger = logging.getLogger(__name__)

# Cache key prefixes
CACHE_PREFIXES = {
    'job_list': 'jobs:list',
    'job_detail': 'jobs:detail',
    'job_search': 'jobs:search',
    'user_profile': 'users:profile',
    'resume_parse': 'resume:parse',
    'match_score': 'match:score',
    'skills': 'skills:list',
    'analytics': 'analytics',
    'recommendations': 'recommendations',
    'notifications': 'notifications',
}

# Cache timeouts (in seconds)
CACHE_TIMEOUTS = {
    'short': 300,      # 5 minutes
    'medium': 1800,    # 30 minutes
    'long': 3600,      # 1 hour
    'very_long': 86400, # 24 hours
}


class CacheManager:
    """
    Centralized cache management for HireWise backend.
    """
    
    def __init__(self):
        self.cache = cache
        self.default_timeout = CACHE_TIMEOUTS['medium']
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a consistent cache key from prefix and parameters.
        """
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
            else:
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        
        # Add keyword arguments (sorted for consistency)
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        return ':'.join(key_parts)
    
    def get(self, prefix: str, *args, **kwargs) -> Any:
        """
        Get cached value by prefix and parameters.
        """
        cache_key = self._generate_cache_key(prefix, *args, **kwargs)
        try:
            return self.cache.get(cache_key)
        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            return None
    
    def set(self, prefix: str, value: Any, timeout: Optional[int] = None, *args, **kwargs) -> bool:
        """
        Set cached value by prefix and parameters.
        """
        cache_key = self._generate_cache_key(prefix, *args, **kwargs)
        timeout = timeout or self.default_timeout
        
        try:
            return self.cache.set(cache_key, value, timeout)
        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            return False
    
    def delete(self, prefix: str, *args, **kwargs) -> bool:
        """
        Delete cached value by prefix and parameters.
        """
        cache_key = self._generate_cache_key(prefix, *args, **kwargs)
        try:
            return self.cache.delete(cache_key)
        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all cache keys matching a pattern.
        """
        try:
            # This requires django-redis backend
            return self.cache.delete_pattern(pattern)
        except AttributeError:
            logger.warning("Pattern deletion not supported by cache backend")
            return 0
        except Exception as e:
            logger.error(f"Cache pattern delete error for pattern {pattern}: {e}")
            return 0
    
    def get_or_set(self, prefix: str, default_func, timeout: Optional[int] = None, *args, **kwargs) -> Any:
        """
        Get cached value or set it using default function.
        """
        cached_value = self.get(prefix, *args, **kwargs)
        if cached_value is not None:
            return cached_value
        
        # Generate new value
        try:
            new_value = default_func()
            self.set(prefix, new_value, timeout, *args, **kwargs)
            return new_value
        except Exception as e:
            logger.error(f"Error generating cache value for {prefix}: {e}")
            return None


# Global cache manager instance
cache_manager = CacheManager()


def cache_result(prefix: str, timeout: Optional[int] = None, key_args: Optional[List[str]] = None):
    """
    Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix
        timeout: Cache timeout in seconds
        key_args: List of argument names to include in cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key arguments
            cache_args = []
            cache_kwargs = {}
            
            if key_args:
                # Use specific arguments for cache key
                func_kwargs = kwargs.copy()
                for i, arg in enumerate(args):
                    if i < len(key_args):
                        cache_kwargs[key_args[i]] = arg
                
                for key in key_args:
                    if key in func_kwargs:
                        cache_kwargs[key] = func_kwargs[key]
            else:
                # Use all arguments for cache key
                cache_args = args
                cache_kwargs = kwargs
            
            # Try to get from cache
            cached_result = cache_manager.get(prefix, *cache_args, **cache_kwargs)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(prefix, result, timeout, *cache_args, **cache_kwargs)
            return result
        
        return wrapper
    return decorator


class JobCacheManager:
    """
    Specialized cache manager for job-related data.
    """
    
    @staticmethod
    def get_job_list_cache_key(filters: Dict, page: int = 1) -> str:
        """Generate cache key for job list with filters."""
        filter_hash = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:8]
        return f"{CACHE_PREFIXES['job_list']}:{filter_hash}:page:{page}"
    
    @staticmethod
    def cache_job_list(filters: Dict, page: int, data: Any, timeout: int = CACHE_TIMEOUTS['short']):
        """Cache job list results."""
        cache_key = JobCacheManager.get_job_list_cache_key(filters, page)
        cache.set(cache_key, data, timeout)
    
    @staticmethod
    def get_cached_job_list(filters: Dict, page: int = 1) -> Optional[Any]:
        """Get cached job list results."""
        cache_key = JobCacheManager.get_job_list_cache_key(filters, page)
        return cache.get(cache_key)
    
    @staticmethod
    def invalidate_job_caches(job_id: Optional[str] = None):
        """Invalidate job-related caches."""
        patterns_to_clear = [
            f"{CACHE_PREFIXES['job_list']}:*",
            f"{CACHE_PREFIXES['job_search']}:*",
        ]
        
        if job_id:
            patterns_to_clear.append(f"{CACHE_PREFIXES['job_detail']}:{job_id}")
        
        for pattern in patterns_to_clear:
            cache_manager.delete_pattern(pattern)


class UserCacheManager:
    """
    Specialized cache manager for user-related data.
    """
    
    @staticmethod
    def cache_user_profile(user_id: str, profile_data: Dict, timeout: int = CACHE_TIMEOUTS['medium']):
        """Cache user profile data."""
        cache_key = f"{CACHE_PREFIXES['user_profile']}:{user_id}"
        cache.set(cache_key, profile_data, timeout)
    
    @staticmethod
    def get_cached_user_profile(user_id: str) -> Optional[Dict]:
        """Get cached user profile data."""
        cache_key = f"{CACHE_PREFIXES['user_profile']}:{user_id}"
        return cache.get(cache_key)
    
    @staticmethod
    def invalidate_user_cache(user_id: str):
        """Invalidate user-related caches."""
        patterns_to_clear = [
            f"{CACHE_PREFIXES['user_profile']}:{user_id}",
            f"{CACHE_PREFIXES['recommendations']}:{user_id}:*",
            f"{CACHE_PREFIXES['notifications']}:{user_id}:*",
        ]
        
        for pattern in patterns_to_clear:
            cache_manager.delete_pattern(pattern)


class AICacheManager:
    """
    Specialized cache manager for AI-related operations.
    """
    
    @staticmethod
    def cache_resume_parse_result(resume_hash: str, result: Dict, timeout: int = CACHE_TIMEOUTS['very_long']):
        """Cache resume parsing results."""
        cache_key = f"{CACHE_PREFIXES['resume_parse']}:{resume_hash}"
        cache.set(cache_key, result, timeout)
    
    @staticmethod
    def get_cached_resume_parse_result(resume_hash: str) -> Optional[Dict]:
        """Get cached resume parsing results."""
        cache_key = f"{CACHE_PREFIXES['resume_parse']}:{resume_hash}"
        return cache.get(cache_key)
    
    @staticmethod
    def cache_match_score(resume_id: str, job_id: str, score: float, timeout: int = CACHE_TIMEOUTS['long']):
        """Cache match score results."""
        cache_key = f"{CACHE_PREFIXES['match_score']}:{resume_id}:{job_id}"
        cache.set(cache_key, score, timeout)
    
    @staticmethod
    def get_cached_match_score(resume_id: str, job_id: str) -> Optional[float]:
        """Get cached match score results."""
        cache_key = f"{CACHE_PREFIXES['match_score']}:{resume_id}:{job_id}"
        return cache.get(cache_key)
    
    @staticmethod
    def invalidate_ai_caches(resume_id: Optional[str] = None, job_id: Optional[str] = None):
        """Invalidate AI-related caches."""
        patterns_to_clear = []
        
        if resume_id:
            patterns_to_clear.extend([
                f"{CACHE_PREFIXES['resume_parse']}:{resume_id}",
                f"{CACHE_PREFIXES['match_score']}:{resume_id}:*",
            ])
        
        if job_id:
            patterns_to_clear.append(f"{CACHE_PREFIXES['match_score']}:*:{job_id}")
        
        for pattern in patterns_to_clear:
            cache_manager.delete_pattern(pattern)


class AnalyticsCacheManager:
    """
    Specialized cache manager for analytics data.
    """
    
    @staticmethod
    def cache_analytics_data(key: str, data: Dict, timeout: int = CACHE_TIMEOUTS['medium']):
        """Cache analytics data."""
        cache_key = f"{CACHE_PREFIXES['analytics']}:{key}"
        cache.set(cache_key, data, timeout)
    
    @staticmethod
    def get_cached_analytics_data(key: str) -> Optional[Dict]:
        """Get cached analytics data."""
        cache_key = f"{CACHE_PREFIXES['analytics']}:{key}"
        return cache.get(cache_key)
    
    @staticmethod
    def invalidate_analytics_cache(pattern: Optional[str] = None):
        """Invalidate analytics caches."""
        if pattern:
            cache_manager.delete_pattern(f"{CACHE_PREFIXES['analytics']}:{pattern}")
        else:
            cache_manager.delete_pattern(f"{CACHE_PREFIXES['analytics']}:*")


def warm_cache():
    """
    Warm up frequently accessed cache entries.
    """
    logger.info("Starting cache warm-up process")
    
    try:
        from .models import JobPost, Skill
        
        # Warm up skills cache
        skills = list(Skill.objects.filter(is_verified=True).values('id', 'name', 'category'))
        cache_manager.set(CACHE_PREFIXES['skills'], skills, CACHE_TIMEOUTS['very_long'])
        
        # Warm up recent jobs cache
        recent_jobs = JobPost.objects.filter(
            is_active=True,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).select_related('recruiter__recruiter_profile').values(
            'id', 'title', 'location', 'job_type', 'created_at',
            'recruiter__recruiter_profile__company_name'
        )[:50]
        
        JobCacheManager.cache_job_list(
            {'recent': True}, 
            1, 
            list(recent_jobs), 
            CACHE_TIMEOUTS['short']
        )
        
        logger.info("Cache warm-up completed successfully")
        
    except Exception as e:
        logger.error(f"Cache warm-up failed: {e}")


def clear_all_caches():
    """
    Clear all application caches.
    """
    logger.info("Clearing all application caches")
    
    try:
        for prefix in CACHE_PREFIXES.values():
            cache_manager.delete_pattern(f"{prefix}:*")
        
        logger.info("All caches cleared successfully")
        
    except Exception as e:
        logger.error(f"Cache clearing failed: {e}")


# Cache monitoring utilities
class CacheMonitor:
    """
    Monitor cache performance and statistics.
    """
    
    @staticmethod
    def get_cache_stats() -> Dict:
        """Get cache statistics."""
        try:
            # This requires django-redis backend
            stats = cache._cache.get_client().info()
            return {
                'hits': stats.get('keyspace_hits', 0),
                'misses': stats.get('keyspace_misses', 0),
                'hit_rate': stats.get('keyspace_hits', 0) / max(
                    stats.get('keyspace_hits', 0) + stats.get('keyspace_misses', 0), 1
                ) * 100,
                'memory_usage': stats.get('used_memory_human', 'N/A'),
                'connected_clients': stats.get('connected_clients', 0),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    @staticmethod
    def log_cache_performance():
        """Log cache performance metrics."""
        stats = CacheMonitor.get_cache_stats()
        if stats:
            logger.info(f"Cache Performance - Hit Rate: {stats.get('hit_rate', 0):.2f}%, "
                       f"Memory Usage: {stats.get('memory_usage', 'N/A')}")