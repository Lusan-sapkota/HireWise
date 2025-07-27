"""
Comprehensive tests for the advanced search and recommendation system
"""

import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    JobPost, Application, Resume, JobSeekerProfile, RecruiterProfile,
    Skill, UserSkill, JobView, AIAnalysisResult
)
from .search_analytics import SearchAnalytics, PopularSearchTerms, SearchSuggestions, SavedSearch
from .recommendation_engine import RecommendationEngine, SearchOptimizer, PersonalizedContentDelivery

User = get_user_model()


class RecommendationEngineTestCase(TestCase):
    """
    Test cases for the RecommendationEngine class
    """
    
    def setUp(self):
        """Set up test data"""
        # Clear cache before each test
        cache.clear()
        
        # Create test users
        self.job_seeker = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        
        # Create profiles
        self.job_seeker_profile = JobSeekerProfile.objects.create(
            user=self.job_seeker,
            location='San Francisco',
            experience_level='mid',
            current_position='Software Developer',
            expected_salary=100000,
            skills='Python, Django, React, JavaScript',
            availability=True
        )
        
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Corp',
            company_website='https://techcorp.com',
            industry='Technology',
            location='San Francisco'
        )
        
        # Create skills
        self.python_skill = Skill.objects.create(name='Python', category='language')
        self.django_skill = Skill.objects.create(name='Django', category='framework')
        self.react_skill = Skill.objects.create(name='React', category='framework')
        
        # Add skills to job seeker
        UserSkill.objects.create(
            user=self.job_seeker,
            skill=self.python_skill,
            proficiency_level='advanced',
            years_of_experience=3
        )
        UserSkill.objects.create(
            user=self.job_seeker,
            skill=self.django_skill,
            proficiency_level='intermediate',
            years_of_experience=2
        )
        
        # Create job posts
        self.job_post1 = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Senior Python Developer',
            description='Looking for a senior Python developer with Django experience',
            requirements='3+ years Python, Django, REST APIs',
            location='San Francisco',
            job_type='full_time',
            experience_level='mid',
            salary_min=90000,
            salary_max=120000,
            skills_required='Python, Django, REST APIs',
            is_active=True
        )
        
        self.job_post2 = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Frontend React Developer',
            description='React developer for modern web applications',
            requirements='React, JavaScript, HTML, CSS',
            location='Remote',
            job_type='full_time',
            experience_level='mid',
            salary_min=80000,
            salary_max=110000,
            skills_required='React, JavaScript, HTML, CSS',
            remote_work_allowed=True,
            is_active=True
        )
        
        self.recommendation_engine = RecommendationEngine()
    
    def test_get_job_recommendations_for_user(self):
        """Test job recommendations for job seekers"""
        recommendations = self.recommendation_engine.get_job_recommendations_for_user(
            self.job_seeker, limit=10
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check recommendation structure
        for rec in recommendations:
            self.assertIn('job_id', rec)
            self.assertIn('job', rec)
            self.assertIn('score', rec)
            self.assertIn('sources', rec)
            self.assertIn('reasons', rec)
            self.assertIn('recommendation_type', rec)
            self.assertIsInstance(rec['score'], float)
            self.assertGreaterEqual(rec['score'], 0.0)
            self.assertLessEqual(rec['score'], 1.0)
    
    def test_get_candidate_recommendations_for_job(self):
        """Test candidate recommendations for recruiters"""
        recommendations = self.recommendation_engine.get_candidate_recommendations_for_job(
            self.job_post1, limit=10
        )
        
        self.assertIsInstance(recommendations, list)
        
        # Should include our job seeker since they have matching skills
        if recommendations:
            for rec in recommendations:
                self.assertIn('candidate_id', rec)
                self.assertIn('candidate', rec)
                self.assertIn('score', rec)
                self.assertIn('sources', rec)
                self.assertIn('reasons', rec)
                self.assertIn('recommendation_type', rec)
    
    def test_content_based_job_recommendations(self):
        """Test content-based recommendation algorithm"""
        recommendations = self.recommendation_engine._get_content_based_job_recommendations(
            self.job_seeker, limit=10
        )
        
        self.assertIsInstance(recommendations, list)
        
        # Should find jobs matching user's skills and profile
        job_ids = [rec['job_id'] for rec in recommendations]
        self.assertIn(str(self.job_post1.id), job_ids)  # Should match Python/Django job
    
    def test_skill_matched_candidates(self):
        """Test skill-based candidate matching"""
        recommendations = self.recommendation_engine._get_skill_matched_candidates(
            self.job_post1, limit=10
        )
        
        self.assertIsInstance(recommendations, list)
        
        # Should find our job seeker who has Python/Django skills
        if recommendations:
            candidate_ids = [rec['candidate_id'] for rec in recommendations]
            self.assertIn(str(self.job_seeker.id), candidate_ids)
    
    def test_calculate_content_based_score(self):
        """Test content-based scoring algorithm"""
        user_skills = ['Python', 'Django', 'JavaScript']
        
        score = self.recommendation_engine._calculate_content_based_score(
            self.job_seeker, self.job_post1, user_skills
        )
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertGreater(score, 0.3)  # Should be above minimum threshold
    
    def test_find_similar_users(self):
        """Test finding similar users for collaborative filtering"""
        # Create another job seeker with similar skills
        similar_user = User.objects.create_user(
            username='similar_user',
            email='similar@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        JobSeekerProfile.objects.create(
            user=similar_user,
            location='San Francisco',
            experience_level='mid',
            skills='Python, Django, PostgreSQL'
        )
        
        UserSkill.objects.create(
            user=similar_user,
            skill=self.python_skill,
            proficiency_level='advanced'
        )
        
        similar_users = self.recommendation_engine._find_similar_users(
            self.job_seeker, limit=10
        )
        
        self.assertIsInstance(similar_users, list)
        
        if similar_users:
            user_ids = [user['user_id'] for user in similar_users]
            self.assertIn(similar_user.id, user_ids)


class SearchOptimizerTestCase(TestCase):
    """
    Test cases for the SearchOptimizer class
    """
    
    def setUp(self):
        """Set up test data"""
        cache.clear()
        
        # Create test users and data (similar to RecommendationEngineTestCase)
        self.job_seeker = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        
        JobSeekerProfile.objects.create(
            user=self.job_seeker,
            location='San Francisco',
            experience_level='mid'
        )
        
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Corp'
        )
        
        # Create job posts for search testing
        self.job_post1 = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Python Developer',
            description='Python development position with Django',
            location='San Francisco',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django',
            is_active=True
        )
        
        self.job_post2 = JobPost.objects.create(
            recruiter=self.recruiter,
            title='JavaScript Developer',
            description='Frontend JavaScript development',
            location='Remote',
            job_type='full_time',
            experience_level='mid',
            skills_required='JavaScript, React',
            remote_work_allowed=True,
            is_active=True
        )
        
        self.search_optimizer = SearchOptimizer()
    
    def test_search_jobs_basic(self):
        """Test basic job search functionality"""
        results = self.search_optimizer.search_jobs(
            query='Python',
            user=self.job_seeker,
            limit=10
        )
        
        self.assertIn('results', results)
        self.assertIn('total_count', results)
        self.assertIn('page_size', results)
        self.assertIn('offset', results)
        self.assertIn('has_next', results)
        
        # Should find Python job
        job_titles = [job['title'] for job in results['results']]
        self.assertIn('Python Developer', job_titles)
    
    def test_search_jobs_with_filters(self):
        """Test job search with filters"""
        filters = {
            'location': 'San Francisco',
            'job_type': 'full_time',
            'experience_level': 'mid'
        }
        
        results = self.search_optimizer.search_jobs(
            query='',
            filters=filters,
            user=self.job_seeker,
            limit=10
        )
        
        self.assertGreater(results['total_count'], 0)
        
        # All results should match filters
        for job in results['results']:
            self.assertEqual(job['job_type'], 'full_time')
            self.assertEqual(job['experience_level'], 'mid')
    
    def test_search_candidates(self):
        """Test candidate search for recruiters"""
        results = self.search_optimizer.search_candidates(
            query='Python',
            user=self.recruiter,
            limit=10
        )
        
        self.assertIn('results', results)
        self.assertIn('total_count', results)
        
        # Should work without errors for recruiters
        self.assertIsInstance(results['results'], list)
    
    def test_search_candidates_access_control(self):
        """Test that only recruiters can search candidates"""
        results = self.search_optimizer.search_candidates(
            query='Python',
            user=self.job_seeker,  # Job seeker trying to search candidates
            limit=10
        )
        
        self.assertIn('error', results)
        self.assertEqual(results['error'], 'Access denied')
    
    def test_build_text_search_query(self):
        """Test text search query building"""
        query = self.search_optimizer._build_text_search_query('Python Django')
        
        # Should create a valid Q object
        from django.db.models import Q
        self.assertIsInstance(query, Q)
    
    def test_build_filter_query(self):
        """Test filter query building"""
        filters = {
            'location': 'San Francisco',
            'job_type': 'full_time',
            'salary_min': 80000
        }
        
        query = self.search_optimizer._build_filter_query(filters)
        
        from django.db.models import Q
        self.assertIsInstance(query, Q)


