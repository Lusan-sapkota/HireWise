"""
Advanced recommendation engine for job matching and candidate recommendations.
Implements collaborative filtering, content-based filtering, and hybrid approaches.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import math

from django.db.models import Q, Count, Avg, F, Case, When, Value, IntegerField
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from .models import (
    User, JobPost, Application, Resume, AIAnalysisResult, 
    JobSeekerProfile, RecruiterProfile, JobView, UserSkill, Skill
)

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Main recommendation engine that combines multiple recommendation strategies
    """
    
    def __init__(self):
        self.cache_timeout = getattr(settings, 'RECOMMENDATION_CACHE_TIMEOUT', 3600)  # 1 hour
        self.max_recommendations = getattr(settings, 'MAX_RECOMMENDATIONS', 50)
        
    def get_job_recommendations_for_user(self, user: User, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get personalized job recommendations for a job seeker
        """
        if user.user_type != 'job_seeker':
            return []
        
        cache_key = f"job_recommendations_{user.id}_{limit}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Get user profile and preferences
            profile = getattr(user, 'job_seeker_profile', None)
            if not profile:
                return []
            
            # Combine multiple recommendation strategies
            content_based = self._get_content_based_job_recommendations(user, limit * 2)
            collaborative = self._get_collaborative_job_recommendations(user, limit * 2)
            popularity_based = self._get_popularity_based_job_recommendations(user, limit)
            
            # Merge and rank recommendations
            recommendations = self._merge_job_recommendations(
                content_based, collaborative, popularity_based, limit
            )
            
            # Add recommendation metadata
            for rec in recommendations:
                rec['recommendation_type'] = self._determine_recommendation_type(rec)
                rec['generated_at'] = timezone.now().isoformat()
            
            cache.set(cache_key, recommendations, self.cache_timeout)
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating job recommendations for user {user.id}: {str(e)}")
            return [] 
    def get_candidate_recommendations_for_job(self, job_post: JobPost, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get candidate recommendations for a job posting (for recruiters)
        """
        cache_key = f"candidate_recommendations_{job_post.id}_{limit}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Get candidates based on multiple strategies
            skill_matched = self._get_skill_matched_candidates(job_post, limit * 2)
            experience_matched = self._get_experience_matched_candidates(job_post, limit * 2)
            location_matched = self._get_location_matched_candidates(job_post, limit)
            
            # Merge and rank candidates
            recommendations = self._merge_candidate_recommendations(
                skill_matched, experience_matched, location_matched, limit
            )
            
            # Add recommendation metadata
            for rec in recommendations:
                rec['recommendation_type'] = self._determine_candidate_recommendation_type(rec)
                rec['generated_at'] = timezone.now().isoformat()
            
            cache.set(cache_key, recommendations, self.cache_timeout)
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating candidate recommendations for job {job_post.id}: {str(e)}")
            return []
    
    def _get_content_based_job_recommendations(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """
        Content-based job recommendations based on user profile and skills
        """
        try:
            profile = user.job_seeker_profile
            user_skills = list(user.user_skills.values_list('skill__name', flat=True))
            
            # Build query for matching jobs
            query = Q(is_active=True)
            
            # Exclude jobs user has already applied to
            applied_job_ids = user.applications.values_list('job_post_id', flat=True)
            query &= ~Q(id__in=applied_job_ids)
            
            # Filter by experience level
            if profile.experience_level:
                query &= Q(experience_level=profile.experience_level)
            
            # Filter by location preference (if remote work is not allowed)
            if profile.location:
                query &= Q(
                    Q(location__icontains=profile.location) | 
                    Q(remote_work_allowed=True)
                )
            
            # Get jobs and score them
            jobs = JobPost.objects.filter(query).select_related(
                'recruiter__recruiter_profile'
            ).prefetch_related('applications')[:limit * 3]
            
            recommendations = []
            for job in jobs:
                score = self._calculate_content_based_score(user, job, user_skills)
                if score > 0.3:  # Minimum threshold
                    recommendations.append({
                        'job_id': str(job.id),
                        'job': job,
                        'score': score,
                        'reason': self._generate_content_based_reason(user, job, user_skills)
                    })
            
            # Sort by score and return top results
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error in content-based recommendations: {str(e)}")
            return []
    
    def _get_collaborative_job_recommendations(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """
        Collaborative filtering recommendations based on similar users' behavior
        """
        try:
            # Find similar users based on applications and skills
            similar_users = self._find_similar_users(user, limit=50)
            
            if not similar_users:
                return []
            
            # Get jobs that similar users have applied to or viewed
            similar_user_ids = [u['user_id'] for u in similar_users]
            
            # Jobs applied to by similar users
            applied_jobs = Application.objects.filter(
                job_seeker_id__in=similar_user_ids
            ).values('job_post').annotate(
                application_count=Count('id')
            ).order_by('-application_count')
            
            # Jobs viewed by similar users
            viewed_jobs = JobView.objects.filter(
                viewer_id__in=similar_user_ids
            ).values('job_post').annotate(
                view_count=Count('id')
            ).order_by('-view_count')
            
            # Combine and score
            job_scores = defaultdict(float)
            
            # Score based on applications (higher weight)
            for item in applied_jobs[:limit * 2]:
                job_id = item['job_post']
                job_scores[job_id] += item['application_count'] * 0.7
            
            # Score based on views (lower weight)
            for item in viewed_jobs[:limit * 2]:
                job_id = item['job_post']
                job_scores[job_id] += item['view_count'] * 0.3
            
            # Get job objects and create recommendations
            job_ids = list(job_scores.keys())
            jobs = JobPost.objects.filter(
                id__in=job_ids,
                is_active=True
            ).exclude(
                id__in=user.applications.values_list('job_post_id', flat=True)
            ).select_related('recruiter__recruiter_profile')
            
            recommendations = []
            for job in jobs:
                score = job_scores[job.id] / max(job_scores.values()) if job_scores.values() else 0
                recommendations.append({
                    'job_id': str(job.id),
                    'job': job,
                    'score': score,
                    'reason': f"Users with similar profiles showed interest in this position"
                })
            
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error in collaborative recommendations: {str(e)}")
            return []
    
    def _get_popularity_based_job_recommendations(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """
        Popularity-based recommendations for trending jobs
        """
        try:
            # Get trending jobs based on recent activity
            recent_date = timezone.now() - timedelta(days=7)
            
            trending_jobs = JobPost.objects.filter(
                is_active=True,
                created_at__gte=recent_date
            ).exclude(
                id__in=user.applications.values_list('job_post_id', flat=True)
            ).annotate(
                popularity_score=Count('job_views') + Count('applications') * 2
            ).order_by('-popularity_score').select_related(
                'recruiter__recruiter_profile'
            )[:limit]
            
            recommendations = []
            max_score = trending_jobs.first().popularity_score if trending_jobs else 1
            
            for job in trending_jobs:
                score = job.popularity_score / max_score if max_score > 0 else 0
                recommendations.append({
                    'job_id': str(job.id),
                    'job': job,
                    'score': score,
                    'reason': f"Trending position with {job.popularity_score} recent interactions"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in popularity-based recommendations: {str(e)}")
            return [] 
    def _get_skill_matched_candidates(self, job_post: JobPost, limit: int) -> List[Dict[str, Any]]:
        """
        Find candidates based on skill matching
        """
        try:
            required_skills = [skill.strip().lower() for skill in job_post.skills_required.split(',') if skill.strip()]
            
            if not required_skills:
                return []
            
            # Find users with matching skills
            candidates = User.objects.filter(
                user_type='job_seeker',
                user_skills__skill__name__iregex=r'\b(' + '|'.join(required_skills) + r')\b'
            ).exclude(
                applications__job_post=job_post
            ).annotate(
                skill_match_count=Count('user_skills', distinct=True)
            ).select_related('job_seeker_profile').prefetch_related(
                'user_skills__skill', 'resumes'
            ).order_by('-skill_match_count')[:limit * 2]
            
            recommendations = []
            for candidate in candidates:
                score = self._calculate_skill_match_score(candidate, required_skills)
                if score > 0.2:  # Minimum threshold
                    recommendations.append({
                        'candidate_id': str(candidate.id),
                        'candidate': candidate,
                        'score': score,
                        'reason': self._generate_skill_match_reason(candidate, required_skills)
                    })
            
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error in skill-matched candidates: {str(e)}")
            return []
    
    def _get_experience_matched_candidates(self, job_post: JobPost, limit: int) -> List[Dict[str, Any]]:
        """
        Find candidates based on experience level matching
        """
        try:
            candidates = User.objects.filter(
                user_type='job_seeker',
                job_seeker_profile__experience_level=job_post.experience_level
            ).exclude(
                applications__job_post=job_post
            ).select_related('job_seeker_profile').prefetch_related(
                'user_skills__skill', 'resumes'
            )[:limit * 2]
            
            recommendations = []
            for candidate in candidates:
                score = self._calculate_experience_match_score(candidate, job_post)
                recommendations.append({
                    'candidate_id': str(candidate.id),
                    'candidate': candidate,
                    'score': score,
                    'reason': f"Experience level matches job requirements ({job_post.get_experience_level_display()})"
                })
            
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error in experience-matched candidates: {str(e)}")
            return []
    
    def _get_location_matched_candidates(self, job_post: JobPost, limit: int) -> List[Dict[str, Any]]:
        """
        Find candidates based on location matching
        """
        try:
            query = Q(user_type='job_seeker')
            
            if job_post.remote_work_allowed:
                # For remote jobs, include all candidates
                pass
            else:
                # For non-remote jobs, match location
                query &= Q(job_seeker_profile__location__icontains=job_post.location)
            
            candidates = User.objects.filter(query).exclude(
                applications__job_post=job_post
            ).select_related('job_seeker_profile').prefetch_related(
                'user_skills__skill', 'resumes'
            )[:limit]
            
            recommendations = []
            for candidate in candidates:
                score = 0.8 if job_post.remote_work_allowed else 0.6
                reason = "Available for remote work" if job_post.remote_work_allowed else f"Located in {job_post.location}"
                
                recommendations.append({
                    'candidate_id': str(candidate.id),
                    'candidate': candidate,
                    'score': score,
                    'reason': reason
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in location-matched candidates: {str(e)}")
            return []
    
    def _find_similar_users(self, user: User, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Find users similar to the given user based on skills and application patterns
        """
        try:
            user_skills = set(user.user_skills.values_list('skill__name', flat=True))
            user_applied_jobs = set(user.applications.values_list('job_post__skills_required', flat=True))
            
            # Find users with similar skills
            similar_users = User.objects.filter(
                user_type='job_seeker'
            ).exclude(id=user.id).prefetch_related(
                'user_skills__skill', 'applications__job_post'
            )[:limit * 3]
            
            similarities = []
            for other_user in similar_users:
                other_skills = set(other_user.user_skills.values_list('skill__name', flat=True))
                other_applied_jobs = set(other_user.applications.values_list('job_post__skills_required', flat=True))
                
                # Calculate similarity score
                skill_similarity = self._calculate_jaccard_similarity(user_skills, other_skills)
                job_similarity = self._calculate_jaccard_similarity(user_applied_jobs, other_applied_jobs)
                
                overall_similarity = (skill_similarity * 0.7) + (job_similarity * 0.3)
                
                if overall_similarity > 0.1:  # Minimum threshold
                    similarities.append({
                        'user_id': other_user.id,
                        'similarity': overall_similarity
                    })
            
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar users: {str(e)}")
            return []
    
    def _calculate_jaccard_similarity(self, set1: set, set2: set) -> float:
        """
        Calculate Jaccard similarity between two sets
        """
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0    

    def _calculate_content_based_score(self, user: User, job: JobPost, user_skills: List[str]) -> float:
        """
        Calculate content-based recommendation score
        """
        score = 0.0
        
        # Skill matching (40% weight)
        job_skills = [skill.strip().lower() for skill in job.skills_required.split(',') if skill.strip()]
        user_skills_lower = [skill.lower() for skill in user_skills]
        
        if job_skills:
            skill_matches = sum(1 for skill in job_skills if any(skill in user_skill for user_skill in user_skills_lower))
            skill_score = skill_matches / len(job_skills)
            score += skill_score * 0.4
        
        # Experience level matching (20% weight)
        profile = user.job_seeker_profile
        if profile.experience_level == job.experience_level:
            score += 0.2
        
        # Location matching (15% weight)
        if job.remote_work_allowed or (profile.location and profile.location.lower() in job.location.lower()):
            score += 0.15
        
        # Salary matching (15% weight)
        if profile.expected_salary and job.salary_min and job.salary_max:
            if job.salary_min <= profile.expected_salary <= job.salary_max:
                score += 0.15
            elif profile.expected_salary >= job.salary_min:
                score += 0.1
        
        # Job freshness (10% weight)
        days_old = (timezone.now() - job.created_at).days
        freshness_score = max(0, 1 - (days_old / 30))  # Decay over 30 days
        score += freshness_score * 0.1
        
        return min(score, 1.0)
    
    def _calculate_skill_match_score(self, candidate: User, required_skills: List[str]) -> float:
        """
        Calculate skill match score for candidate recommendation
        """
        candidate_skills = [skill.skill.name.lower() for skill in candidate.user_skills.all().select_related('skill')]
        
        if not required_skills or not candidate_skills:
            return 0.0
        
        matches = sum(1 for req_skill in required_skills 
                     if any(req_skill in cand_skill for cand_skill in candidate_skills))
        
        return matches / len(required_skills)
    
    def _calculate_experience_match_score(self, candidate: User, job_post: JobPost) -> float:
        """
        Calculate experience match score
        """
        profile = candidate.job_seeker_profile
        
        # Base score for exact match
        if profile.experience_level == job_post.experience_level:
            return 0.9
        
        # Partial scores for adjacent levels
        level_order = ['entry', 'mid', 'senior', 'lead']
        
        try:
            candidate_level_idx = level_order.index(profile.experience_level)
            job_level_idx = level_order.index(job_post.experience_level)
            
            level_diff = abs(candidate_level_idx - job_level_idx)
            
            if level_diff == 1:
                return 0.6
            elif level_diff == 2:
                return 0.3
            else:
                return 0.1
        except ValueError:
            return 0.5  # Default score if levels not in standard order
    
    def _merge_job_recommendations(self, content_based: List, collaborative: List, 
                                 popularity_based: List, limit: int) -> List[Dict[str, Any]]:
        """
        Merge and rank job recommendations from different strategies
        """
        job_scores = defaultdict(lambda: {'total_score': 0.0, 'sources': [], 'job': None, 'reasons': []})
        
        # Weight different recommendation types
        weights = {
            'content': 0.5,
            'collaborative': 0.3,
            'popularity': 0.2
        }
        
        # Process content-based recommendations
        for rec in content_based:
            job_id = rec['job_id']
            job_scores[job_id]['total_score'] += rec['score'] * weights['content']
            job_scores[job_id]['sources'].append('content-based')
            job_scores[job_id]['job'] = rec['job']
            job_scores[job_id]['reasons'].append(rec['reason'])
        
        # Process collaborative recommendations
        for rec in collaborative:
            job_id = rec['job_id']
            job_scores[job_id]['total_score'] += rec['score'] * weights['collaborative']
            job_scores[job_id]['sources'].append('collaborative')
            if not job_scores[job_id]['job']:
                job_scores[job_id]['job'] = rec['job']
            job_scores[job_id]['reasons'].append(rec['reason'])
        
        # Process popularity-based recommendations
        for rec in popularity_based:
            job_id = rec['job_id']
            job_scores[job_id]['total_score'] += rec['score'] * weights['popularity']
            job_scores[job_id]['sources'].append('popularity')
            if not job_scores[job_id]['job']:
                job_scores[job_id]['job'] = rec['job']
            job_scores[job_id]['reasons'].append(rec['reason'])
        
        # Convert to final format and sort
        final_recommendations = []
        for job_id, data in job_scores.items():
            final_recommendations.append({
                'job_id': job_id,
                'job': data['job'],
                'score': data['total_score'],
                'sources': list(set(data['sources'])),
                'reasons': data['reasons'][:2]  # Limit to top 2 reasons
            })
        
        final_recommendations.sort(key=lambda x: x['score'], reverse=True)
        return final_recommendations[:limit]
    
    def _merge_candidate_recommendations(self, skill_matched: List, experience_matched: List,
                                       location_matched: List, limit: int) -> List[Dict[str, Any]]:
        """
        Merge and rank candidate recommendations from different strategies
        """
        candidate_scores = defaultdict(lambda: {'total_score': 0.0, 'sources': [], 'candidate': None, 'reasons': []})
        
        # Weight different recommendation types
        weights = {
            'skills': 0.5,
            'experience': 0.3,
            'location': 0.2
        }
        
        # Process skill-matched candidates
        for rec in skill_matched:
            candidate_id = rec['candidate_id']
            candidate_scores[candidate_id]['total_score'] += rec['score'] * weights['skills']
            candidate_scores[candidate_id]['sources'].append('skill-match')
            candidate_scores[candidate_id]['candidate'] = rec['candidate']
            candidate_scores[candidate_id]['reasons'].append(rec['reason'])
        
        # Process experience-matched candidates
        for rec in experience_matched:
            candidate_id = rec['candidate_id']
            candidate_scores[candidate_id]['total_score'] += rec['score'] * weights['experience']
            candidate_scores[candidate_id]['sources'].append('experience-match')
            if not candidate_scores[candidate_id]['candidate']:
                candidate_scores[candidate_id]['candidate'] = rec['candidate']
            candidate_scores[candidate_id]['reasons'].append(rec['reason'])
        
        # Process location-matched candidates
        for rec in location_matched:
            candidate_id = rec['candidate_id']
            candidate_scores[candidate_id]['total_score'] += rec['score'] * weights['location']
            candidate_scores[candidate_id]['sources'].append('location-match')
            if not candidate_scores[candidate_id]['candidate']:
                candidate_scores[candidate_id]['candidate'] = rec['candidate']
            candidate_scores[candidate_id]['reasons'].append(rec['reason'])
        
        # Convert to final format and sort
        final_recommendations = []
        for candidate_id, data in candidate_scores.items():
            final_recommendations.append({
                'candidate_id': candidate_id,
                'candidate': data['candidate'],
                'score': data['total_score'],
                'sources': list(set(data['sources'])),
                'reasons': data['reasons'][:2]  # Limit to top 2 reasons
            })
        
        final_recommendations.sort(key=lambda x: x['score'], reverse=True)
        return final_recommendations[:limit] 
    def _generate_content_based_reason(self, user: User, job: JobPost, user_skills: List[str]) -> str:
        """
        Generate explanation for content-based recommendation
        """
        reasons = []
        
        # Check skill matches
        job_skills = [skill.strip().lower() for skill in job.skills_required.split(',') if skill.strip()]
        user_skills_lower = [skill.lower() for skill in user_skills]
        
        matching_skills = [skill for skill in job_skills if any(skill in user_skill for user_skill in user_skills_lower)]
        if matching_skills:
            reasons.append(f"Matches your skills: {', '.join(matching_skills[:3])}")
        
        # Check experience level
        profile = user.job_seeker_profile
        if profile.experience_level == job.experience_level:
            reasons.append(f"Matches your experience level ({job.get_experience_level_display()})")
        
        # Check location
        if job.remote_work_allowed:
            reasons.append("Remote work available")
        elif profile.location and profile.location.lower() in job.location.lower():
            reasons.append(f"Located in your area ({job.location})")
        
        return "; ".join(reasons[:2]) if reasons else "Good match based on your profile"
    
    def _generate_skill_match_reason(self, candidate: User, required_skills: List[str]) -> str:
        """
        Generate explanation for skill-based candidate recommendation
        """
        candidate_skills = [skill.name.lower() for skill in candidate.user_skills.all().select_related('skill')]
        
        matching_skills = [skill for skill in required_skills 
                          if any(skill in cand_skill for cand_skill in candidate_skills)]
        
        if matching_skills:
            return f"Has required skills: {', '.join(matching_skills[:3])}"
        else:
            return "Skills partially match job requirements"
    
    def _determine_recommendation_type(self, recommendation: Dict[str, Any]) -> str:
        """
        Determine the primary recommendation type based on sources
        """
        sources = recommendation.get('sources', [])
        
        if 'content-based' in sources:
            return 'content-based'
        elif 'collaborative' in sources:
            return 'collaborative'
        elif 'popularity' in sources:
            return 'trending'
        else:
            return 'mixed'
    
    def _determine_candidate_recommendation_type(self, recommendation: Dict[str, Any]) -> str:
        """
        Determine the primary candidate recommendation type based on sources
        """
        sources = recommendation.get('sources', [])
        
        if 'skill-match' in sources:
            return 'skill-based'
        elif 'experience-match' in sources:
            return 'experience-based'
        elif 'location-match' in sources:
            return 'location-based'
        else:
            return 'mixed'


class SearchOptimizer:
    """
    Advanced search optimization and indexing for jobs and candidates
    """
    
    def __init__(self):
        self.cache_timeout = getattr(settings, 'SEARCH_CACHE_TIMEOUT', 1800)  # 30 minutes
    
    def search_jobs(self, query: str, filters: Dict[str, Any] = None, 
                   user: User = None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Advanced job search with optimization and personalization
        """
        try:
            # Build cache key
            cache_key = self._build_search_cache_key('jobs', query, filters, user, limit, offset)
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Build base query
            base_query = Q(is_active=True)
            
            # Apply text search
            if query:
                text_query = self._build_text_search_query(query)
                base_query &= text_query
            
            # Apply filters
            if filters:
                filter_query = self._build_filter_query(filters)
                base_query &= filter_query
            
            # Get jobs with annotations for ranking
            jobs_queryset = JobPost.objects.filter(base_query).select_related(
                'recruiter__recruiter_profile'
            ).annotate(
                relevance_score=self._build_relevance_annotation(query, user),
                popularity_score=Count('job_views') + Count('applications') * 2,
                freshness_score=Case(
                    When(created_at__gte=timezone.now() - timedelta(days=7), then=Value(3)),
                    When(created_at__gte=timezone.now() - timedelta(days=30), then=Value(2)),
                    default=Value(1),
                    output_field=IntegerField()
                )
            ).order_by('-relevance_score', '-popularity_score', '-freshness_score')
            
            # Get total count for pagination
            total_count = jobs_queryset.count()
            
            # Apply pagination
            jobs = jobs_queryset[offset:offset + limit]
            
            # Prepare results
            results = []
            for job in jobs:
                job_data = {
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
                    'relevance_score': getattr(job, 'relevance_score', 0),
                    'popularity_score': getattr(job, 'popularity_score', 0),
                    'applications_count': job.applications_count,
                    'views_count': job.views_count
                }
                
                # Add personalization if user is provided
                if user and user.user_type == 'job_seeker':
                    job_data['personalization'] = self._get_job_personalization(job, user)
                
                results.append(job_data)
            
            # Track search analytics
            self._track_search_analytics(query, filters, user, total_count)
            
            search_result = {
                'results': results,
                'total_count': total_count,
                'page_size': limit,
                'offset': offset,
                'has_next': offset + limit < total_count,
                'search_time': time.time(),
                'query': query,
                'filters_applied': filters or {}
            }
            
            cache.set(cache_key, search_result, self.cache_timeout)
            return search_result
            
        except Exception as e:
            logger.error(f"Error in job search: {str(e)}")
            return {
                'results': [],
                'total_count': 0,
                'page_size': limit,
                'offset': offset,
                'has_next': False,
                'error': str(e)
            } 
    def search_candidates(self, query: str, filters: Dict[str, Any] = None,
                         user: User = None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Advanced candidate search for recruiters
        """
        if user and user.user_type != 'recruiter':
            return {'results': [], 'total_count': 0, 'error': 'Access denied'}
        
        try:
            # Build cache key
            cache_key = self._build_search_cache_key('candidates', query, filters, user, limit, offset)
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Build base query
            base_query = Q(user_type='job_seeker', is_active=True)
            
            # Apply text search
            if query:
                text_query = self._build_candidate_text_search_query(query)
                base_query &= text_query
            
            # Apply filters
            if filters:
                filter_query = self._build_candidate_filter_query(filters)
                base_query &= filter_query
            
            # Get candidates with annotations
            candidates_queryset = User.objects.filter(base_query).select_related(
                'job_seeker_profile'
            ).prefetch_related(
                'user_skills__skill', 'resumes'
            ).annotate(
                profile_completeness=self._build_profile_completeness_annotation(),
                activity_score=Count('job_views') + Count('applications')
            ).order_by('-profile_completeness', '-activity_score')
            
            # Get total count
            total_count = candidates_queryset.count()
            
            # Apply pagination
            candidates = candidates_queryset[offset:offset + limit]
            
            # Prepare results
            results = []
            for candidate in candidates:
                profile = candidate.job_seeker_profile
                candidate_data = {
                    'id': str(candidate.id),
                    'name': candidate.get_full_name() or candidate.username,
                    'email': candidate.email,
                    'location': profile.location if profile else None,
                    'experience_level': profile.experience_level if profile else None,
                    'current_position': profile.current_position if profile else None,
                    'skills': [skill.skill.name for skill in candidate.user_skills.all()],
                    'availability': profile.availability if profile else True,
                    'profile_completeness': getattr(candidate, 'profile_completeness', 0),
                    'activity_score': getattr(candidate, 'activity_score', 0),
                    'resume_count': candidate.resumes.count(),
                    'last_active': candidate.last_login.isoformat() if candidate.last_login else None
                }
                
                results.append(candidate_data)
            
            # Track search analytics
            self._track_search_analytics(query, filters, user, total_count, search_type='candidates')
            
            search_result = {
                'results': results,
                'total_count': total_count,
                'page_size': limit,
                'offset': offset,
                'has_next': offset + limit < total_count,
                'search_time': time.time(),
                'query': query,
                'filters_applied': filters or {}
            }
            
            cache.set(cache_key, search_result, self.cache_timeout)
            return search_result
            
        except Exception as e:
            logger.error(f"Error in candidate search: {str(e)}")
            return {
                'results': [],
                'total_count': 0,
                'page_size': limit,
                'offset': offset,
                'has_next': False,
                'error': str(e)
            }
    
    def _build_text_search_query(self, query: str) -> Q:
        """
        Build text search query for jobs
        """
        search_terms = query.lower().split()
        
        text_query = Q()
        for term in search_terms:
            term_query = (
                Q(title__icontains=term) |
                Q(description__icontains=term) |
                Q(requirements__icontains=term) |
                Q(skills_required__icontains=term) |
                Q(recruiter__recruiter_profile__company_name__icontains=term)
            )
            text_query &= term_query
        
        return text_query
    
    def _build_candidate_text_search_query(self, query: str) -> Q:
        """
        Build text search query for candidates
        """
        search_terms = query.lower().split()
        
        text_query = Q()
        for term in search_terms:
            term_query = (
                Q(first_name__icontains=term) |
                Q(last_name__icontains=term) |
                Q(username__icontains=term) |
                Q(job_seeker_profile__current_position__icontains=term) |
                Q(job_seeker_profile__skills__icontains=term) |
                Q(user_skills__skill__name__icontains=term)
            )
            text_query &= term_query
        
        return text_query
    
    def _build_filter_query(self, filters: Dict[str, Any]) -> Q:
        """
        Build filter query for job search
        """
        filter_query = Q()
        
        if filters.get('location'):
            location_query = Q(location__icontains=filters['location'])
            if filters.get('include_remote', True):
                location_query |= Q(remote_work_allowed=True)
            filter_query &= location_query
        
        if filters.get('job_type'):
            filter_query &= Q(job_type=filters['job_type'])
        
        if filters.get('experience_level'):
            filter_query &= Q(experience_level=filters['experience_level'])
        
        if filters.get('salary_min'):
            filter_query &= Q(salary_max__gte=filters['salary_min'])
        
        if filters.get('salary_max'):
            filter_query &= Q(salary_min__lte=filters['salary_max'])
        
        if filters.get('skills'):
            skills = filters['skills'] if isinstance(filters['skills'], list) else [filters['skills']]
            skills_query = Q()
            for skill in skills:
                skills_query |= Q(skills_required__icontains=skill)
            filter_query &= skills_query
        
        if filters.get('company'):
            filter_query &= Q(recruiter__recruiter_profile__company_name__icontains=filters['company'])
        
        if filters.get('posted_within_days'):
            days = int(filters['posted_within_days'])
            cutoff_date = timezone.now() - timedelta(days=days)
            filter_query &= Q(created_at__gte=cutoff_date)
        
        return filter_query
    
    def _build_candidate_filter_query(self, filters: Dict[str, Any]) -> Q:
        """
        Build filter query for candidate search
        """
        filter_query = Q()
        
        if filters.get('location'):
            filter_query &= Q(job_seeker_profile__location__icontains=filters['location'])
        
        if filters.get('experience_level'):
            filter_query &= Q(job_seeker_profile__experience_level=filters['experience_level'])
        
        if filters.get('skills'):
            skills = filters['skills'] if isinstance(filters['skills'], list) else [filters['skills']]
            skills_query = Q()
            for skill in skills:
                skills_query |= Q(user_skills__skill__name__icontains=skill)
            filter_query &= skills_query
        
        if filters.get('availability'):
            filter_query &= Q(job_seeker_profile__availability=filters['availability'])
        
        if filters.get('expected_salary_max'):
            filter_query &= Q(job_seeker_profile__expected_salary__lte=filters['expected_salary_max'])
        
        return filter_query   
    def _build_relevance_annotation(self, query: str, user: User = None):
        """
        Build relevance score annotation for search results
        """
        if not query:
            return Value(1, output_field=IntegerField())
        
        # This is a simplified relevance scoring
        # In a production system, you might use full-text search capabilities
        search_terms = query.lower().split()
        
        relevance_cases = []
        for i, term in enumerate(search_terms):
            # Higher weight for title matches
            relevance_cases.append(
                When(title__icontains=term, then=Value(5 - i))
            )
            # Medium weight for description matches
            relevance_cases.append(
                When(description__icontains=term, then=Value(3 - i))
            )
            # Lower weight for other field matches
            relevance_cases.append(
                When(skills_required__icontains=term, then=Value(2 - i))
            )
        
        return Case(*relevance_cases, default=Value(0), output_field=IntegerField())
    
    def _build_profile_completeness_annotation(self):
        """
        Build profile completeness score annotation
        """
        return Case(
            When(
                Q(job_seeker_profile__isnull=False) &
                Q(job_seeker_profile__location__isnull=False) &
                Q(job_seeker_profile__experience_level__isnull=False) &
                Q(job_seeker_profile__current_position__isnull=False) &
                Q(resumes__isnull=False),
                then=Value(5)
            ),
            When(
                Q(job_seeker_profile__isnull=False) &
                Q(job_seeker_profile__location__isnull=False) &
                Q(job_seeker_profile__experience_level__isnull=False),
                then=Value(3)
            ),
            When(
                Q(job_seeker_profile__isnull=False),
                then=Value(1)
            ),
            default=Value(0),
            output_field=IntegerField()
        )
    
    def _get_job_personalization(self, job: JobPost, user: User) -> Dict[str, Any]:
        """
        Get personalization data for a job relative to a user
        """
        try:
            profile = user.job_seeker_profile
            user_skills = list(user.user_skills.values_list('skill__name', flat=True))
            
            # Calculate skill match
            job_skills = [skill.strip() for skill in job.skills_required.split(',') if skill.strip()]
            matching_skills = [skill for skill in job_skills if any(skill.lower() in user_skill.lower() for user_skill in user_skills)]
            
            # Check if already applied
            has_applied = user.applications.filter(job_post=job).exists()
            
            # Check if viewed before
            has_viewed = JobView.objects.filter(job_post=job, viewer=user).exists()
            
            return {
                'skill_match_percentage': (len(matching_skills) / len(job_skills) * 100) if job_skills else 0,
                'matching_skills': matching_skills,
                'missing_skills': [skill for skill in job_skills if skill not in matching_skills],
                'experience_level_match': profile.experience_level == job.experience_level if profile else False,
                'location_match': job.remote_work_allowed or (profile and profile.location and profile.location.lower() in job.location.lower()),
                'salary_match': self._check_salary_match(profile, job),
                'has_applied': has_applied,
                'has_viewed': has_viewed,
                'recommendation_score': 0.0  # Will be filled by recommendation engine
            }
            
        except Exception as e:
            logger.error(f"Error getting job personalization: {str(e)}")
            return {}
    
    def _check_salary_match(self, profile, job: JobPost) -> bool:
        """
        Check if job salary matches user expectations
        """
        if not profile or not profile.expected_salary or not job.salary_min:
            return False
        
        return profile.expected_salary >= job.salary_min
    
    def _build_search_cache_key(self, search_type: str, query: str, filters: Dict[str, Any],
                               user: User, limit: int, offset: int) -> str:
        """
        Build cache key for search results
        """
        import hashlib
        
        key_parts = [
            search_type,
            query or '',
            str(sorted(filters.items())) if filters else '',
            str(user.id) if user else 'anonymous',
            str(limit),
            str(offset)
        ]
        
        key_string = '|'.join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"search_{search_type}_{key_hash}"
    
    def _track_search_analytics(self, query: str, filters: Dict[str, Any], user: User,
                               result_count: int, search_type: str = 'jobs'):
        """
        Track search analytics for optimization
        """
        try:
            from .models import SearchAnalytics
            
            # This would require creating a SearchAnalytics model
            # For now, we'll just log the search
            logger.info(f"Search performed - Type: {search_type}, Query: '{query}', "
                       f"Filters: {filters}, User: {user.id if user else 'anonymous'}, "
                       f"Results: {result_count}")
            
        except Exception as e:
            logger.error(f"Error tracking search analytics: {str(e)}")


class PersonalizedContentDelivery:
    """
    Personalized content delivery system for users
    """
    
    def __init__(self):
        self.recommendation_engine = RecommendationEngine()
        self.search_optimizer = SearchOptimizer()
    
    def get_personalized_dashboard(self, user: User) -> Dict[str, Any]:
        """
        Get personalized dashboard content for a user
        """
        try:
            if user.user_type == 'job_seeker':
                return self._get_job_seeker_dashboard(user)
            elif user.user_type == 'recruiter':
                return self._get_recruiter_dashboard(user)
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error generating personalized dashboard for user {user.id}: {str(e)}")
            return {}
    
    def _get_job_seeker_dashboard(self, user: User) -> Dict[str, Any]:
        """
        Get personalized dashboard for job seekers
        """
        # Get recommendations
        job_recommendations = self.recommendation_engine.get_job_recommendations_for_user(user, limit=10)
        
        # Get recent applications
        recent_applications = user.applications.select_related('job_post').order_by('-applied_at')[:5]
        
        # Get profile completion suggestions
        profile_suggestions = self._get_profile_completion_suggestions(user)
        
        # Get trending jobs in user's field
        trending_jobs = self._get_trending_jobs_for_user(user, limit=5)
        
        return {
            'user_type': 'job_seeker',
            'recommendations': {
                'jobs': job_recommendations,
                'trending_jobs': trending_jobs
            },
            'recent_activity': {
                'applications': [
                    {
                        'job_title': app.job_post.title,
                        'company': app.job_post.recruiter.recruiter_profile.company_name if hasattr(app.job_post.recruiter, 'recruiter_profile') else 'Unknown',
                        'status': app.status,
                        'applied_at': app.applied_at.isoformat(),
                        'match_score': app.match_score
                    }
                    for app in recent_applications
                ]
            },
            'profile_suggestions': profile_suggestions,
            'stats': self._get_job_seeker_stats(user)
        }
    
    def _get_recruiter_dashboard(self, user: User) -> Dict[str, Any]:
        """
        Get personalized dashboard for recruiters
        """
        # Get active job posts
        active_jobs = user.job_posts.filter(is_active=True).order_by('-created_at')[:5]
        
        # Get recent applications
        recent_applications = Application.objects.filter(
            job_post__recruiter=user
        ).select_related('job_seeker', 'job_post').order_by('-applied_at')[:10]
        
        # Get candidate recommendations for active jobs
        candidate_recommendations = []
        for job in active_jobs[:3]:  # Top 3 active jobs
            candidates = self.recommendation_engine.get_candidate_recommendations_for_job(job, limit=5)
            if candidates:
                candidate_recommendations.append({
                    'job_id': str(job.id),
                    'job_title': job.title,
                    'candidates': candidates
                })
        
        return {
            'user_type': 'recruiter',
            'active_jobs': [
                {
                    'id': str(job.id),
                    'title': job.title,
                    'applications_count': job.applications_count,
                    'views_count': job.views_count,
                    'created_at': job.created_at.isoformat()
                }
                for job in active_jobs
            ],
            'recent_applications': [
                {
                    'candidate_name': app.job_seeker.get_full_name() or app.job_seeker.username,
                    'job_title': app.job_post.title,
                    'status': app.status,
                    'applied_at': app.applied_at.isoformat(),
                    'match_score': app.match_score
                }
                for app in recent_applications
            ],
            'candidate_recommendations': candidate_recommendations,
            'stats': self._get_recruiter_stats(user)
        }
    
    def _get_profile_completion_suggestions(self, user: User) -> List[str]:
        """
        Get profile completion suggestions for job seekers
        """
        suggestions = []
        
        try:
            profile = user.job_seeker_profile
            
            if not profile.location:
                suggestions.append("Add your location to get better job matches")
            
            if not profile.experience_level:
                suggestions.append("Set your experience level")
            
            if not profile.current_position:
                suggestions.append("Add your current position")
            
            if not profile.skills:
                suggestions.append("List your skills to improve matching")
            
            if not user.resumes.exists():
                suggestions.append("Upload your resume for AI-powered matching")
            
            if not user.user_skills.exists():
                suggestions.append("Add your technical skills")
            
        except Exception as e:
            logger.error(f"Error getting profile suggestions: {str(e)}")
        
        return suggestions
    
    def _get_trending_jobs_for_user(self, user: User, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get trending jobs relevant to the user
        """
        try:
            profile = user.job_seeker_profile
            recent_date = timezone.now() - timedelta(days=7)
            
            query = Q(is_active=True, created_at__gte=recent_date)
            
            # Filter by user's experience level if available
            if profile and profile.experience_level:
                query &= Q(experience_level=profile.experience_level)
            
            # Exclude jobs user has already applied to
            query &= ~Q(id__in=user.applications.values_list('job_post_id', flat=True))
            
            trending_jobs = JobPost.objects.filter(query).annotate(
                trend_score=Count('job_views') + Count('applications') * 2
            ).order_by('-trend_score').select_related(
                'recruiter__recruiter_profile'
            )[:limit]
            
            return [
                {
                    'id': str(job.id),
                    'title': job.title,
                    'company': job.recruiter.recruiter_profile.company_name if hasattr(job.recruiter, 'recruiter_profile') else 'Unknown',
                    'location': job.location,
                    'trend_score': job.trend_score,
                    'created_at': job.created_at.isoformat()
                }
                for job in trending_jobs
            ]
            
        except Exception as e:
            logger.error(f"Error getting trending jobs: {str(e)}")
            return []
    
    def _get_job_seeker_stats(self, user: User) -> Dict[str, Any]:
        """
        Get statistics for job seeker dashboard
        """
        try:
            return {
                'total_applications': user.applications.count(),
                'pending_applications': user.applications.filter(status='pending').count(),
                'interview_scheduled': user.applications.filter(status='interview_scheduled').count(),
                'profile_views': JobView.objects.filter(viewer=user).count(),
                'resume_count': user.resumes.count(),
                'skills_count': user.user_skills.count()
            }
        except Exception as e:
            logger.error(f"Error getting job seeker stats: {str(e)}")
            return {}
    
    def _get_recruiter_stats(self, user: User) -> Dict[str, Any]:
        """
        Get statistics for recruiter dashboard
        """
        try:
            return {
                'active_jobs': user.job_posts.filter(is_active=True).count(),
                'total_applications': Application.objects.filter(job_post__recruiter=user).count(),
                'pending_applications': Application.objects.filter(job_post__recruiter=user, status='pending').count(),
                'total_job_views': sum(job.views_count for job in user.job_posts.all()),
                'hired_candidates': Application.objects.filter(job_post__recruiter=user, status='hired').count()
            }
        except Exception as e:
            logger.error(f"Error getting recruiter stats: {str(e)}")
            return {}