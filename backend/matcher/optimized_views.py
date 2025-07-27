"""
Optimized views demonstrating the use of caching, query optimization, 
and pagination improvements for HireWise backend.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.cache import cache
from django.http import JsonResponse

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request

from .models import JobPost, Application, User, Resume, Skill
from .serializers import (
    JobPostSerializer, JobPostListSerializer, ApplicationSerializer,
    UserSerializer, SkillSerializer
)
from .cache_utils import cache_manager, JobCacheManager, UserCacheManager
from .query_optimization import OptimizedQueryManager, DatabaseOptimizer
from .api_cache import (
    api_cache, cache_job_list, cache_job_detail, cache_user_profile,
    cache_dashboard_data, cache_analytics_data, cache_skills_list,
    CacheInvalidationManager
)
from .file_optimization import FileUploadManager, process_file_upload
from .pagination_optimization import (
    OptimizedPageNumberPagination, OptimizedCursorPagination,
    InfiniteScrollPagination, PaginationConfig
)

logger = logging.getLogger(__name__)


class OptimizedJobPostViewSet(viewsets.ModelViewSet):
    """
    Optimized JobPost ViewSet with comprehensive caching and query optimization.
    """
    serializer_class = JobPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OptimizedPageNumberPagination
    
    def get_queryset(self):
        """
        Get optimized queryset with proper select_related and prefetch_related.
        """
        queryset = JobPost.objects.filter(is_active=True)
        return JobPost.get_pagination_optimizations(queryset)
    
    def get_serializer_class(self):
        """
        Use different serializers for list vs detail views.
        """
        if self.action == 'list':
            return JobPostListSerializer
        return JobPostSerializer
    
    @cache_job_list(timeout=300)  # 5 minutes cache
    def list(self, request, *args, **kwargs):
        """
        Optimized job list with caching and query optimization.
        """
        # Extract filters from query parameters
        filters = self._extract_filters(request)
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        # Use optimized query manager
        result = OptimizedQueryManager.get_optimized_job_list(
            filters=filters,
            user=request.user,
            page=page,
            page_size=page_size
        )
        
        return Response({
            'results': result['jobs'],
            'count': result['total_count'],
            'next': self._get_next_url(request, result) if result['has_next'] else None,
            'previous': self._get_previous_url(request, result) if result['has_previous'] else None,
            'page_info': {
                'current_page': result['current_page'],
                'total_pages': result['page_count'],
                'page_size': page_size,
            }
        })
    
    @cache_job_detail(timeout=1800)  # 30 minutes cache
    def retrieve(self, request, *args, **kwargs):
        """
        Optimized job detail with caching.
        """
        instance = self.get_object()
        
        # Increment view count asynchronously
        instance.increment_view_count()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Create job post and invalidate related caches.
        """
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_201_CREATED:
            # Invalidate job list caches
            CacheInvalidationManager.invalidate_job_caches(
                recruiter_id=str(request.user.id)
            )
        
        return response
    
    def update(self, request, *args, **kwargs):
        """
        Update job post and invalidate related caches.
        """
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            job_id = str(kwargs.get('pk'))
            CacheInvalidationManager.invalidate_job_caches(
                job_id=job_id,
                recruiter_id=str(request.user.id)
            )
        
        return response
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete job post and invalidate related caches.
        """
        job_id = str(kwargs.get('pk'))
        response = super().destroy(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_204_NO_CONTENT:
            CacheInvalidationManager.invalidate_job_caches(
                job_id=job_id,
                recruiter_id=str(request.user.id)
            )
        
        return response
    
    @action(detail=True, methods=['get'])
    @cache_analytics_data(timeout=900)  # 15 minutes cache
    def analytics(self, request, pk=None):
        """
        Get job analytics with caching.
        """
        job = self.get_object()
        
        # Check permissions
        if job.recruiter != request.user:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        analytics_data = OptimizedQueryManager.get_job_analytics_data(str(job.id))
        return Response(analytics_data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Optimized job search with caching.
        """
        search_query = request.query_params.get('q', '')
        filters = self._extract_filters(request)
        filters['search'] = search_query
        
        # Use cached search if available
        cache_key = f"job_search:{hash(str(filters))}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return Response(cached_result)
        
        # Perform search
        result = OptimizedQueryManager.get_optimized_job_list(
            filters=filters,
            user=request.user,
            page=1,
            page_size=50
        )
        
        # Cache search results for 5 minutes
        cache.set(cache_key, result, 300)
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def infinite_scroll(self, request):
        """
        Infinite scroll pagination for mobile apps.
        """
        last_id = request.query_params.get('last_id')
        page_size = int(request.query_params.get('page_size', 20))
        
        queryset = self.get_queryset()
        filters = self._extract_filters(request)
        
        # Apply filters
        if filters:
            queryset = self._apply_filters(queryset, filters)
        
        # Use infinite scroll pagination
        paginator = InfiniteScrollPagination(page_size=page_size)
        result = paginator.paginate_for_infinite_scroll(
            queryset, last_id=last_id
        )
        
        # Serialize items
        serializer = JobPostListSerializer(result['items'], many=True)
        
        return Response({
            'items': serializer.data,
            'has_more': result['has_more'],
            'last_id': result['last_id'],
            'count': result['count'],
        })
    
    def _extract_filters(self, request) -> Dict[str, Any]:
        """
        Extract and validate filters from request parameters.
        """
        filters = {}
        
        # Search filter
        if search := request.query_params.get('search'):
            filters['search'] = search
        
        # Location filter
        if location := request.query_params.get('location'):
            filters['location'] = location
        
        # Job type filter
        if job_type := request.query_params.get('job_type'):
            filters['job_type'] = job_type
        
        # Experience level filter
        if experience_level := request.query_params.get('experience_level'):
            filters['experience_level'] = experience_level
        
        # Salary filters
        if salary_min := request.query_params.get('salary_min'):
            try:
                filters['salary_min'] = int(salary_min)
            except ValueError:
                pass
        
        if salary_max := request.query_params.get('salary_max'):
            try:
                filters['salary_max'] = int(salary_max)
            except ValueError:
                pass
        
        # Skills filter
        if skills := request.query_params.get('skills'):
            filters['skills'] = skills.split(',')
        
        # Remote work filter
        if request.query_params.get('remote_only') == 'true':
            filters['remote_only'] = True
        
        # Featured jobs filter
        if request.query_params.get('featured_only') == 'true':
            filters['featured_only'] = True
        
        return filters
    
    def _apply_filters(self, queryset, filters):
        """
        Apply filters to queryset (fallback method).
        """
        # This is a simplified version - the OptimizedQueryManager handles this better
        if 'search' in filters:
            queryset = queryset.filter(
                Q(title__icontains=filters['search']) |
                Q(description__icontains=filters['search'])
            )
        
        if 'location' in filters:
            queryset = queryset.filter(location__icontains=filters['location'])
        
        if 'job_type' in filters:
            queryset = queryset.filter(job_type=filters['job_type'])
        
        return queryset
    
    def _get_next_url(self, request, result):
        """Generate next page URL."""
        if result['has_next']:
            next_page = result['current_page'] + 1
            return f"{request.build_absolute_uri()}?page={next_page}"
        return None
    
    def _get_previous_url(self, request, result):
        """Generate previous page URL."""
        if result['has_previous']:
            prev_page = result['current_page'] - 1
            return f"{request.build_absolute_uri()}?page={prev_page}"
        return None


