"""
Comprehensive tests for enhanced job posting management
"""
import json
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from .models import (
    User, JobPost, RecruiterProfile, JobSeekerProfile, 
    Application, Resume, JobAnalytics, JobView
)
from .serializers import JobPostSerializer, JobPostListSerializer

User = get_user_model()


class JobPostModelTest(TestCase):
    """Test JobPost model functionality"""
    
    def setUp(self):
        self.recruiter_user = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            company_name='Test Company',
            company_website='https://testcompany.com',
            industry='Technology'
        )
        
    def test_job_post_creation(self):
        """Test basic job post creation"""
        job_post = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Software Engineer',
            description='We are looking for a skilled software engineer...',
            requirements='Python, Django, React',
            location='San Francisco, CA',
            job_type='full_time',
            experience_level='mid',
            salary_min=80000,
            salary_max=120000,
            skills_required='Python, Django, React, PostgreSQL'
        )
        
        self.assertEqual(job_post.title, 'Software Engineer')
        self.assertEqual(job_post.recruiter, self.recruiter_user)
        self.assertTrue(job_post.is_active)
        self.assertFalse(job_post.is_featured)
        self.assertEqual(job_post.views_count, 0)
        self.assertEqual(job_post.applications_count, 0)
        self.assertIsNotNone(job_post.slug)
        
    def test_job_post_slug_generation(self):
        """Test automatic slug generation"""
        job_post = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Senior Python Developer',
            description='Test description',
            requirements='Test requirements',
            location='Remote',
            job_type='full_time',
            experience_level='senior',
            skills_required='Python, Django'
        )
        
        expected_slug = 'senior-python-developer-test-company'
        self.assertEqual(job_post.slug, expected_slug)
        
    def test_job_post_is_expired_property(self):
        """Test is_expired property"""
        # Job with future deadline
        future_job = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Future Job',
            description='Test description',
            requirements='Test requirements',
            location='Remote',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python',
            application_deadline=timezone.now() + timedelta(days=30)
        )
        self.assertFalse(future_job.is_expired)
        
        # Job with past deadline
        past_job = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Past Job',
            description='Test description',
            requirements='Test requirements',
            location='Remote',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python',
            application_deadline=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(past_job.is_expired)
        
    def test_increment_view_count(self):
        """Test atomic view count increment"""
        job_post = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Test Job',
            description='Test description',
            requirements='Test requirements',
            location='Remote',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python'
        )
        
        initial_count = job_post.views_count
        job_post.increment_view_count()
        job_post.refresh_from_db()
        
        self.assertEqual(job_post.views_count, initial_count + 1)