class PersonalizedContentDeliveryTestCase(TestCase):
    """
    Test cases for PersonalizedContentDelivery class
    """
    
    def setUp(self):
        """Set up test data"""
        cache.clear()
        
        self.job_seeker = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        
        JobSeekerProfile.objects.create(
            user=self.job_seeker,
            location='San Francisco',
            experience_level='mid'
        )
        
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Corp'
        )
        
        self.content_delivery = PersonalizedContentDelivery()
    
    def test_get_personalized_dashboard_job_seeker(self):
        """Test personalized dashboard for job seekers"""
        dashboard = self.content_delivery.get_personalized_dashboard(self.job_seeker)
        
        self.assertEqual(dashboard['user_type'], 'job_seeker')
        self.assertIn('recommendations', dashboard)
        self.assertIn('recent_activity', dashboard)
        self.assertIn('profile_suggestions', dashboard)
        self.assertIn('stats', dashboard)
    
    def test_get_personalized_dashboard_recruiter(self):
        """Test personalized dashboard for recruiters"""
        dashboard = self.content_delivery.get_personalized_dashboard(self.recruiter)
        
        self.assertEqual(dashboard['user_type'], 'recruiter')
        self.assertIn('active_jobs', dashboard)
        self.assertIn('recent_applications', dashboard)
        self.assertIn('candidate_recommendations', dashboard)
        self.assertIn('stats', dashboard)
    
    def test_get_profile_completion_suggestions(self):
        """Test profile completion suggestions"""
        suggestions = self.content_delivery._get_profile_completion_suggestions(self.job_seeker)
        
        self.assertIsInstance(suggestions, list)
        # Should suggest adding skills, resume, etc.
        self.assertGreater(len(suggestions), 0)


