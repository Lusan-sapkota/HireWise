"""
API views for advanced search and recommendation system
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import User, JobPost, Application, JobSeekerProfile, RecruiterProfile
from .recommendation_engine import RecommendationEngine, SearchOptimizer, PersonalizedContentDelivery
from .search_analytics import SearchAnalytics, PopularSearchTerms, SearchSuggestions, UserSearchPreferences, SavedSearch
from .serializers import JobPostListSerializer

logger = logging.getLogger(__name__)


class JobRecommendationView(generics.GenericAPIView):
    """
    Get personalized job recommendations for job seekers
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.user_type != 'job_seeker':
            return Response(
                {'error': 'Only job seekers can get job recommendations'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            limit = int(request.GET.get('limit', 20))
            limit = min(limit, 50)  # Cap at 50 recommendations
            
            recommendation_engine = RecommendationEngine()
            recommendations = recommendation_engine.get_job_recommendations_for_user(request.user, limit)
            
            # Format response
            formatted_recommendations = []
            for rec in recommendations:
                job = rec['job']
                formatted_rec = {
                    'job_id': rec['job_id'],
                    'score': rec['score'],
                    'reasons': rec['reasons'],
                    'sources': rec['sources'],
                    'recommendation_type': rec['recommendation_type'],
                    'job': {
                        'id': str(job.id),
                        'title': job.title,
                        'company': job.recruiter.recruiter_profile.company_name if hasattr(job.recruiter, 'recruiter_profile') else 'Unknown',
                        'location': job.location,
                        'remote_work_allowed': job.remote_work_allowed,
                        'job_type': job.job_type,
                        'experience_level': job.experience_level,
                        'salary_min': job.salary_min,
                        'salary_max': job.salary_max,
                        'skills_required': job.skills_required.split(',') if job.skills_required else [],
                        'created_at': job.created_at.isoformat(),
                        'applications_count': job.applications_count,
                        'views_count': job.views_count
                    }
                }
                formatted_recommendations.append(formatted_rec)
            
            return Response({
                'success': True,
                'recommendations': formatted_recommendations,
                'total_count': len(formatted_recommendations),
                'generated_at': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting job recommendations for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to get recommendations', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CandidateRecommendationView(generics.GenericAPIView):
    """
    Get candidate recommendations for job postings (recruiters only)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_id):
        if request.user.user_type != 'recruiter':
            return Response(
                {'error': 'Only recruiters can get candidate recommendations'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Verify job belongs to recruiter
            job_post = JobPost.objects.get(id=job_id, recruiter=request.user)
        except JobPost.DoesNotExist:
            return Response(
                {'error': 'Job post not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            limit = int(request.GET.get('limit', 20))
            limit = min(limit, 50)  # Cap at 50 recommendations
            
            recommendation_engine = RecommendationEngine()
            recommendations = recommendation_engine.get_candidate_recommendations_for_job(job_post, limit)
            
            # Format response
            formatted_recommendations = []
            for rec in recommendations:
                candidate = rec['candidate']
                profile = candidate.job_seeker_profile
                
                formatted_rec = {
                    'candidate_id': rec['candidate_id'],
                    'score': rec['score'],
                    'reasons': rec['reasons'],
                    'sources': rec['sources'],
                    'recommendation_type': rec['recommendation_type'],
                    'candidate': {
                        'id': str(candidate.id),
                        'name': candidate.get_full_name() or candidate.username,
                        'email': candidate.email,
                        'location': profile.location if profile else None,
                        'experience_level': profile.experience_level if profile else None,
                        'current_position': profile.current_position if profile else None,
                        'skills': [skill.skill.name for skill in candidate.user_skills.all()],
                        'availability': profile.availability if profile else True,
                        'resume_count': candidate.resumes.count(),
                        'last_active': candidate.last_login.isoformat() if candidate.last_login else None
                    }
                }
                formatted_recommendations.append(formatted_rec)
            
            return Response({
                'success': True,
                'job_id': str(job_id),
                'job_title': job_post.title,
                'recommendations': formatted_recommendations,
                'total_count': len(formatted_recommendations),
                'generated_at': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting candidate recommendations for job {job_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get recommendations', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdvancedJobSearchView(generics.GenericAPIView):
    """
    Advanced job search with optimization and personalization
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Parse search parameters
            query = request.GET.get('q', '').strip()
            limit = min(int(request.GET.get('limit', 20)), 100)
            offset = int(request.GET.get('offset', 0))
            
            # Parse filters
            filters = {}
            if request.GET.get('location'):
                filters['location'] = request.GET.get('location')
            if request.GET.get('job_type'):
                filters['job_type'] = request.GET.get('job_type')
            if request.GET.get('experience_level'):
                filters['experience_level'] = request.GET.get('experience_level')
            if request.GET.get('salary_min'):
                filters['salary_min'] = int(request.GET.get('salary_min'))
            if request.GET.get('salary_max'):
                filters['salary_max'] = int(request.GET.get('salary_max'))
            if request.GET.get('skills'):
                filters['skills'] = request.GET.get('skills').split(',')
            if request.GET.get('company'):
                filters['company'] = request.GET.get('company')
            if request.GET.get('posted_within_days'):
                filters['posted_within_days'] = int(request.GET.get('posted_within_days'))
            if request.GET.get('include_remote'):
                filters['include_remote'] = request.GET.get('include_remote').lower() == 'true'
            
            # Perform search
            search_optimizer = SearchOptimizer()
            search_results = search_optimizer.search_jobs(
                query=query,
                filters=filters,
                user=request.user if request.user.is_authenticated else None,
                limit=limit,
                offset=offset
            )
            
            # Track search analytics
            if request.user.is_authenticated:
                self._track_search_analytics(request.user, query, filters, len(search_results.get('results', [])))
            
            return Response(search_results, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in advanced job search: {str(e)}")
            return Response(
                {'error': 'Search failed', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _track_search_analytics(self, user, query, filters, result_count):
        """
        Track search analytics for optimization
        """
        try:
            SearchAnalytics.objects.create(
                user=user,
                search_type='jobs',
                query=query,
                filters_applied=filters,
                results_count=result_count
            )
            
            # Update popular search terms
            if query:
                popular_term, created = PopularSearchTerms.objects.get_or_create(
                    search_type='jobs',
                    term=query.lower(),
                    defaults={'search_count': 1}
                )
                if not created:
                    popular_term.search_count += 1
                    popular_term.save()
                    
        except Exception as e:
            logger.error(f"Error tracking search analytics: {str(e)}")


class AdvancedCandidateSearchView(generics.GenericAPIView):
    """
    Advanced candidate search for recruiters
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.user_type != 'recruiter':
            return Response(
                {'error': 'Only recruiters can search candidates'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Parse search parameters
            query = request.GET.get('q', '').strip()
            limit = min(int(request.GET.get('limit', 20)), 100)
            offset = int(request.GET.get('offset', 0))
            
            # Parse filters
            filters = {}
            if request.GET.get('location'):
                filters['location'] = request.GET.get('location')
            if request.GET.get('experience_level'):
                filters['experience_level'] = request.GET.get('experience_level')
            if request.GET.get('skills'):
                filters['skills'] = request.GET.get('skills').split(',')
            if request.GET.get('availability'):
                filters['availability'] = request.GET.get('availability').lower() == 'true'
            if request.GET.get('expected_salary_max'):
                filters['expected_salary_max'] = int(request.GET.get('expected_salary_max'))
            
            # Perform search
            search_optimizer = SearchOptimizer()
            search_results = search_optimizer.search_candidates(
                query=query,
                filters=filters,
                user=request.user,
                limit=limit,
                offset=offset
            )
            
            # Track search analytics
            self._track_search_analytics(request.user, query, filters, len(search_results.get('results', [])))
            
            return Response(search_results, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in advanced candidate search: {str(e)}")
            return Response(
                {'error': 'Search failed', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _track_search_analytics(self, user, query, filters, result_count):
        """
        Track search analytics for optimization
        """
        try:
            SearchAnalytics.objects.create(
                user=user,
                search_type='candidates',
                query=query,
                filters_applied=filters,
                results_count=result_count
            )
            
            # Update popular search terms
            if query:
                popular_term, created = PopularSearchTerms.objects.get_or_create(
                    search_type='candidates',
                    term=query.lower(),
                    defaults={'search_count': 1}
                )
                if not created:
                    popular_term.search_count += 1
                    popular_term.save()
                    
        except Exception as e:
            logger.error(f"Error tracking search analytics: {str(e)}")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def personalized_dashboard_view(request):
    """
    Get personalized dashboard content for users
    """
    try:
        content_delivery = PersonalizedContentDelivery()
        dashboard_data = content_delivery.get_personalized_dashboard(request.user)
        
        return Response({
            'success': True,
            'dashboard': dashboard_data,
            'generated_at': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating personalized dashboard for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Failed to generate dashboard', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def search_suggestions_view(request):
    """
    Get search suggestions for autocomplete
    """
    try:
        query = request.GET.get('q', '').strip()
        search_type = request.GET.get('type', 'jobs')  # 'jobs' or 'candidates'
        suggestion_type = request.GET.get('suggestion_type', 'query')  # 'query', 'skill', 'location', etc.
        limit = min(int(request.GET.get('limit', 10)), 20)
        
        if len(query) < 2:
            return Response({'suggestions': []}, status=status.HTTP_200_OK)
        
        # Get suggestions from database
        suggestions = SearchSuggestions.objects.filter(
            search_type=search_type,
            suggestion_type=suggestion_type,
            text__icontains=query,
            is_active=True
        ).order_by('-popularity_score')[:limit]
        
        suggestion_list = [
            {
                'text': suggestion.text,
                'type': suggestion.suggestion_type,
                'popularity_score': suggestion.popularity_score
            }
            for suggestion in suggestions
        ]
        
        # If no suggestions found, generate some based on popular terms
        if not suggestion_list:
            popular_terms = PopularSearchTerms.objects.filter(
                search_type=search_type,
                term__icontains=query
            ).order_by('-search_count')[:limit]
            
            suggestion_list = [
                {
                    'text': term.term,
                    'type': 'popular',
                    'popularity_score': term.search_count
                }
                for term in popular_terms
            ]
        
        return Response({
            'suggestions': suggestion_list,
            'query': query,
            'search_type': search_type
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting search suggestions: {str(e)}")
        return Response(
            {'error': 'Failed to get suggestions', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def popular_searches_view(request):
    """
    Get popular search terms and trending queries
    """
    try:
        search_type = request.GET.get('type', 'jobs')  # 'jobs' or 'candidates'
        limit = min(int(request.GET.get('limit', 20)), 50)
        days = int(request.GET.get('days', 7))  # Last N days
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Get popular terms from recent searches
        popular_terms = PopularSearchTerms.objects.filter(
            search_type=search_type,
            last_searched__gte=cutoff_date
        ).order_by('-search_count')[:limit]
        
        terms_data = [
            {
                'term': term.term,
                'search_count': term.search_count,
                'click_through_rate': term.click_through_rate,
                'last_searched': term.last_searched.isoformat()
            }
            for term in popular_terms
        ]
        
        return Response({
            'popular_terms': terms_data,
            'search_type': search_type,
            'period_days': days,
            'generated_at': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting popular searches: {str(e)}")
        return Response(
            {'error': 'Failed to get popular searches', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_search_view(request):
    """
    Save a search query for alerts and quick access
    """
    try:
        name = request.data.get('name', '').strip()
        search_type = request.data.get('search_type', 'jobs')
        query = request.data.get('query', '').strip()
        filters = request.data.get('filters', {})
        alerts_enabled = request.data.get('alerts_enabled', True)
        alert_frequency = request.data.get('alert_frequency', 'daily')
        
        if not name:
            return Response(
                {'error': 'Search name is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already has a saved search with this name
        if SavedSearch.objects.filter(user=request.user, name=name).exists():
            return Response(
                {'error': 'A saved search with this name already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create saved search
        saved_search = SavedSearch.objects.create(
            user=request.user,
            name=name,
            search_type=search_type,
            query=query,
            filters=filters,
            alerts_enabled=alerts_enabled,
            alert_frequency=alert_frequency
        )
        
        return Response({
            'success': True,
            'saved_search': {
                'id': str(saved_search.id),
                'name': saved_search.name,
                'search_type': saved_search.search_type,
                'query': saved_search.query,
                'filters': saved_search.filters,
                'alerts_enabled': saved_search.alerts_enabled,
                'alert_frequency': saved_search.alert_frequency,
                'created_at': saved_search.created_at.isoformat()
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error saving search for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Failed to save search', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def saved_searches_view(request):
    """
    Get user's saved searches
    """
    try:
        search_type = request.GET.get('type')  # Optional filter by type
        
        saved_searches = SavedSearch.objects.filter(
            user=request.user,
            is_active=True
        )
        
        if search_type:
            saved_searches = saved_searches.filter(search_type=search_type)
        
        saved_searches = saved_searches.order_by('-created_at')
        
        searches_data = [
            {
                'id': str(search.id),
                'name': search.name,
                'search_type': search.search_type,
                'query': search.query,
                'filters': search.filters,
                'alerts_enabled': search.alerts_enabled,
                'alert_frequency': search.alert_frequency,
                'last_alert_sent': search.last_alert_sent.isoformat() if search.last_alert_sent else None,
                'created_at': search.created_at.isoformat()
            }
            for search in saved_searches
        ]
        
        return Response({
            'saved_searches': searches_data,
            'total_count': len(searches_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting saved searches for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Failed to get saved searches', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_saved_search_view(request, search_id):
    """
    Delete a saved search
    """
    try:
        saved_search = SavedSearch.objects.get(
            id=search_id,
            user=request.user
        )
        saved_search.delete()
        
        return Response({
            'success': True,
            'message': 'Saved search deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except SavedSearch.DoesNotExist:
        return Response(
            {'error': 'Saved search not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error deleting saved search {search_id}: {str(e)}")
        return Response(
            {'error': 'Failed to delete saved search', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_analytics_view(request):
    """
    Get search analytics for the current user
    """
    try:
        days = int(request.GET.get('days', 30))
        search_type = request.GET.get('type')  # Optional filter by type
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        analytics = SearchAnalytics.objects.filter(
            user=request.user,
            searched_at__gte=cutoff_date
        )
        
        if search_type:
            analytics = analytics.filter(search_type=search_type)
        
        analytics = analytics.order_by('-searched_at')
        
        # Aggregate data
        total_searches = analytics.count()
        from django.db.models import Avg
        avg_results = analytics.aggregate(avg_results=Avg('results_count'))['avg_results'] or 0
        
        # Get top queries
        from django.db.models import Count
        top_queries = analytics.values('query').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Recent searches
        recent_searches = analytics[:20]
        
        analytics_data = {
            'period_days': days,
            'total_searches': total_searches,
            'average_results_per_search': round(avg_results, 2),
            'top_queries': [
                {
                    'query': item['query'],
                    'count': item['count']
                }
                for item in top_queries if item['query']
            ],
            'recent_searches': [
                {
                    'query': search.query,
                    'search_type': search.search_type,
                    'results_count': search.results_count,
                    'searched_at': search.searched_at.isoformat()
                }
                for search in recent_searches
            ]
        }
        
        return Response(analytics_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting search analytics for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Failed to get search analytics', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_search_interaction_view(request):
    """
    Track user interactions with search results (clicks, views, etc.)
    """
    try:
        search_id = request.data.get('search_id')
        interaction_type = request.data.get('interaction_type')  # 'click', 'view', 'apply'
        result_id = request.data.get('result_id')
        result_type = request.data.get('result_type')  # 'job', 'candidate'
        
        if not all([search_id, interaction_type, result_id]):
            return Response(
                {'error': 'Missing required fields'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update search analytics with interaction data
        try:
            search_analytics = SearchAnalytics.objects.get(
                id=search_id,
                user=request.user
            )
            
            # Add to clicked results
            if interaction_type == 'click':
                clicked_results = search_analytics.clicked_results or []
                if result_id not in clicked_results:
                    clicked_results.append(result_id)
                    search_analytics.clicked_results = clicked_results
                    search_analytics.save()
            
        except SearchAnalytics.DoesNotExist:
            # If search analytics record doesn't exist, create a basic one
            pass
        
        # Log the interaction for analytics
        logger.info(f"Search interaction - User: {request.user.id}, "
                   f"Type: {interaction_type}, Result: {result_id}")
        
        return Response({
            'success': True,
            'message': 'Interaction tracked successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error tracking search interaction: {str(e)}")
        return Response(
            {'error': 'Failed to track interaction', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )