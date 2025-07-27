"""
Database query optimization utilities for HireWise backend.
Provides optimized querysets and database performance improvements.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from django.db import models, connection
from django.db.models import (
    Q, F, Count, Avg, Sum, Max, Min, Prefetch, 
    Case, When, Value, IntegerField, FloatField
)
from django.db.models.query import QuerySet
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings

logger = logging.getLogger(__name__)


class OptimizedQueryManager:
    """
    Manager for optimized database queries.
    """
    
    @staticmethod
    def get_optimized_job_list(
        filters: Optional[Dict] = None,
        user=None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get optimized job list with minimal database queries.
        """
        from .models import JobPost
        
        # Base queryset with optimizations
        queryset = JobPost.objects.select_related(
            'recruiter',
            'recruiter__recruiter_profile'
        ).filter(is_active=True)
        
        # Apply filters
        if filters:
            queryset = OptimizedQueryManager._apply_job_filters(queryset, filters, user)
        
        # Add computed fields
        queryset = queryset.annotate(
            company_name=F('recruiter__recruiter_profile__company_name'),
            total_applications=Count('applications'),
            days_since_posted=models.ExpressionWrapper(
                timezone.now() - F('created_at'),
                output_field=models.DurationField()
            )
        )
        
        # Order by relevance and recency
        queryset = queryset.order_by('-is_featured', '-created_at')
        
        # Paginate efficiently
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'jobs': list(page_obj.object_list.values(
                'id', 'title', 'location', 'job_type', 'experience_level',
                'salary_min', 'salary_max', 'created_at', 'company_name',
                'total_applications', 'views_count', 'is_featured'
            )),
            'total_count': paginator.count,
            'page_count': paginator.num_pages,
            'current_page': page,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    
    @staticmethod
    def _apply_job_filters(queryset: QuerySet, filters: Dict, user=None) -> QuerySet:
        """
        Apply filters to job queryset efficiently.
        """
        # Search filter
        if search := filters.get('search'):
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(skills_required__icontains=search) |
                Q(recruiter__recruiter_profile__company_name__icontains=search)
            )
        
        # Location filter
        if location := filters.get('location'):
            queryset = queryset.filter(
                Q(location__icontains=location) |
                Q(remote_work_allowed=True)
            )
        
        # Job type filter
        if job_type := filters.get('job_type'):
            if isinstance(job_type, list):
                queryset = queryset.filter(job_type__in=job_type)
            else:
                queryset = queryset.filter(job_type=job_type)
        
        # Experience level filter
        if experience_level := filters.get('experience_level'):
            if isinstance(experience_level, list):
                queryset = queryset.filter(experience_level__in=experience_level)
            else:
                queryset = queryset.filter(experience_level=experience_level)
        
        # Salary range filter
        if salary_min := filters.get('salary_min'):
            queryset = queryset.filter(
                Q(salary_min__gte=salary_min) | Q(salary_min__isnull=True)
            )
        
        if salary_max := filters.get('salary_max'):
            queryset = queryset.filter(
                Q(salary_max__lte=salary_max) | Q(salary_max__isnull=True)
            )
        
        # Skills filter
        if skills := filters.get('skills'):
            if isinstance(skills, list):
                skills_query = Q()
                for skill in skills:
                    skills_query |= Q(skills_required__icontains=skill)
                queryset = queryset.filter(skills_query)
            else:
                queryset = queryset.filter(skills_required__icontains=skills)
        
        # Date range filter
        if date_from := filters.get('date_from'):
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to := filters.get('date_to'):
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Company filter
        if company := filters.get('company'):
            queryset = queryset.filter(
                recruiter__recruiter_profile__company_name__icontains=company
            )
        
        # Remote work filter
        if filters.get('remote_only'):
            queryset = queryset.filter(remote_work_allowed=True)
        
        # Featured jobs filter
        if filters.get('featured_only'):
            queryset = queryset.filter(is_featured=True)
        
        return queryset
    
    @staticmethod
    def get_optimized_user_applications(
        user_id: str,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get optimized user applications with minimal queries.
        """
        from .models import Application
        
        queryset = Application.objects.select_related(
            'job_post',
            'job_post__recruiter__recruiter_profile',
            'resume'
        ).filter(job_seeker_id=user_id)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Add computed fields
        queryset = queryset.annotate(
            company_name=F('job_post__recruiter__recruiter_profile__company_name'),
            job_title=F('job_post__title'),
            days_since_applied=models.ExpressionWrapper(
                timezone.now() - F('applied_at'),
                output_field=models.DurationField()
            )
        ).order_by('-applied_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'applications': list(page_obj.object_list.values(
                'id', 'status', 'applied_at', 'match_score',
                'job_title', 'company_name', 'job_post_id'
            )),
            'total_count': paginator.count,
            'page_count': paginator.num_pages,
            'current_page': page,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    
    @staticmethod
    def get_optimized_recruiter_applications(
        recruiter_id: str,
        job_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get optimized recruiter applications with minimal queries.
        """
        from .models import Application
        
        queryset = Application.objects.select_related(
            'job_seeker',
            'job_seeker__job_seeker_profile',
            'job_post',
            'resume'
        ).filter(job_post__recruiter_id=recruiter_id)
        
        if job_id:
            queryset = queryset.filter(job_post_id=job_id)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Add computed fields
        queryset = queryset.annotate(
            applicant_name=models.Concat(
                F('job_seeker__first_name'),
                Value(' '),
                F('job_seeker__last_name')
            ),
            job_title=F('job_post__title'),
            days_since_applied=models.ExpressionWrapper(
                timezone.now() - F('applied_at'),
                output_field=models.DurationField()
            )
        ).order_by('-applied_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'applications': list(page_obj.object_list.values(
                'id', 'status', 'applied_at', 'match_score',
                'applicant_name', 'job_title', 'job_seeker_id'
            )),
            'total_count': paginator.count,
            'page_count': paginator.num_pages,
            'current_page': page,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    
    @staticmethod
    def get_job_analytics_data(job_id: str) -> Dict[str, Any]:
        """
        Get comprehensive job analytics with optimized queries.
        """
        from .models import JobPost, Application, JobView
        
        # Single query for job with related data
        job = JobPost.objects.select_related(
            'recruiter__recruiter_profile'
        ).annotate(
            total_applications=Count('applications'),
            pending_applications=Count(
                'applications',
                filter=Q(applications__status='pending')
            ),
            reviewed_applications=Count(
                'applications',
                filter=Q(applications__status='reviewed')
            ),
            avg_match_score=Avg('applications__match_score'),
            total_views=Count('job_views'),
            unique_views=Count('job_views__viewer', distinct=True)
        ).get(id=job_id)
        
        # Get application status distribution
        status_distribution = Application.objects.filter(
            job_post_id=job_id
        ).values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Get recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_stats = Application.objects.filter(
            job_post_id=job_id,
            applied_at__gte=thirty_days_ago
        ).extra(
            select={'day': 'date(applied_at)'}
        ).values('day').annotate(
            applications=Count('id')
        ).order_by('day')
        
        return {
            'job_title': job.title,
            'company_name': job.recruiter.recruiter_profile.company_name,
            'total_applications': job.total_applications,
            'pending_applications': job.pending_applications,
            'reviewed_applications': job.reviewed_applications,
            'avg_match_score': job.avg_match_score or 0,
            'total_views': job.total_views,
            'unique_views': job.unique_views,
            'conversion_rate': (job.total_applications / max(job.total_views, 1)) * 100,
            'status_distribution': list(status_distribution),
            'daily_applications': list(daily_stats),
        }
    
    @staticmethod
    def get_user_dashboard_data(user_id: str, user_type: str) -> Dict[str, Any]:
        """
        Get optimized dashboard data for users.
        """
        if user_type == 'job_seeker':
            return OptimizedQueryManager._get_job_seeker_dashboard(user_id)
        elif user_type == 'recruiter':
            return OptimizedQueryManager._get_recruiter_dashboard(user_id)
        else:
            return {}
    
    @staticmethod
    def _get_job_seeker_dashboard(user_id: str) -> Dict[str, Any]:
        """
        Get job seeker dashboard data with optimized queries.
        """
        from .models import Application, Resume, JobPost
        
        # Single query for application stats
        app_stats = Application.objects.filter(
            job_seeker_id=user_id
        ).aggregate(
            total_applications=Count('id'),
            pending_applications=Count('id', filter=Q(status='pending')),
            reviewed_applications=Count('id', filter=Q(status='reviewed')),
            interview_applications=Count('id', filter=Q(status='interview_scheduled')),
            avg_match_score=Avg('match_score')
        )
        
        # Recent applications
        recent_applications = Application.objects.filter(
            job_seeker_id=user_id
        ).select_related(
            'job_post__recruiter__recruiter_profile'
        ).annotate(
            company_name=F('job_post__recruiter__recruiter_profile__company_name'),
            job_title=F('job_post__title')
        ).order_by('-applied_at')[:5].values(
            'id', 'status', 'applied_at', 'match_score',
            'job_title', 'company_name'
        )
        
        # Resume count
        resume_count = Resume.objects.filter(job_seeker_id=user_id).count()
        
        # Recommended jobs (simplified)
        recommended_jobs = JobPost.objects.filter(
            is_active=True
        ).select_related(
            'recruiter__recruiter_profile'
        ).annotate(
            company_name=F('recruiter__recruiter_profile__company_name')
        ).order_by('-created_at')[:5].values(
            'id', 'title', 'location', 'company_name', 'created_at'
        )
        
        return {
            'stats': app_stats,
            'recent_applications': list(recent_applications),
            'resume_count': resume_count,
            'recommended_jobs': list(recommended_jobs),
        }
    
    @staticmethod
    def _get_recruiter_dashboard(user_id: str) -> Dict[str, Any]:
        """
        Get recruiter dashboard data with optimized queries.
        """
        from .models import JobPost, Application
        
        # Job stats
        job_stats = JobPost.objects.filter(
            recruiter_id=user_id
        ).aggregate(
            total_jobs=Count('id'),
            active_jobs=Count('id', filter=Q(is_active=True)),
            total_applications=Sum('applications_count'),
            total_views=Sum('views_count')
        )
        
        # Application stats
        app_stats = Application.objects.filter(
            job_post__recruiter_id=user_id
        ).aggregate(
            pending_applications=Count('id', filter=Q(status='pending')),
            reviewed_applications=Count('id', filter=Q(status='reviewed')),
            interview_applications=Count('id', filter=Q(status='interview_scheduled')),
            hired_applications=Count('id', filter=Q(status='hired'))
        )
        
        # Recent applications
        recent_applications = Application.objects.filter(
            job_post__recruiter_id=user_id
        ).select_related(
            'job_seeker',
            'job_post'
        ).annotate(
            applicant_name=models.Concat(
                F('job_seeker__first_name'),
                Value(' '),
                F('job_seeker__last_name')
            ),
            job_title=F('job_post__title')
        ).order_by('-applied_at')[:10].values(
            'id', 'status', 'applied_at', 'match_score',
            'applicant_name', 'job_title'
        )
        
        # Top performing jobs
        top_jobs = JobPost.objects.filter(
            recruiter_id=user_id,
            is_active=True
        ).annotate(
            application_count=Count('applications')
        ).order_by('-application_count')[:5].values(
            'id', 'title', 'applications_count', 'views_count', 'created_at'
        )
        
        return {
            'job_stats': job_stats,
            'application_stats': app_stats,
            'recent_applications': list(recent_applications),
            'top_jobs': list(top_jobs),
        }