class RecommendationAPITestCase(APITestCase):
    """
    Test cases for recommendation API endpoints
    """
    
    def setUp(self):
        """Set up test data and authentication"""
        cache.clear()
        
        self.client = APIClient()
        
        # Create test users
        self.job_seeker = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        
        # Create profiles
        JobSeekerProfile.objects.create(
            user=self.job_seeker,
            location='San Francisco',
            experience_level='mid'
        )
        
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Corp'
        )
        
        # Create a job post
        self.job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Python Developer',
            description='Python development position',
            location='San Francisco',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django',
            is_active=True
        )
        
        # Generate JWT tokens
        self.job_seeker_token = str(RefreshToken.for_user(self.job_seeker).access_token)
        self.recruiter_token = str(RefreshToken.for_user(self.recruiter).access_token)
    
    def test_job_recommendations_endpoint(self):
        """Test job recommendations API endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        url = reverse('job-recommendations')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('recommendations', data)
        self.assertIn('total_count', data)
        self.assertIn('generated_at', data)
    
    def test_job_recommendations_access_control(self):
        """Test that only job seekers can access job recommendations"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.recruiter_token}')
        
        url = reverse('job-recommendations')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_candidate_recommendations_endpoint(self):
        """Test candidate recommendations API endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.recruiter_token}')
        
        url = reverse('candidate-recommendations', kwargs={'job_id': self.job_post.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('recommendations', data)
        self.assertIn('job_id', data)
        self.assertIn('job_title', data)
    
    def test_candidate_recommendations_access_control(self):
        """Test that only recruiters can access candidate recommendations"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        url = reverse('candidate-recommendations', kwargs={'job_id': self.job_post.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_advanced_job_search_endpoint(self):
        """Test advanced job search API endpoint"""
        url = reverse('advanced-job-search')
        response = self.client.get(url, {'q': 'Python', 'limit': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('total_count', data)
        self.assertIn('page_size', data)
    
    def test_advanced_candidate_search_endpoint(self):
        """Test advanced candidate search API endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.recruiter_token}')
        
        url = reverse('advanced-candidate-search')
        response = self.client.get(url, {'q': 'Python', 'limit': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('total_count', data)
    
    def test_personalized_dashboard_endpoint(self):
        """Test personalized dashboard API endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        url = reverse('personalized-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('dashboard', data)
        self.assertIn('generated_at', data)


class SearchAnalyticsTestCase(APITestCase):
    """
    Test cases for search analytics functionality
    """
    
    def setUp(self):
        """Set up test data"""
        cache.clear()
        
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.token = str(RefreshToken.for_user(self.user).access_token)
    
    def test_search_suggestions_endpoint(self):
        """Test search suggestions API endpoint"""
        # Create some search suggestions
        SearchSuggestions.objects.create(
            search_type='jobs',
            suggestion_type='query',
            text='Python Developer',
            popularity_score=10.0
        )
        
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': 'Python', 'type': 'jobs'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('suggestions', data)
        self.assertIn('query', data)
        self.assertIn('search_type', data)
    
    def test_popular_searches_endpoint(self):
        """Test popular searches API endpoint"""
        # Create popular search terms
        PopularSearchTerms.objects.create(
            search_type='jobs',
            term='python developer',
            search_count=50
        )
        
        url = reverse('popular-searches')
        response = self.client.get(url, {'type': 'jobs'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('popular_terms', data)
        self.assertIn('search_type', data)
    
    def test_save_search_endpoint(self):
        """Test save search API endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        url = reverse('save-search')
        data = {
            'name': 'Python Jobs',
            'search_type': 'jobs',
            'query': 'Python Developer',
            'filters': {'location': 'San Francisco'},
            'alerts_enabled': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('saved_search', response_data)
    
    def test_saved_searches_endpoint(self):
        """Test saved searches API endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create a saved search
        SavedSearch.objects.create(
            user=self.user,
            name='Python Jobs',
            search_type='jobs',
            query='Python Developer'
        )
        
        url = reverse('saved-searches')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('saved_searches', data)
        self.assertIn('total_count', data)
        self.assertEqual(len(data['saved_searches']), 1)
    
    def test_search_analytics_endpoint(self):
        """Test search analytics API endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create search analytics data
        SearchAnalytics.objects.create(
            user=self.user,
            search_type='jobs',
            query='Python Developer',
            results_count=25
        )
        
        url = reverse('search-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('total_searches', data)
        self.assertIn('average_results_per_search', data)
        self.assertIn('top_queries', data)
        self.assertIn('recent_searches', data)


class RecommendationPerformanceTestCase(TestCase):
    """
    Test cases for recommendation system performance
    """
    
    def setUp(self):
        """Set up performance test data"""
        cache.clear()
        
        # Create multiple users and jobs for performance testing
        self.users = []
        self.jobs = []
        
        # Create recruiter
        self.recruiter = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Corp'
        )
        
        # Create multiple job seekers
        for i in range(10):
            user = User.objects.create_user(
                username=f'jobseeker{i}',
                email=f'jobseeker{i}@test.com',
                password='testpass123',
                user_type='job_seeker'
            )
            
            JobSeekerProfile.objects.create(
                user=user,
                location='San Francisco',
                experience_level='mid',
                skills=f'Python, Django, Skill{i}'
            )
            
            self.users.append(user)
        
        # Create multiple job posts
        for i in range(20):
            job = JobPost.objects.create(
                recruiter=self.recruiter,
                title=f'Developer Position {i}',
                description=f'Job description {i}',
                location='San Francisco',
                job_type='full_time',
                experience_level='mid',
                skills_required=f'Python, Django, Skill{i % 5}',
                is_active=True
            )
            self.jobs.append(job)
        
        self.recommendation_engine = RecommendationEngine()
    
    def test_recommendation_performance(self):
        """Test recommendation generation performance"""
        import time
        
        start_time = time.time()
        
        # Generate recommendations for multiple users
        for user in self.users[:5]:  # Test with 5 users
            recommendations = self.recommendation_engine.get_job_recommendations_for_user(
                user, limit=10
            )
            self.assertIsInstance(recommendations, list)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(execution_time, 10.0, "Recommendation generation took too long")
    
    def test_search_performance(self):
        """Test search performance with multiple queries"""
        import time
        
        search_optimizer = SearchOptimizer()
        
        start_time = time.time()
        
        # Perform multiple searches
        queries = ['Python', 'Django', 'Developer', 'Engineer', 'Software']
        for query in queries:
            results = search_optimizer.search_jobs(query, limit=10)
            self.assertIn('results', results)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(execution_time, 5.0, "Search took too long")
    
    def test_caching_effectiveness(self):
        """Test that caching improves performance"""
        import time
        
        user = self.users[0]
        
        # First call (should cache the result)
        start_time = time.time()
        recommendations1 = self.recommendation_engine.get_job_recommendations_for_user(
            user, limit=10
        )
        first_call_time = time.time() - start_time
        
        # Second call (should use cache)
        start_time = time.time()
        recommendations2 = self.recommendation_engine.get_job_recommendations_for_user(
            user, limit=10
        )
        second_call_time = time.time() - start_time
        
        # Second call should be faster due to caching
        self.assertLess(second_call_time, first_call_time)
        
        # Results should be the same
        self.assertEqual(len(recommendations1), len(recommendations2))