class OptimizedApplicationViewSet(viewsets.ModelViewSet):
    """
    Optimized Application ViewSet with caching and query optimization.
    """
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OptimizedPageNumberPagination
    
    def get_queryset(self):
        """
        Get optimized queryset based on user type.
        """
        user = self.request.user
        
        if user.user_type == 'job_seeker':
            queryset = Application.objects.filter(job_seeker=user)
        elif user.user_type == 'recruiter':
            queryset = Application.objects.filter(job_post__recruiter=user)
        else:
            queryset = Application.objects.none()
        
        return Application.get_pagination_optimizations(queryset)
    
    @api_cache(timeout=300, vary_on_user=True)
    def list(self, request, *args, **kwargs):
        """
        Optimized application list with caching.
        """
        user = request.user
        status_filter = request.query_params.get('status')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        if user.user_type == 'job_seeker':
            result = OptimizedQueryManager.get_optimized_user_applications(
                user_id=str(user.id),
                status_filter=status_filter,
                page=page,
                page_size=page_size
            )
        elif user.user_type == 'recruiter':
            job_id = request.query_params.get('job_id')
            result = OptimizedQueryManager.get_optimized_recruiter_applications(
                recruiter_id=str(user.id),
                job_id=job_id,
                status_filter=status_filter,
                page=page,
                page_size=page_size
            )
        else:
            return Response({'error': 'Invalid user type'}, status=400)
        
        return Response({
            'results': result['applications'],
            'count': result['total_count'],
            'page_info': {
                'current_page': result['current_page'],
                'total_pages': result['page_count'],
                'has_next': result['has_next'],
                'has_previous': result['has_previous'],
            }
        })
    
    def create(self, request, *args, **kwargs):
        """
        Create application and invalidate related caches.
        """
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_201_CREATED:
            # Invalidate application caches
            CacheInvalidationManager.invalidate_application_caches(
                application_id=response.data['id'],
                job_seeker_id=str(request.user.id),
                recruiter_id=str(request.data.get('job_post', {}).get('recruiter', ''))
            )
        
        return response