class DatabaseOptimizer:
    """
    Database optimization utilities and monitoring.
    """
    
    @staticmethod
    def analyze_slow_queries(threshold_seconds: float = 2.0) -> List[Dict]:
        """
        Analyze slow queries from Django's query log.
        """
        from django.db import connection
        
        slow_queries = []
        
        for query in connection.queries:
            time_taken = float(query['time'])
            if time_taken > threshold_seconds:
                slow_queries.append({
                    'sql': query['sql'],
                    'time': time_taken,
                    'timestamp': query.get('timestamp', 'unknown')
                })
        
        return sorted(slow_queries, key=lambda x: x['time'], reverse=True)
    
    @staticmethod
    def get_query_count() -> int:
        """
        Get current query count for the request.
        """
        return len(connection.queries)
    
    @staticmethod
    def log_query_performance():
        """
        Log query performance metrics.
        """
        query_count = DatabaseOptimizer.get_query_count()
        slow_queries = DatabaseOptimizer.analyze_slow_queries()
        
        logger.info(f"Query Performance - Total Queries: {query_count}, "
                   f"Slow Queries: {len(slow_queries)}")
        
        for query in slow_queries[:5]:  # Log top 5 slow queries
            logger.warning(f"Slow Query ({query['time']:.2f}s): {query['sql'][:200]}...")
    
    @staticmethod
    def optimize_queryset_for_api(queryset: QuerySet, fields: List[str]) -> QuerySet:
        """
        Optimize queryset for API responses by selecting only needed fields.
        """
        # Use only() to fetch only required fields
        return queryset.only(*fields)
    
    @staticmethod
    def bulk_create_optimized(model_class, objects: List, batch_size: int = 1000):
        """
        Optimized bulk create with batching.
        """
        total_created = 0
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            created = model_class.objects.bulk_create(batch, ignore_conflicts=True)
            total_created += len(created)
        
        return total_created
    
    @staticmethod
    def bulk_update_optimized(objects: List, fields: List[str], batch_size: int = 1000):
        """
        Optimized bulk update with batching.
        """
        from django.db import models
        
        if not objects:
            return 0
        
        model_class = objects[0].__class__
        total_updated = 0
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            updated = model_class.objects.bulk_update(batch, fields)
            total_updated += updated
        
        return total_updated


# Query optimization decorators
def optimize_queryset(select_related: List[str] = None, prefetch_related: List[str] = None):
    """
    Decorator to optimize queryset with select_related and prefetch_related.
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            queryset = func(self, *args, **kwargs)
            
            if select_related:
                queryset = queryset.select_related(*select_related)
            
            if prefetch_related:
                queryset = queryset.prefetch_related(*prefetch_related)
            
            return queryset
        
        return wrapper
    return decorator


def monitor_queries(func):
    """
    Decorator to monitor query performance.
    """
    def wrapper(*args, **kwargs):
        initial_query_count = DatabaseOptimizer.get_query_count()
        
        result = func(*args, **kwargs)
        
        final_query_count = DatabaseOptimizer.get_query_count()
        query_diff = final_query_count - initial_query_count
        
        if query_diff > 10:  # Log if more than 10 queries
            logger.warning(f"High query count in {func.__name__}: {query_diff} queries")
        
        return result
    
    return wrapper