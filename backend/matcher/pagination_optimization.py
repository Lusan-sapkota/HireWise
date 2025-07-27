"""
Pagination and lazy loading optimization utilities for HireWise backend.
Provides efficient pagination strategies and lazy loading mechanisms.
"""

import logging
from typing import Dict, List, Optional, Any, Type, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

from django.core.paginator import Paginator, Page, EmptyPage, PageNotAnInteger
from django.db.models import QuerySet, Model, Q, Count, Prefetch
from django.db.models.query import QuerySet as QuerySetType
from django.http import Http404
from django.utils import timezone
from django.conf import settings

from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response
from rest_framework import status

from .cache_utils import cache_manager, CACHE_TIMEOUTS

logger = logging.getLogger(__name__)


@dataclass
class PaginationConfig:
    """
    Configuration for pagination behavior.
    """
    page_size: int = 20
    max_page_size: int = 100
    page_size_query_param: str = 'page_size'
    page_query_param: str = 'page'
    cache_timeout: int = CACHE_TIMEOUTS['short']
    enable_caching: bool = True
    enable_count_optimization: bool = True


class OptimizedPageNumberPagination(PageNumberPagination):
    """
    Optimized page number pagination with caching and performance improvements.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def __init__(self, config: Optional[PaginationConfig] = None):
        super().__init__()
        if config:
            self.page_size = config.page_size
            self.max_page_size = config.max_page_size
            self.page_size_query_param = config.page_size_query_param
            self.config = config
        else:
            self.config = PaginationConfig()
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate queryset with optimizations.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None
        
        # Generate cache key for pagination
        cache_key = self._generate_pagination_cache_key(queryset, request, page_size)
        
        # Try to get from cache
        if self.config.enable_caching:
            cached_result = cache_manager.get('pagination', cache_key)
            if cached_result:
                return cached_result['page_data']
        
        # Optimize queryset before pagination
        optimized_queryset = self._optimize_queryset(queryset)
        
        paginator = self._get_optimized_paginator(optimized_queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)
        
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        
        # Cache the result
        if self.config.enable_caching:
            cache_data = {
                'page_data': list(page.object_list),
                'page_info': {
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'current_page': page.number,
                }
            }
            cache_manager.set(
                'pagination', 
                cache_data, 
                self.config.cache_timeout,
                cache_key
            )
        
        return page
    
    def get_paginated_response(self, data):
        """
        Return paginated response with additional metadata.
        """
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_size': self.get_page_size(self.request),
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'results': data,
            'pagination_info': {
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
                'start_index': self.page.start_index(),
                'end_index': self.page.end_index(),
            }
        })
    
    def _generate_pagination_cache_key(self, queryset, request, page_size):
        """
        Generate cache key for pagination.
        """
        import hashlib
        
        # Include query parameters that affect results
        query_params = dict(request.query_params)
        query_params.pop('page', None)  # Don't include page in cache key
        
        # Create hash of queryset and parameters
        cache_components = [
            str(queryset.query),
            str(sorted(query_params.items())),
            str(page_size)
        ]
        
        cache_string = '|'.join(cache_components)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _optimize_queryset(self, queryset):
        """
        Apply optimizations to queryset before pagination.
        """
        # Add select_related and prefetch_related based on model
        model = queryset.model
        
        if hasattr(model, 'get_pagination_optimizations'):
            return model.get_pagination_optimizations(queryset)
        
        # Default optimizations
        return queryset
    
    def _get_optimized_paginator(self, queryset, page_size):
        """
        Get optimized paginator with count optimization.
        """
        if self.config.enable_count_optimization:
            return OptimizedPaginator(queryset, page_size)
        else:
            return Paginator(queryset, page_size)


class OptimizedCursorPagination(CursorPagination):
    """
    Optimized cursor pagination for large datasets.
    """
    page_size = 20
    max_page_size = 100
    ordering = '-created_at'
    cursor_query_param = 'cursor'
    page_size_query_param = 'page_size'
    
    def __init__(self, config: Optional[PaginationConfig] = None):
        super().__init__()
        if config:
            self.page_size = config.page_size
            self.max_page_size = config.max_page_size
            self.config = config
        else:
            self.config = PaginationConfig()
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate queryset using cursor-based pagination.
        """
        # Optimize queryset
        optimized_queryset = self._optimize_queryset(queryset)
        
        return super().paginate_queryset(optimized_queryset, request, view)
    
    def _optimize_queryset(self, queryset):
        """
        Apply optimizations specific to cursor pagination.
        """
        # Ensure ordering field is indexed
        # Add select_related for foreign keys used in ordering
        return queryset


class OptimizedPaginator(Paginator):
    """
    Optimized paginator with smart count estimation.
    """
    
    def __init__(self, object_list, per_page, **kwargs):
        super().__init__(object_list, per_page, **kwargs)
        self._count = None
        self._estimated_count = None
    
    @property
    def count(self):
        """
        Get count with optimization for large datasets.
        """
        if self._count is None:
            # For large datasets, use estimation instead of exact count
            if self._should_use_estimated_count():
                self._count = self._get_estimated_count()
            else:
                self._count = self.object_list.count()
        
        return self._count
    
    def _should_use_estimated_count(self):
        """
        Determine if estimated count should be used.
        """
        # Use estimated count for large tables or complex queries
        try:
            # Quick check with LIMIT 1000
            sample_count = self.object_list[:1000].count()
            return sample_count >= 1000
        except Exception:
            return False
    
    def _get_estimated_count(self):
        """
        Get estimated count using database statistics.
        """
        try:
            from django.db import connection
            
            # Get table name
            table_name = self.object_list.model._meta.db_table
            
            # Use database-specific estimation
            with connection.cursor() as cursor:
                if connection.vendor == 'postgresql':
                    cursor.execute(
                        "SELECT reltuples::BIGINT FROM pg_class WHERE relname = %s",
                        [table_name]
                    )
                    result = cursor.fetchone()
                    if result:
                        return int(result[0])
                
                elif connection.vendor == 'mysql':
                    cursor.execute(
                        "SELECT table_rows FROM information_schema.tables "
                        "WHERE table_name = %s AND table_schema = DATABASE()",
                        [table_name]
                    )
                    result = cursor.fetchone()
                    if result:
                        return int(result[0])
            
            # Fallback to actual count
            return self.object_list.count()
        
        except Exception as e:
            logger.warning(f"Count estimation failed: {e}")
            return self.object_list.count()


class LazyLoadingManager:
    """
    Manages lazy loading of related objects and expensive computations.
    """
    
    @staticmethod
    def lazy_load_related(queryset: QuerySet, relations: List[str]) -> QuerySet:
        """
        Apply lazy loading optimizations for related objects.
        """
        # Use select_related for foreign keys
        foreign_key_relations = []
        many_to_many_relations = []
        
        for relation in relations:
            field = queryset.model._meta.get_field(relation.split('__')[0])
            if field.many_to_many or field.one_to_many:
                many_to_many_relations.append(relation)
            else:
                foreign_key_relations.append(relation)
        
        if foreign_key_relations:
            queryset = queryset.select_related(*foreign_key_relations)
        
        if many_to_many_relations:
            queryset = queryset.prefetch_related(*many_to_many_relations)
        
        return queryset
    
    @staticmethod
    def create_optimized_prefetch(
        relation: str,
        queryset: Optional[QuerySet] = None,
        to_attr: Optional[str] = None
    ) -> Prefetch:
        """
        Create optimized Prefetch object.
        """
        if queryset is None:
            return Prefetch(relation, to_attr=to_attr)
        
        # Optimize the prefetch queryset
        optimized_queryset = LazyLoadingManager._optimize_prefetch_queryset(queryset)
        
        return Prefetch(relation, queryset=optimized_queryset, to_attr=to_attr)
    
    @staticmethod
    def _optimize_prefetch_queryset(queryset: QuerySet) -> QuerySet:
        """
        Optimize queryset used in prefetch.
        """
        # Add common optimizations
        return queryset.select_related().order_by('id')


class InfiniteScrollPagination:
    """
    Pagination for infinite scroll interfaces.
    """
    
    def __init__(self, page_size: int = 20, max_items: int = 1000):
        self.page_size = page_size
        self.max_items = max_items
    
    def paginate_for_infinite_scroll(
        self,
        queryset: QuerySet,
        last_id: Optional[str] = None,
        direction: str = 'next'
    ) -> Dict[str, Any]:
        """
        Paginate queryset for infinite scroll.
        
        Args:
            queryset: Base queryset to paginate
            last_id: ID of last item from previous page
            direction: 'next' or 'previous'
        
        Returns:
            Dictionary with items and pagination info
        """
        # Apply cursor-based filtering
        if last_id:
            if direction == 'next':
                queryset = queryset.filter(id__lt=last_id)
            else:
                queryset = queryset.filter(id__gt=last_id)
        
        # Order by ID descending for consistent pagination
        queryset = queryset.order_by('-id')
        
        # Get one extra item to check if there are more
        items = list(queryset[:self.page_size + 1])
        
        has_more = len(items) > self.page_size
        if has_more:
            items = items[:self.page_size]
        
        # Get first and last IDs for next pagination
        first_id = items[0].id if items else None
        last_id = items[-1].id if items else None
        
        return {
            'items': items,
            'has_more': has_more,
            'first_id': first_id,
            'last_id': last_id,
            'count': len(items),
        }


