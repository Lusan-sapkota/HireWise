"""
Comprehensive tests for job application system
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
    Application, Resume, AIAnalysisResult
)
from .serializers import ApplicationSerializer

User = get_user_model()


class ApplicationModelTest(TestCase):
    """Test Application model functionality"""
    
    def setUp(self):
        # Create recruiter
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
        
        # Create job seeker
        self.job_seeker_user = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        self.job_seeker_profile = JobSeekerProfile.objects.create(
            user=self.job_seeker_user,
            location='San Francisco, CA'
        )
        
        # Create job post
        self.job_post = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Software Engineer',
            description='Test job description',
            requirements='Test requirements',
            location='San Francisco, CA',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker_user,
            original_filename='test_resume.pdf',
            file_size=1024,
            is_primary=True
        )
    
    def test_application_creation(self):
        """Test basic application creation"""
        application = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post,
            resume=self.resume,
            cover_letter='Test cover letter',
            match_score=0.85
        )
        
        self.assertEqual(application.job_seeker, self.job_seeker_user)
        self.assertEqual(application.job_post, self.job_post)
        self.assertEqual(application.resume, self.resume)
        self.assertEqual(application.status, 'pending')
        self.assertEqual(application.match_score, 0.85)
        self.assertIsNotNone(application.applied_at)
    
    def test_application_unique_constraint(self):
        """Test that user cannot apply to same job twice"""
        # Create first application
        Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post,
            resume=self.resume
        )
        
        # Try to create duplicate application
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Application.objects.create(
                job_seeker=self.job_seeker_user,
                job_post=self.job_post,
                resume=self.resume
            )
    
    def test_application_string_representation(self):
        """Test application string representation"""
        application = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post,
            resume=self.resume
        )
        
        expected_str = f"{self.job_seeker_user.username} -> {self.job_post.title}"
        self.assertEqual(str(application), expected_str)
    
    def test_application_status_choices(self):
        """Test application status choices"""
        application = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post,
            resume=self.resume
        )
        
        valid_statuses = [
            'pending', 'reviewed', 'shortlisted', 'interview_scheduled',
            'interviewed', 'hired', 'rejected'
        ]
        
        for status_choice in valid_statuses:
            application.status = status_choice
            application.save()
            self.assertEqual(application.status, status_choice)


class ApplicationAPITest(APITestCase):
    """Test Application API endpoints"""
    
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
            company_name='Test Company'
        )
        
        self.job_seeker_user = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        self.job_seeker_profile = JobSeekerProfile.objects.create(
            user=self.job_seeker_user,
            location='San Francisco, CA'
        )
        
        # Create another job seeker for testing access control
        self.other_job_seeker = User.objects.create_user(
            username='jobseeker2',
            email='jobseeker2@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        JobSeekerProfile.objects.create(user=self.other_job_seeker)
        
        # Create job posts
        self.job_post1 = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Software Engineer',
            description='Test job description',
            requirements='Test requirements',
            location='San Francisco, CA',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django',
            is_active=True
        )
        
        self.job_post2 = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Frontend Developer',
            description='Frontend job description',
            requirements='Frontend requirements',
            location='Remote',
            job_type='full_time',
            experience_level='entry',
            skills_required='React, JavaScript',
            is_active=True
        )
        
        # Create inactive job for testing
        self.inactive_job = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Inactive Job',
            description='Inactive job description',
            requirements='Inactive requirements',
            location='Test Location',
            job_type='full_time',
            experience_level='mid',
            skills_required='Test skills',
            is_active=False
        )
        
        # Create expired job for testing
        self.expired_job = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Expired Job',
            description='Expired job description',
            requirements='Expired requirements',
            location='Test Location',
            job_type='full_time',
            experience_level='mid',
            skills_required='Test skills',
            application_deadline=timezone.now() - timedelta(days=1),
            is_active=True
        )
        
        # Create resumes
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker_user,
            original_filename='test_resume.pdf',
            file_size=1024,
            is_primary=True
        )
        
        self.other_resume = Resume.objects.create(
            job_seeker=self.other_job_seeker,
            original_filename='other_resume.pdf',
            file_size=1024,
            is_primary=True
        )
        
        self.client = APIClient()
    
    def get_jwt_token(self, user):
        """Helper method to get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_application_list_unauthenticated(self):
        """Test that unauthenticated users cannot access applications"""
        url = reverse('application-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_application_list_job_seeker(self):
        """Test application listing for job seekers"""
        # Create applications
        app1 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post1,
            resume=self.resume,
            cover_letter='Cover letter 1'
        )
        
        app2 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post2,
            resume=self.resume,
            cover_letter='Cover letter 2'
        )
        
        # Create application by other user (should not be visible)
        Application.objects.create(
            job_seeker=self.other_job_seeker,
            job_post=self.job_post1,
            resume=self.other_resume
        )
        
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Check that only own applications are returned
        app_ids = [app['id'] for app in response.data['results']]
        self.assertIn(str(app1.id), app_ids)
        self.assertIn(str(app2.id), app_ids)
    
    def test_application_list_recruiter(self):
        """Test application listing for recruiters"""
        # Create applications
        app1 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post1,
            resume=self.resume
        )
        
        app2 = Application.objects.create(
            job_seeker=self.other_job_seeker,
            job_post=self.job_post2,
            resume=self.other_resume
        )
        
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Check that applications for recruiter's jobs are returned
        app_ids = [app['id'] for app in response.data['results']]
        self.assertIn(str(app1.id), app_ids)
        self.assertIn(str(app2.id), app_ids)
    
    @patch('matcher.utils.calculate_match_score')
    @patch('matcher.utils.analyze_job_match')
    def test_application_create_success(self, mock_analyze, mock_calculate):
        """Test successful application creation"""
        mock_calculate.return_value = 0.85
        mock_analyze.return_value = {
            'matching_skills': ['Python', 'Django'],
            'missing_skills': ['React'],
            'recommendations': 'Good match'
        }
        
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-list')
        data = {
            'job_post': str(self.job_post1.id),
            'cover_letter': 'This is my cover letter for the software engineer position.'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify application was created
        application = Application.objects.get(id=response.data['id'])
        self.assertEqual(application.job_seeker, self.job_seeker_user)
        self.assertEqual(application.job_post, self.job_post1)
        self.assertEqual(application.resume, self.resume)
        self.assertEqual(application.match_score, 0.85)
        self.assertEqual(application.status, 'pending')
        
        # Verify AI analysis was created
        ai_analysis = AIAnalysisResult.objects.filter(application=application).first()
        self.assertIsNotNone(ai_analysis)
        self.assertEqual(ai_analysis.analysis_type, 'job_match')
        
        # Verify job post applications count was updated
        self.job_post1.refresh_from_db()
        self.assertEqual(self.job_post1.applications_count, 1)
    
    def test_application_create_duplicate(self):
        """Test that duplicate applications are prevented"""
        # Create first application
        Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post1,
            resume=self.resume
        )
        
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-list')
        data = {
            'job_post': str(self.job_post1.id),
            'cover_letter': 'Another cover letter'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You have already applied to this job', str(response.data))
    
    def test_application_create_inactive_job(self):
        """Test that applications to inactive jobs are prevented"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-list')
        data = {
            'job_post': str(self.inactive_job.id),
            'cover_letter': 'Cover letter for inactive job'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no longer active', str(response.data))
    
    def test_application_create_expired_job(self):
        """Test that applications to expired jobs are prevented"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-list')
        data = {
            'job_post': str(self.expired_job.id),
            'cover_letter': 'Cover letter for expired job'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('deadline', str(response.data))
    
    def test_application_create_no_resume(self):
        """Test that applications without resume are prevented"""
        # Delete the resume
        self.resume.delete()
        
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-list')
        data = {
            'job_post': str(self.job_post1.id),
            'cover_letter': 'Cover letter without resume'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('upload a resume', str(response.data))
    
    def test_application_create_recruiter_forbidden(self):
        """Test that recruiters cannot create applications"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-list')
        data = {
            'job_post': str(self.job_post1.id),
            'cover_letter': 'Recruiter trying to apply'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_application_filtering(self):
        """Test application filtering functionality"""
        # Create applications with different statuses
        app1 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post1,
            resume=self.resume,
            status='pending'
        )
        
        app2 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post2,
            resume=self.resume,
            status='reviewed'
        )
        
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-list')
        
        # Filter by status
        response = self.client.get(url, {'status': 'pending'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(app1.id))
        
        # Filter by multiple statuses
        response = self.client.get(url, {'status': 'pending,reviewed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Filter by job post
        response = self.client.get(url, {'job_post': str(self.job_post1.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(app1.id))
    
    def test_application_search(self):
        """Test application search functionality"""
        app1 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post1,
            resume=self.resume,
            cover_letter='I am passionate about Python development'
        )
        
        app2 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post2,
            resume=self.resume,
            cover_letter='I love frontend development with React'
        )
        
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-list')
        
        # Search by job title
        response = self.client.get(url, {'search': 'Software'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(app1.id))
        
        # Search by cover letter content
        response = self.client.get(url, {'search': 'Python'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(app1.id))
    
    def test_application_ordering(self):
        """Test application ordering"""
        app1 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post1,
            resume=self.resume,
            match_score=0.7
        )
        
        app2 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post2,
            resume=self.resume,
            match_score=0.9
        )
        
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-list')
        
        # Order by match score (descending)
        response = self.client.get(url, {'ordering': '-match_score'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['id'], str(app2.id))
        self.assertEqual(response.data['results'][1]['id'], str(app1.id))
        
        # Order by match score (ascending)
        response = self.client.get(url, {'ordering': 'match_score'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['id'], str(app1.id))
        self.assertEqual(response.data['results'][1]['id'], str(app2.id))


class ApplicationStatusManagementTest(APITestCase):
    """Test application status management functionality"""
    
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
            company_name='Test Company'
        )
        
        self.job_seeker_user = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        JobSeekerProfile.objects.create(user=self.job_seeker_user)
        
        # Create another recruiter for testing access control
        self.other_recruiter = User.objects.create_user(
            username='recruiter2',
            email='recruiter2@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        RecruiterProfile.objects.create(
            user=self.other_recruiter,
            company_name='Other Company'
        )
        
        # Create job post
        self.job_post = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Software Engineer',
            description='Test job description',
            requirements='Test requirements',
            location='San Francisco, CA',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker_user,
            original_filename='test_resume.pdf',
            file_size=1024,
            is_primary=True
        )
        
        # Create application
        self.application = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post,
            resume=self.resume,
            cover_letter='Test cover letter'
        )
        
        self.client = APIClient()
    
    def get_jwt_token(self, user):
        """Helper method to get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_update_status_success(self):
        """Test successful status update by recruiter"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-update-status', kwargs={'pk': self.application.pk})
        data = {
            'status': 'reviewed',
            'recruiter_notes': 'Good candidate, moving to next round'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify status was updated
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'reviewed')
        self.assertEqual(self.application.recruiter_notes, 'Good candidate, moving to next round')
    
    def test_update_status_invalid_status(self):
        """Test status update with invalid status"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-update-status', kwargs={'pk': self.application.pk})
        data = {'status': 'invalid_status'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid status', str(response.data))
    
    def test_update_status_wrong_recruiter(self):
        """Test that only job owner can update status"""
        token = self.get_jwt_token(self.other_recruiter)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-update-status', kwargs={'pk': self.application.pk})
        data = {'status': 'reviewed'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_status_job_seeker_forbidden(self):
        """Test that job seekers cannot update status"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-update-status', kwargs={'pk': self.application.pk})
        data = {'status': 'reviewed'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_all_status_transitions(self):
        """Test all valid status transitions"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-update-status', kwargs={'pk': self.application.pk})
        
        valid_statuses = [
            'reviewed', 'shortlisted', 'interview_scheduled',
            'interviewed', 'hired'
        ]
        
        for status_choice in valid_statuses:
            data = {'status': status_choice}
            response = self.client.patch(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.application.refresh_from_db()
            self.assertEqual(self.application.status, status_choice)
        
        # Test rejection
        data = {'status': 'rejected', 'recruiter_notes': 'Not a good fit'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'rejected')
        self.assertEqual(self.application.recruiter_notes, 'Not a good fit')


class ApplicationHistoryTest(APITestCase):
    """Test application history and tracking functionality"""
    
    def setUp(self):
        # Create test users
        self.job_seeker_user = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        JobSeekerProfile.objects.create(user=self.job_seeker_user)
        
        self.recruiter_user = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        RecruiterProfile.objects.create(
            user=self.recruiter_user,
            company_name='Test Company'
        )
        
        # Create job posts
        self.job_post1 = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Software Engineer',
            description='Test description',
            requirements='Test requirements',
            location='San Francisco, CA',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django'
        )
        
        self.job_post2 = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Frontend Developer',
            description='Frontend description',
            requirements='Frontend requirements',
            location='Remote',
            job_type='full_time',
            experience_level='entry',
            skills_required='React, JavaScript'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker_user,
            original_filename='test_resume.pdf',
            file_size=1024,
            is_primary=True
        )
        
        # Create applications with different statuses
        self.app1 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post1,
            resume=self.resume,
            status='pending',
            applied_at=timezone.now() - timedelta(days=5)
        )
        
        self.app2 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post2,
            resume=self.resume,
            status='reviewed',
            applied_at=timezone.now() - timedelta(days=10)
        )
        
        # Create a third job post for the third application
        self.job_post3 = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Data Scientist',
            description='Data science description',
            requirements='Data science requirements',
            location='Boston',
            job_type='full_time',
            experience_level='senior',
            skills_required='Python, Machine Learning'
        )
        
        self.app3 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post3,
            resume=self.resume,
            status='hired',
            applied_at=timezone.now() - timedelta(days=45)
        )
        
        self.client = APIClient()
    
    def get_jwt_token(self, user):
        """Helper method to get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_application_history_success(self):
        """Test successful application history retrieval"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('applications', response.data)
        self.assertIn('status_summary', response.data)
        self.assertIn('recent_count', response.data)
        self.assertIn('total_count', response.data)
        
        # Check total count
        self.assertEqual(response.data['total_count'], 3)
        
        # Check recent count (last 30 days)
        self.assertEqual(response.data['recent_count'], 2)  # app1 and app2
        
        # Check status summary
        status_summary = {item['status']: item['count'] for item in response.data['status_summary']}
        self.assertEqual(status_summary.get('pending', 0), 1)
        self.assertEqual(status_summary.get('reviewed', 0), 1)
        self.assertEqual(status_summary.get('hired', 0), 1)
    
    def test_application_history_recruiter_forbidden(self):
        """Test that recruiters cannot access job seeker history"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_application_timeline(self):
        """Test application timeline functionality"""
        # Create AI analysis for the application
        AIAnalysisResult.objects.create(
            application=self.app1,
            analysis_type='job_match',
            input_data='Test input',
            analysis_result={'test': 'result'},
            confidence_score=0.85
        )
        
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-timeline', kwargs={'pk': self.app1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('application_id', response.data)
        self.assertIn('timeline', response.data)
        
        # Check timeline events
        timeline = response.data['timeline']
        self.assertGreater(len(timeline), 0)
        
        # Check that application submission event exists
        submission_events = [event for event in timeline if event['event'] == 'Application Submitted']
        self.assertEqual(len(submission_events), 1)
        
        # Check that AI analysis event exists
        ai_events = [event for event in timeline if event['event'] == 'AI Analysis Completed']
        self.assertEqual(len(ai_events), 1)


class ApplicationAnalyticsTest(APITestCase):
    """Test application analytics and reporting functionality"""
    
    def setUp(self):
        # Create test users
        self.recruiter_user = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        RecruiterProfile.objects.create(
            user=self.recruiter_user,
            company_name='Test Company'
        )
        
        self.job_seeker_user = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        JobSeekerProfile.objects.create(user=self.job_seeker_user)
        
        # Create job posts
        self.job_post1 = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Software Engineer',
            description='Test description',
            requirements='Test requirements',
            location='San Francisco, CA',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django'
        )
        
        self.job_post2 = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Frontend Developer',
            description='Frontend description',
            requirements='Frontend requirements',
            location='Remote',
            job_type='full_time',
            experience_level='entry',
            skills_required='React, JavaScript'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker_user,
            original_filename='test_resume.pdf',
            file_size=1024,
            is_primary=True
        )
        
        # Create applications with different statuses and match scores
        # Note: Each application must be for a different job due to unique constraint
        self.app1 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post1,
            resume=self.resume,
            status='pending',
            match_score=0.85,
            applied_at=timezone.now() - timedelta(days=5)
        )
        
        self.app2 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post2,
            resume=self.resume,
            status='reviewed',
            match_score=0.75,
            applied_at=timezone.now() - timedelta(days=10),
            updated_at=timezone.now() - timedelta(days=9)
        )
        
        # Create a third job post for the third application
        self.job_post3 = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Data Scientist',
            description='Data science description',
            requirements='Data science requirements',
            location='Boston',
            job_type='full_time',
            experience_level='senior',
            skills_required='Python, Machine Learning'
        )
        
        self.app3 = Application.objects.create(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post3,
            resume=self.resume,
            status='hired',
            match_score=0.95,
            applied_at=timezone.now() - timedelta(days=15),
            updated_at=timezone.now() - timedelta(days=5)
        )
        
        self.client = APIClient()
    
    def get_jwt_token(self, user):
        """Helper method to get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_application_analytics_success(self):
        """Test successful application analytics retrieval"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        expected_keys = [
            'total_applications', 'status_distribution', 'applications_over_time',
            'top_jobs', 'average_match_score', 'match_score_distribution',
            'average_response_time_hours', 'total_response_times'
        ]
        
        for key in expected_keys:
            self.assertIn(key, response.data)
        
        # Check total applications
        self.assertEqual(response.data['total_applications'], 3)
        
        # Check status distribution
        status_dist = {item['status']: item['count'] for item in response.data['status_distribution']}
        self.assertEqual(status_dist.get('pending', 0), 1)
        self.assertEqual(status_dist.get('reviewed', 0), 1)
        self.assertEqual(status_dist.get('hired', 0), 1)
        
        # Check average match score
        expected_avg = (0.85 + 0.75 + 0.95) / 3
        self.assertEqual(response.data['average_match_score'], round(expected_avg, 2))
        
        # Check top jobs
        top_jobs = response.data['top_jobs']
        self.assertGreater(len(top_jobs), 0)
        
        # Check match score distribution
        match_dist = response.data['match_score_distribution']
        self.assertEqual(len(match_dist), 5)  # 5 ranges
    
    def test_application_analytics_job_seeker_forbidden(self):
        """Test that job seekers cannot access recruiter analytics"""
        token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_application_export(self):
        """Test application data export functionality"""
        token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('application-export')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="applications.csv"', response['Content-Disposition'])
        
        # Check CSV content
        content = response.content.decode('utf-8')
        lines = content.strip().split('\n')
        
        # Check header
        header = lines[0]
        expected_columns = [
            'Application ID', 'Job Title', 'Company', 'Applicant', 'Status',
            'Applied Date', 'Match Score', 'Cover Letter Preview'
        ]
        for column in expected_columns:
            self.assertIn(column, header)
        
        # Check data rows (should have 3 applications)
        self.assertEqual(len(lines), 4)  # Header + 3 data rows


class ApplicationWorkflowIntegrationTest(APITestCase):
    """Integration tests for complete application workflow"""
    
    def setUp(self):
        # Create test users
        self.recruiter_user = User.objects.create_user(
            username='recruiter1',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        RecruiterProfile.objects.create(
            user=self.recruiter_user,
            company_name='Test Company'
        )
        
        self.job_seeker_user = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        JobSeekerProfile.objects.create(user=self.job_seeker_user)
        
        # Create job post
        self.job_post = JobPost.objects.create(
            recruiter=self.recruiter_user,
            title='Software Engineer',
            description='Test job description',
            requirements='Test requirements',
            location='San Francisco, CA',
            job_type='full_time',
            experience_level='mid',
            skills_required='Python, Django'
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker_user,
            original_filename='test_resume.pdf',
            file_size=1024,
            is_primary=True
        )
        
        self.client = APIClient()
    
    def get_jwt_token(self, user):
        """Helper method to get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    @patch('matcher.utils.calculate_match_score')
    @patch('matcher.utils.analyze_job_match')
    def test_complete_application_workflow(self, mock_analyze, mock_calculate):
        """Test complete application workflow from creation to hiring"""
        mock_calculate.return_value = 0.85
        mock_analyze.return_value = {
            'matching_skills': ['Python', 'Django'],
            'missing_skills': ['React'],
            'recommendations': 'Good match'
        }
        
        # Step 1: Job seeker applies for job
        job_seeker_token = self.get_jwt_token(self.job_seeker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {job_seeker_token}')
        
        apply_url = reverse('application-list')
        apply_data = {
            'job_post': str(self.job_post.id),
            'cover_letter': 'I am very interested in this position.'
        }
        
        response = self.client.post(apply_url, apply_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        application_id = response.data['id']
        
        # Step 2: Recruiter reviews applications
        recruiter_token = self.get_jwt_token(self.recruiter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {recruiter_token}')
        
        list_url = reverse('application-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Step 3: Recruiter updates status to reviewed
        update_url = reverse('application-update-status', kwargs={'pk': application_id})
        update_data = {
            'status': 'reviewed',
            'recruiter_notes': 'Good candidate, proceeding to next round'
        }
        
        response = self.client.patch(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'reviewed')
        
        # Step 4: Job seeker checks application history
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {job_seeker_token}')
        
        history_url = reverse('application-history')
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 1)
        
        # Check status summary
        status_summary = {item['status']: item['count'] for item in response.data['status_summary']}
        self.assertEqual(status_summary.get('reviewed', 0), 1)
        
        # Step 5: Check application timeline
        timeline_url = reverse('application-timeline', kwargs={'pk': application_id})
        response = self.client.get(timeline_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        timeline = response.data['timeline']
        self.assertGreater(len(timeline), 1)  # Should have submission + status update events
        
        # Step 6: Recruiter continues workflow - shortlist
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {recruiter_token}')
        
        update_data = {'status': 'shortlisted'}
        response = self.client.patch(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 7: Schedule interview
        update_data = {'status': 'interview_scheduled'}
        response = self.client.patch(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 8: Mark as interviewed
        update_data = {'status': 'interviewed'}
        response = self.client.patch(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 9: Final decision - hire
        update_data = {
            'status': 'hired',
            'recruiter_notes': 'Excellent candidate, offering position'
        }
        response = self.client.patch(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'hired')
        
        # Step 10: Recruiter checks analytics
        analytics_url = reverse('application-analytics')
        response = self.client.get(analytics_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should show 1 hired application
        status_dist = {item['status']: item['count'] for item in response.data['status_distribution']}
        self.assertEqual(status_dist.get('hired', 0), 1)
        
        # Step 11: Export applications data
        export_url = reverse('application-export')
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')