class JobPostAPITest(APITestCase):
    """Test JobPost API endpoints"""
    
    def setUp(self):
        # Create test users
        self.recruiter_user = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            company_name='Test Company',
            company_website='https://testcompany.com',
            industry='Technology'
        )
        
        self.job_seeker_user = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        self.job_seeker_profile = JobSeekerProfile.objects.create(
            user=self.job_seeker_user,
            location='San Francisco, CA',
            experience_level='mid'
        )
        
        # Create test job posts
        self.job_post1 = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Software Engineer',
            description='We are looking for a skilled software engineer with experience in Python and Django.',
            requirements='3+ years of Python experience, Django framework knowledge',
            location='San Francisco, CA',
            job_type='full_time',
            experience_level='mid',
            salary_min=80000,
            salary_max=120000,
            skills_required='Python, Django, React, PostgreSQL',
            is_active=True
        )
        
        self.job_post2 = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Frontend Developer',
            description='Looking for a frontend developer with React experience.',
            requirements='2+ years of React experience',
            location='Remote',
            job_type='full_time',
            experience_level='entry',
            salary_min=60000,
            salary_max=90000,
            skills_required='React, JavaScript, HTML, CSS',
            remote_work_allowed=True,
            is_active=True
        )
        
        # Create inactive job for testing
        self.inactive_job = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Inactive Job',
            description='This job is inactive',
            requirements='Test requirements',
            location='Test Location',
            job_type='full_time',
            experience_level='mid',
            skills_required='Test skills',
            is_active=False
        )
        
        self.client = APIClient()
        
    def get_jwt_token(self, user):
        """Helper method to get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
        
    def test_job_post_list_unauthenticated(self):
        """Test that unauthenticated users cannot access job posts"""
        url = reverse('job-post-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_job_post_list_authenticated(self):
        """Test job post listing for authenticated users"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Only active jobs
        
        # Check that inactive job is not included
        job_titles = [job['title'] for job in response.data['results']]
        self.assertNotIn('Inactive Job', job_titles)
        
    def test_job_post_search(self):
        """Test job post search functionality"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-list')
        
        # Search by title
        response = self.client.get(url, {'search': 'Software'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Software Engineer')
        
        # Search by skills
        response = self.client.get(url, {'search': 'React'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Both jobs have React
        
    def test_job_post_filtering(self):
        """Test job post filtering functionality"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-list')
        
        # Filter by job type
        response = self.client.get(url, {'job_type': 'full_time'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Filter by experience level
        response = self.client.get(url, {'experience_level': 'entry'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Frontend Developer')
        
        # Filter by location
        response = self.client.get(url, {'location': 'San Francisco'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Software Engineer')
        
        # Filter by remote work
        response = self.client.get(url, {'remote_only': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Frontend Developer')
        
    def test_salary_range_filtering(self):
        """Test salary range filtering"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-list')
        
        # Filter by minimum salary - should return jobs where max salary >= requested min
        response = self.client.get(url, {'salary_min': '100000'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Software Engineer')
        
        # Filter by maximum salary - should return jobs where min salary <= requested max
        response = self.client.get(url, {'salary_max': '70000'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Frontend Developer')
        
    def test_skills_filtering(self):
        """Test skills-based filtering"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-list')
        
        # Filter by single skill
        response = self.client.get(url, {'skills': 'Python'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Software Engineer')
        
        # Filter by multiple skills
        response = self.client.get(url, {'skills': 'React,JavaScript'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Frontend Developer')
        
    def test_job_post_ordering(self):
        """Test job post ordering"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-list')
        
        # Order by title
        response = self.client.get(url, {'ordering': 'title'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [job['title'] for job in response.data['results']]
        self.assertEqual(titles, sorted(titles))
        
        # Order by salary (descending)
        response = self.client.get(url, {'ordering': '-salary_max'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        salaries = [job['salary_max'] for job in response.data['results']]
        self.assertEqual(salaries, sorted(salaries, reverse=True))
        
    def test_job_post_create_as_recruiter(self):
        """Test job post creation by recruiter"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-list')
        data = {
            'title': 'Backend Developer',
            'description': 'We are looking for a backend developer with strong Python skills.',
            'requirements': 'Python, Django, PostgreSQL, Redis',
            'location': 'New York, NY',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'salary_min': 100000,
            'salary_max': 150000,
            'skills_required': 'Python, Django, PostgreSQL, Redis',
            'remote_work_allowed': False
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify job post was created
        job_post = JobPost.objects.get(title='Backend Developer')
        self.assertEqual(job_post.recruiter, self.recruiter_user)
        self.assertTrue(job_post.is_active)
        
        # Verify analytics was created
        self.assertTrue(hasattr(job_post, 'analytics'))
        
    def test_job_post_create_as_job_seeker_forbidden(self):
        """Test that job seekers cannot create job posts"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-list')
        data = {
            'title': 'Test Job',
            'description': 'Test description',
            'requirements': 'Test requirements',
            'location': 'Test Location',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'skills_required': 'Test skills'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_job_post_create_validation(self):
        """Test job post creation validation"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-list')
        
        # Test with invalid data (missing required fields)
        invalid_data = {
            'title': 'A',  # Too short
            'description': 'Short',  # Too short
            'requirements': 'Short',  # Too short
        }
        
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check specific validation errors
        self.assertIn('title', response.data)
        self.assertIn('description', response.data)
        self.assertIn('requirements', response.data)
        self.assertIn('location', response.data)
        self.assertIn('job_type', response.data)
        self.assertIn('experience_level', response.data)
        self.assertIn('skills_required', response.data)
        
        # Test salary validation with valid required fields
        salary_invalid_data = {
            'title': 'Valid Job Title',
            'description': 'This is a valid job description that is long enough to pass validation requirements.',
            'requirements': 'These are valid job requirements that are long enough.',
            'location': 'Test Location',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'skills_required': 'Python, Django',
            'salary_min': 100000,
            'salary_max': 50000,  # Less than min
            'application_deadline': '2020-01-01T00:00:00Z'  # Past date
        }
        
        response = self.client.post(url, salary_invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('salary_max', response.data)
        
        # Test application deadline validation separately
        deadline_invalid_data = {
            'title': 'Valid Job Title',
            'description': 'This is a valid job description that is long enough to pass validation requirements.',
            'requirements': 'These are valid job requirements that are long enough.',
            'location': 'Test Location',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'skills_required': 'Python, Django',
            'salary_min': 50000,
            'salary_max': 80000,
            'application_deadline': '2020-01-01T00:00:00Z'  # Past date
        }
        
        response = self.client.post(url, deadline_invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('application_deadline', response.data)
        
    def test_job_post_retrieve_with_view_tracking(self):
        """Test job post retrieval with view tracking"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-detail', kwargs={'pk': self.job_post1.pk})
        
        initial_views = self.job_post1.views_count
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that view count was incremented
        self.job_post1.refresh_from_db()
        self.assertEqual(self.job_post1.views_count, initial_views + 1)
        
        # Check that JobView record was created
        job_view = JobView.objects.filter(job_post=self.job_post1, viewer=self.job_seeker_user).first()
        self.assertIsNotNone(job_view)
        
    def test_job_post_update_by_owner(self):
        """Test job post update by owner"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-detail', kwargs={'pk': self.job_post1.pk})
        data = {
            'title': 'Senior Software Engineer',
            'salary_max': 140000
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.job_post1.refresh_from_db()
        self.assertEqual(self.job_post1.title, 'Senior Software Engineer')
        self.assertEqual(self.job_post1.salary_max, 140000)
        
    def test_job_post_update_by_non_owner_forbidden(self):
        """Test that non-owners cannot update job posts"""
        # Create another recruiter
        other_recruiter = User.objects.create_user(
            username='other_recruiter',
            email='other@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        RecruiterProfile.objects.create(
            user=other_recruiter,
            company_name='Other Company'
        )
        
        token = self.get_jwt_token(other_recruiter)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-detail', kwargs={'pk': self.job_post1.pk})
        data = {'title': 'Hacked Title'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_job_post_delete_by_owner(self):
        """Test job post deletion by owner"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-detail', kwargs={'pk': self.job_post1.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(JobPost.objects.filter(pk=self.job_post1.pk).exists())
        
    def test_job_post_applications_endpoint(self):
        """Test job post applications endpoint"""
        # Create an application
        resume = Resume.objects.create(
            job_seeker=self.job_seeker_user,
            original_filename='test_resume.pdf',
            file_size=1024,
            is_primary=True
        )
        
        application = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post1,
            resume=resume,
            cover_letter='Test cover letter',
            match_score=0.85
        )
        
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-applications', kwargs={'pk': self.job_post1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(application.id))
        
    def test_job_post_analytics_endpoint(self):
        """Test job post analytics endpoint"""
        # Create analytics data
        JobAnalytics.objects.create(
            job_post=self.job_post1,
            total_views=100,
            unique_views=80,
            total_applications=5,
            conversion_rate=5.0
        )
        
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-analytics', kwargs={'pk': self.job_post1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_views'], 100)
        self.assertEqual(response.data['unique_views'], 80)
        self.assertEqual(response.data['total_applications'], 5)
        self.assertEqual(response.data['conversion_rate'], 5.0)
        
    def test_job_post_toggle_active_endpoint(self):
        """Test job post toggle active endpoint"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-toggle-active', kwargs={'pk': self.job_post1.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.job_post1.refresh_from_db()
        self.assertFalse(self.job_post1.is_active)  # Should be toggled to False
        
        # Toggle again
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.job_post1.refresh_from_db()
        self.assertTrue(self.job_post1.is_active)  # Should be toggled back to True
        
    def test_job_post_duplicate_endpoint(self):
        """Test job post duplication endpoint"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-duplicate', kwargs={'pk': self.job_post1.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that a new job post was created
        duplicated_job = JobPost.objects.get(title='Software Engineer (Copy)')
        self.assertEqual(duplicated_job.recruiter, self.recruiter_user)
        self.assertFalse(duplicated_job.is_active)  # Should start as inactive
        self.assertEqual(duplicated_job.views_count, 0)
        self.assertEqual(duplicated_job.applications_count, 0)
        
        # Check that analytics was created for the duplicated job
        self.assertTrue(hasattr(duplicated_job, 'analytics'))
        
    def test_search_suggestions_endpoint(self):
        """Test search suggestions endpoint"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-search-suggestions')
        
        # Test with valid query
        response = self.client.get(url, {'q': 'Soft'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        suggestions = response.data['suggestions']
        self.assertIn('titles', suggestions)
        self.assertIn('locations', suggestions)
        self.assertIn('companies', suggestions)
        self.assertIn('Software Engineer', suggestions['titles'])
        
        # Test with short query
        response = self.client.get(url, {'q': 'S'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['suggestions'], [])
        
    def test_recruiter_my_jobs_filter(self):
        """Test recruiter's my_jobs filter"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('job-post-list')
        response = self.client.get(url, {'my_jobs': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include both active and inactive jobs for the recruiter
        self.assertEqual(len(response.data['results']), 3)  # 2 active + 1 inactive


class JobAnalyticsTest(TestCase):
    """Test JobAnalytics model and functionality"""
    
    def setUp(self):
        self.recruiter_user = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            company_name='Test Company'
        )
        
        self.job_post = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Test Job',
            description='Test description',
            requirements='Test requirements',
            location='Test Location',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django'
        )
        
    def test_job_analytics_creation(self):
        """Test JobAnalytics creation"""
        analytics = JobAnalytics.objects.create(
            job_post=self.job_post,
            total_views=100,
            unique_views=80,
            total_applications=10
        )
        
        self.assertEqual(analytics.job_post, self.job_post)
        self.assertEqual(analytics.total_views, 100)
        self.assertEqual(analytics.unique_views, 80)
        self.assertEqual(analytics.total_applications, 10)
        self.assertEqual(analytics.conversion_rate, 0.0)  # Not calculated yet
        
    def test_conversion_rate_calculation(self):
        """Test conversion rate calculation"""
        analytics = JobAnalytics.objects.create(
            job_post=self.job_post,
            total_views=100,
            total_applications=5
        )
        
        analytics.update_conversion_rate()
        self.assertEqual(analytics.conversion_rate, 5.0)  # 5/100 * 100 = 5%
        
        # Test with zero views
        analytics.total_views = 0
        analytics.update_conversion_rate()
        self.assertEqual(analytics.conversion_rate, 0.0)


class JobViewTest(TestCase):
    """Test JobView model and tracking"""
    
    def setUp(self):
        self.recruiter_user = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            company_name='Test Company'
        )
        
        self.job_seeker_user = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.job_post = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Test Job',
            description='Test description',
            requirements='Test requirements',
            location='Test Location',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django'
        )
        
    def test_job_view_creation(self):
        """Test JobView creation"""
        job_view = JobView.objects.create(
            job_post=self.job_post,
            viewer=self.job_seeker_user,
            ip_address='192.168.1.1',
            user_agent='Test User Agent',
            referrer='https://example.com',
            view_duration=30
        )
        
        self.assertEqual(job_view.job_post, self.job_post)
        self.assertEqual(job_view.viewer, self.job_seeker_user)
        self.assertEqual(job_view.ip_address, '192.168.1.1')
        self.assertEqual(job_view.view_duration, 30)
        
    def test_anonymous_job_view(self):
        """Test JobView creation for anonymous users"""
        job_view = JobView.objects.create(
            job_post=self.job_post,
            viewer=None,  # Anonymous user
            ip_address='192.168.1.1',
            user_agent='Test User Agent'
        )
        
        self.assertEqual(job_view.job_post, self.job_post)
        self.assertIsNone(job_view.viewer)
        self.assertEqual(job_view.ip_address, '192.168.1.1')


class JobPostSerializerTest(TestCase):
    """Test JobPost serializers"""
    
    def setUp(self):
        self.recruiter_user = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            company_name='Test Company'
        )
        
    def test_job_post_serializer_skills_list(self):
        """Test skills_list field in serializer"""
        job_post = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Test Job',
            description='Test description',
            requirements='Test requirements',
            location='Test Location',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django, React, PostgreSQL'
        )
        
        serializer = JobPostSerializer(job_post)
        skills_list = serializer.data['skills_list']
        
        expected_skills = ['Python', 'Django', 'React', 'PostgreSQL']
        self.assertEqual(skills_list, expected_skills)
        
    def test_job_post_create_serializer_validation(self):
        """Test JobPostCreateSerializer validation"""
        from .serializers import JobPostCreateSerializer
        
        # Test with invalid data (field validation)
        invalid_data = {
            'title': 'AB',  # Too short
            'description': 'Short desc',  # Too short
            'requirements': 'Short req',  # Too short
            'location': 'Test Location',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'skills_required': 'Python',
        }
        
        serializer = JobPostCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        
        self.assertIn('title', serializer.errors)
        self.assertIn('description', serializer.errors)
        self.assertIn('requirements', serializer.errors)
        
        # Test salary validation separately
        salary_invalid_data = {
            'title': 'Valid Job Title',
            'description': 'This is a valid job description that is long enough to pass validation requirements.',
            'requirements': 'These are valid job requirements that are long enough.',
            'location': 'Test Location',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'skills_required': 'Python',
            'salary_min': 100000,
            'salary_max': 50000,  # Less than min
        }
        
        salary_serializer = JobPostCreateSerializer(data=salary_invalid_data)
        self.assertFalse(salary_serializer.is_valid())
        self.assertIn('salary_max', salary_serializer.errors)
        
    def test_job_post_list_serializer_skills_limit(self):
        """Test that JobPostListSerializer limits skills to 5"""
        job_post = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Test Job',
            description='Test description',
            requirements='Test requirements',
            location='Test Location',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django, React, PostgreSQL, Redis, Docker, Kubernetes, AWS'
        )
        
        serializer = JobPostListSerializer(job_post)
        skills_list = serializer.data['skills_list']
        
        # Should be limited to first 5 skills
        self.assertEqual(len(skills_list), 5)
        expected_skills = ['Python', 'Django', 'React', 'PostgreSQL', 'Redis']
        self.assertEqual(skills_list, expected_skills)