class PaginationOptimizer:
    """
    Utilities for optimizing pagination performance.
    """
    
    @staticmethod
    def optimize_job_list_pagination(queryset: QuerySet) -> QuerySet:
        """
        Optimize job list queryset for pagination.
        """
        return queryset.select_related(
            'recruiter',
            'recruiter__recruiter_profile'
        ).prefetch_related(
            Prefetch(
                'applications',
                queryset=queryset.model.applications.related.related_model.objects.select_related('job_seeker')
            )
        ).annotate(
            applications_count=Count('applications')
        )
    
    @staticmethod
    def optimize_application_list_pagination(queryset: QuerySet) -> QuerySet:
        """
        Optimize application list queryset for pagination.
        """
        return queryset.select_related(
            'job_seeker',
            'job_seeker__job_seeker_profile',
            'job_post',
            'job_post__recruiter__recruiter_profile',
            'resume'
        )
    
    @staticmethod
    def optimize_user_list_pagination(queryset: QuerySet) -> QuerySet:
        """
        Optimize user list queryset for pagination.
        """
        return queryset.select_related(
            'job_seeker_profile',
            'recruiter_profile'
        ).prefetch_related(
            'user_skills__skill'
        )
    
    @staticmethod
    def get_pagination_stats(queryset: QuerySet, page_size: int) -> Dict[str, Any]:
        """
        Get pagination statistics for performance monitoring.
        """
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            'total_count': total_count,
            'total_pages': total_pages,
            'page_size': page_size,
            'estimated_query_time': total_count * 0.001,  # Rough estimation
        }


# Utility functions

def paginate_queryset(
    queryset: QuerySet,
    page: int = 1,
    page_size: int = 20,
    config: Optional[PaginationConfig] = None
) -> Dict[str, Any]:
    """
    Utility function to paginate any queryset.
    """
    if config is None:
        config = PaginationConfig(page_size=page_size)
    
    paginator = OptimizedPaginator(queryset, config.page_size)
    
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    return {
        'items': list(page_obj.object_list),
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
    }


def create_infinite_scroll_response(
    queryset: QuerySet,
    last_id: Optional[str] = None,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    Create infinite scroll response from queryset.
    """
    paginator = InfiniteScrollPagination(page_size=page_size)
    return paginator.paginate_for_infinite_scroll(queryset, last_id)


def optimize_queryset_for_pagination(queryset: QuerySet, model_name: str) -> QuerySet:
    """
    Apply model-specific optimizations for pagination.
    """
    optimizers = {
        'JobPost': PaginationOptimizer.optimize_job_list_pagination,
        'Application': PaginationOptimizer.optimize_application_list_pagination,
        'User': PaginationOptimizer.optimize_user_list_pagination,
    }
    
    optimizer = optimizers.get(model_name)
    if optimizer:
        return optimizer(queryset)
    
    return queryset


# Performance monitoring

class PaginationMonitor:
    """
    Monitor pagination performance and usage patterns.
    """
    
    @staticmethod
    def log_pagination_performance(
        queryset: QuerySet,
        page_size: int,
        execution_time: float
    ):
        """
        Log pagination performance metrics.
        """
        stats = PaginationOptimizer.get_pagination_stats(queryset, page_size)
        
        logger.info(
            f"Pagination Performance - Model: {queryset.model.__name__}, "
            f"Total Count: {stats['total_count']}, "
            f"Page Size: {page_size}, "
            f"Execution Time: {execution_time:.3f}s"
        )
        
        if execution_time > 2.0:  # Log slow pagination
            logger.warning(
                f"Slow pagination detected - Model: {queryset.model.__name__}, "
                f"Time: {execution_time:.3f}s"
            )
    
    @staticmethod
    def get_pagination_cache_stats() -> Dict[str, Any]:
        """
        Get pagination cache statistics.
        """
        # This would require cache monitoring implementation
        return {
            'cache_hits': 0,
            'cache_misses': 0,
            'hit_rate': 0.0,
        }