class OptimizedUserDashboardView(viewsets.GenericViewSet):
    """
    Optimized user dashboard with comprehensive caching.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    @cache_dashboard_data(timeout=300)  # 5 minutes cache
    def dashboard(self, request):
        """
        Get optimized dashboard data for user.
        """
        user = request.user
        dashboard_data = OptimizedQueryManager.get_user_dashboard_data(
            str(user.id), user.user_type
        )
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['post'])
    def upload_resume(self, request):
        """
        Optimized file upload with compression and caching.
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Process file upload with optimization
        result = process_file_upload(
            uploaded_file, 
            str(request.user.id), 
            'resume'
        )
        
        if result['success']:
            # Create Resume object
            resume = Resume.objects.create(
                job_seeker=request.user,
                file=result['file_path'],
                original_filename=result['original_filename'],
                file_size=result['file_size']
            )
            
            # Invalidate user caches
            UserCacheManager.invalidate_user_cache(str(request.user.id))
            
            return Response({
                'id': resume.id,
                'filename': result['original_filename'],
                'file_size': result['file_size'],
                'compression_ratio': result['compression_ratio'],
                'processing_time': result['processing_time'],
            })
        else:
            return Response(
                {'error': result['error']}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class OptimizedSkillsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Optimized skills ViewSet with long-term caching.
    """
    queryset = Skill.objects.filter(is_verified=True)
    serializer_class = SkillSerializer
    permission_classes = [permissions.AllowAny]
    
    @cache_skills_list(timeout=86400)  # 24 hours cache
    def list(self, request, *args, **kwargs):
        """
        Cached skills list (rarely changes).
        """
        category = request.query_params.get('category')
        search = request.query_params.get('search')
        
        queryset = self.get_queryset()
        
        if category:
            queryset = queryset.filter(category=category)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        # Use values() for better performance
        skills = list(queryset.values('id', 'name', 'category', 'description'))
        
        return Response({
            'results': skills,
            'count': len(skills),
        })


# Performance monitoring view
class PerformanceMonitoringView(viewsets.GenericViewSet):
    """
    View for monitoring system performance.
    """
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def cache_stats(self, request):
        """
        Get cache performance statistics.
        """
        from .cache_utils import CacheMonitor
        
        stats = CacheMonitor.get_cache_stats()
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def query_performance(self, request):
        """
        Get database query performance statistics.
        """
        slow_queries = DatabaseOptimizer.analyze_slow_queries()
        query_count = DatabaseOptimizer.get_query_count()
        
        return Response({
            'query_count': query_count,
            'slow_queries': slow_queries[:10],  # Top 10 slow queries
        })
    
    @action(detail=False, methods=['post'])
    def warm_cache(self, request):
        """
        Manually trigger cache warm-up.
        """
        from .cache_utils import warm_cache
        from .api_cache import APICacheWarmer
        
        try:
            warm_cache()
            APICacheWarmer.warm_job_list_cache()
            APICacheWarmer.warm_skills_cache()
            
            return Response({'message': 'Cache warm-up completed successfully'})
        except Exception as e:
            return Response(
                {'error': f'Cache warm-up failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def clear_cache(self, request):
        """
        Clear all application caches.
        """
        from .cache_utils import clear_all_caches
        
        try:
            clear_all_caches()
            return Response({'message': 'All caches cleared successfully'})
        except Exception as e:
            return Response(
                {'error': f'Cache clearing failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )