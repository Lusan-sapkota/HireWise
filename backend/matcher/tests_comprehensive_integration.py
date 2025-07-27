"""
Comprehensive integration tests for all HireWise API endpoints.

This test suite covers complete user workflows and endpoint integration,
ensuring all API endpoints work correctly together.
"""

import pytest
import json
import tempfile
import os
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from django.utils import timezone

from .models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost,
    Application, AIAnalysisResult, InterviewSession, Skill, UserSkill,
    EmailVerificationToken, PasswordResetToken
)
from .factories import (
    UserFactory, JobSeekerProfileFactory, RecruiterProfileFactory,
    ResumeFactory, JobPostFactory, ApplicationFactory
)


class BaseIntegrationTestCase(APITestCase):
    """Base class for integration tests with common setup."""
    
    def setUp(self):
        """Set up test data and authentication."""
        self.client = APIClient()
        
        # Create test users
        self.job_seeker_user = UserFactory(user_type='job_seeker')
        self.recruiter_user = UserFactory(user_type='recruiter')
        self.admin_user = UserFactory(user_type='admin', is_staff=True)
        
        # Create profiles
        self.job_seeker_profile = JobSeekerProfileFactory(user=self.job_seeker_user)
        self.recruiter_profile = RecruiterProfileFactory(user=self.recruiter_user)
        
        # Create test job posts
        self.job_post = JobPostFactory(recruiter=self.recruiter_user)
        self.inactive_job_post = JobPostFactory(recruiter=self.recruiter_user, is_active=False)
        
        # Create test resume
        self.resume = ResumeFactory(job_seeker=self.job_seeker_user)
        
        # Create test skills
        self.skills = [
            Skill.objects.create(name='Python', category='programming'),
            Skill.objects.create(name='Django', category='framework'),
            Skill.objects.create(name='JavaScript', category='programming'),
        ]
    
    def get_jwt_token(self, user):
        """Get JWT token for user authentication."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate_user(self, user):
        """Authenticate user with JWT token."""
        token = self.get_jwt_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token
    
    def create_test_file(self, filename='test_resume.pdf', content=b'test content'):
        """Create a test file for upload tests."""
        return SimpleUploadedFile(filename, content, content_type='application/pdf')


class AuthenticationIntegrationTests(BaseIntegrationTestCase):
    """Integration tests for authentication workflows."""
    
    def test_complete_registration_workflow(self):
        """Test complete user registration workflow."""
        # Test job seeker registration
        registration_data = {
            'username': 'new_jobseeker',
            'email': 'jobseeker@test.com',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123',
            'first_name': 'John',
            'last_name': 'Doe',
            'user_type': 'job_seeker',
            'phone_number': '+1234567890'
        }
        
        response = self.client.post('/api/v1/auth/jwt/register/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
        
        # Verify user was created
        user = User.objects.get(username='new_jobseeker')
        self.assertEqual(user.user_type, 'job_seeker')
        self.assertFalse(user.is_verified)
        
        # Test recruiter registration
        recruiter_data = {
            'username': 'new_recruiter',
            'email': 'recruiter@test.com',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'user_type': 'recruiter',
            'phone_number': '+1234567891'
        }
        
        response = self.client.post('/api/v1/auth/jwt/register/', recruiter_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify recruiter profile was created
        recruiter = User.objects.get(username='new_recruiter')
        self.assertTrue(hasattr(recruiter, 'recruiterprofile'))
    
    def test_login_logout_workflow(self):
        """Test login and logout workflow."""
        # Test login
        login_data = {
            'username': self.job_seeker_user.username,
            'password': 'testpassword123'
        }
        
        response = self.client.post('/api/v1/auth/jwt/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        
        # Test authenticated request
        token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        profile_response = self.client.get('/api/v1/auth/profile/')
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        
        # Test logout
        refresh_token = response.data['tokens']['refresh']
        logout_response = self.client.post('/api/v1/auth/jwt/logout/', {
            'refresh_token': refresh_token
        })
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
    
    def test_token_refresh_workflow(self):
        """Test JWT token refresh workflow."""
        # Login to get tokens
        login_data = {
            'username': self.job_seeker_user.username,
            'password': 'testpassword123'
        }
        
        login_response = self.client.post('/api/v1/auth/jwt/login/', login_data)
        refresh_token = login_response.data['tokens']['refresh']
        
        # Test token refresh
        refresh_response = self.client.post('/api/v1/auth/token/refresh/', {
            'refresh': refresh_token
        })
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
    
    def test_password_reset_workflow(self):
        """Test password reset workflow."""
        # Request password reset
        reset_request_data = {
            'email': self.job_seeker_user.email
        }
        
        response = self.client.post('/api/v1/auth/request-password-reset/', reset_request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify token was created
        token = PasswordResetToken.objects.get(user=self.job_seeker_user)
        self.assertIsNotNone(token)
        
        # Test password reset confirmation
        reset_data = {
            'token': token.token,
            'new_password': 'newpassword123'
        }
        
        reset_response = self.client.post('/api/v1/auth/reset-password/', reset_data)
        self.assertEqual(reset_response.status_code, status.HTTP_200_OK)


class JobManagementIntegrationTests(BaseIntegrationTestCase):
    """Integration tests for job management workflows."""
    
    def test_complete_job_posting_workflow(self):
        """Test complete job posting workflow."""
        self.authenticate_user(self.recruiter_user)
        
        # Create job posting
        job_data = {
            'title': 'Senior Python Developer',
            'description': 'We are looking for an experienced Python developer...',
            'location': 'San Francisco, CA',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'salary_min': 120000,
            'salary_max': 180000,
            'skills_required': ['Python', 'Django', 'PostgreSQL'],
            'requirements': 'Bachelor\'s degree required'
        }
        
        response = self.client.post('/api/v1/job-posts/', job_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job_id = response.data['id']
        
        # Test job retrieval
        get_response = self.client.get(f'/api/v1/job-posts/{job_id}/')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['title'], job_data['title'])
        
        # Test job update
        update_data = {
            'title': 'Senior Python Developer - Updated',
            'salary_max': 200000
        }
        
        update_response = self.client.patch(f'/api/v1/job-posts/{job_id}/', update_data)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['title'], update_data['title'])
        
        # Test job deletion
        delete_response = self.client.delete(f'/api/v1/job-posts/{job_id}/')
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_job_search_and_filtering(self):
        """Test job search and filtering functionality."""
        # Create additional test jobs
        JobPostFactory(
            recruiter=self.recruiter_user,
            title='Frontend Developer',
            location='New York, NY',
            job_type='full_time',
            skills_required=['JavaScript', 'React', 'CSS']
        )
        JobPostFactory(
            recruiter=self.recruiter_user,
            title='Backend Developer',
            location='Remote',
            job_type='contract',
            skills_required=['Python', 'Django', 'API']
        )
        
        self.authenticate_user(self.job_seeker_user)
        
        # Test search by title
        response = self.client.get('/api/v1/job-posts/?search=Frontend')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('Frontend', response.data['results'][0]['title'])
        
        # Test filter by location
        response = self.client.get('/api/v1/job-posts/?location=Remote')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test filter by job type
        response = self.client.get('/api/v1/job-posts/?job_type=contract')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test filter by skills
        response = self.client.get('/api/v1/job-posts/?skills=Python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) >= 1)
    
    def test_job_analytics_workflow(self):
        """Test job analytics and view tracking."""
        self.authenticate_user(self.job_seeker_user)
        
        # View job multiple times
        job_id = self.job_post.id
        for _ in range(3):
            response = self.client.get(f'/api/v1/job-posts/{job_id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check analytics as recruiter
        self.authenticate_user(self.recruiter_user)
        
        analytics_response = self.client.get('/api/v1/dashboard/stats/')
        self.assertEqual(analytics_response.status_code, status.HTTP_200_OK)
        self.assertIn('total_jobs', analytics_response.data)
        self.assertIn('total_views', analytics_response.data)


class ApplicationWorkflowIntegrationTests(BaseIntegrationTestCase):
    """Integration tests for job application workflows."""
    
    def test_complete_application_workflow(self):
        """Test complete job application workflow."""
        self.authenticate_user(self.job_seeker_user)
        
        # Apply to job
        application_data = {
            'job_post': str(self.job_post.id),
            'resume': str(self.resume.id),
            'cover_letter': 'I am very interested in this position...'
        }
        
        response = self.client.post('/api/v1/applications/', application_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        
        application_id = response.data['id']
        
        # Check application in job seeker's list
        applications_response = self.client.get('/api/v1/applications/')
        self.assertEqual(applications_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(applications_response.data['results']), 1)
        
        # Switch to recruiter and update application status
        self.authenticate_user(self.recruiter_user)
        
        status_update_data = {
            'status': 'interview_scheduled',
            'recruiter_notes': 'Please schedule interview for next week'
        }
        
        update_response = self.client.patch(f'/api/v1/applications/{application_id}/', status_update_data)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['status'], 'interview_scheduled')
        
        # Test duplicate application prevention
        self.authenticate_user(self.job_seeker_user)
        
        duplicate_response = self.client.post('/api/v1/applications/', application_data)
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_application_permissions(self):
        """Test application access permissions."""
        # Create application
        application = ApplicationFactory(
            job_seeker=self.job_seeker_user,
            job_post=self.job_post,
            resume=self.resume
        )
        
        # Test job seeker can view their application
        self.authenticate_user(self.job_seeker_user)
        response = self.client.get(f'/api/v1/applications/{application.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test recruiter can view applications for their jobs
        self.authenticate_user(self.recruiter_user)
        response = self.client.get(f'/api/v1/applications/{application.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test other users cannot view the application
        other_user = UserFactory(user_type='job_seeker')
        self.authenticate_user(other_user)
        response = self.client.get(f'/api/v1/applications/{application.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ResumeParsingIntegrationTests(BaseIntegrationTestCase):
    """Integration tests for resume parsing workflows."""
    
    @patch('matcher.services.parse_resume_with_gemini')
    def test_resume_upload_and_parsing_workflow(self, mock_parse):
        """Test complete resume upload and parsing workflow."""
        # Mock Gemini API response
        mock_parse.return_value = {
            'parsed_text': 'John Doe\nSoftware Engineer\n...',
            'parsed_data': {
                'personal_info': {
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'phone': '+1234567890'
                },
                'skills': ['Python', 'Django', 'JavaScript'],
                'experience': [
                    {
                        'company': 'Tech Corp',
                        'position': 'Software Engineer',
                        'duration': '2020-2024'
                    }
                ]
            },
            'confidence_score': 0.95
        }
        
        self.authenticate_user(self.job_seeker_user)
        
        # Upload and parse resume
        test_file = self.create_test_file('resume.pdf', b'PDF content here')
        
        response = self.client.post('/api/v1/parse-resume/', {
            'resume_file': test_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('parsed_data', response.data)
        self.assertIn('confidence_score', response.data)
        
        # Verify resume was saved
        resume = Resume.objects.filter(job_seeker=self.job_seeker_user).last()
        self.assertIsNotNone(resume)
        self.assertEqual(resume.original_filename, 'resume.pdf')
    
    @patch('matcher.tasks.parse_resume_async.delay')
    def test_async_resume_parsing_workflow(self, mock_task):
        """Test asynchronous resume parsing workflow."""
        # Mock Celery task
        mock_task.return_value.id = 'test-task-id'
        
        self.authenticate_user(self.job_seeker_user)
        
        # Submit async parsing request
        test_file = self.create_test_file('large_resume.pdf', b'Large PDF content' * 1000)
        
        response = self.client.post('/api/v1/parse-resume-async/', {
            'resume_file': test_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('task_id', response.data)
        
        # Check task status
        task_id = response.data['task_id']
        status_response = self.client.get(f'/api/v1/parse-task-status/{task_id}/')
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)


class MatchScoringIntegrationTests(BaseIntegrationTestCase):
    """Integration tests for job matching workflows."""
    
    @patch('matcher.services.calculate_match_score_with_ml')
    def test_match_score_calculation_workflow(self, mock_calculate):
        """Test match score calculation workflow."""
        # Mock ML model response
        mock_calculate.return_value = {
            'overall_score': 87.5,
            'breakdown': {
                'skills_match': 92.0,
                'experience_match': 85.0,
                'education_match': 88.0
            },
            'matching_skills': ['Python', 'Django'],
            'missing_skills': ['Docker', 'Kubernetes'],
            'recommendations': ['Consider learning containerization'],
            'confidence': 0.94
        }
        
        self.authenticate_user(self.job_seeker_user)
        
        # Calculate match score
        match_data = {
            'resume_id': str(self.resume.id),
            'job_id': str(self.job_post.id)
        }
        
        response = self.client.post('/api/v1/calculate-match-score/', match_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overall_score', response.data)
        self.assertIn('breakdown', response.data)
        self.assertIn('matching_skills', response.data)
        
        # Verify analysis result was saved
        analysis = AIAnalysisResult.objects.filter(
            resume=self.resume,
            job_post=self.job_post,
            analysis_type='match_score'
        ).first()
        self.assertIsNotNone(analysis)
    
    def test_batch_match_score_calculation(self):
        """Test batch match score calculation."""
        # Create additional jobs and resumes
        job2 = JobPostFactory(recruiter=self.recruiter_user)
        resume2 = ResumeFactory(job_seeker=self.job_seeker_user)
        
        self.authenticate_user(self.job_seeker_user)
        
        batch_data = {
            'resume_ids': [str(self.resume.id), str(resume2.id)],
            'job_ids': [str(self.job_post.id), str(job2.id)]
        }
        
        with patch('matcher.services.calculate_match_score_with_ml') as mock_calculate:
            mock_calculate.return_value = {'overall_score': 75.0}
            
            response = self.client.post('/api/v1/batch-calculate-match-scores/', batch_data)
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            self.assertIn('task_id', response.data)


class FileUploadIntegrationTests(BaseIntegrationTestCase):
    """Integration tests for secure file upload workflows."""
    
    def test_secure_file_upload_workflow(self):
        """Test secure file upload workflow."""
        self.authenticate_user(self.job_seeker_user)
        
        # Test valid file upload
        test_file = self.create_test_file('document.pdf', b'Valid PDF content')
        
        response = self.client.post('/api/v1/files/upload/', {
            'file': test_file,
            'file_type': 'resume'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('file_id', response.data)
        self.assertIn('secure_url', response.data)
        
        # Test file listing
        list_response = self.client.get('/api/v1/files/list/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data['results']), 1)
        
        # Test file deletion
        file_id = response.data['file_id']
        delete_response = self.client.delete(f'/api/v1/files/delete/{file_id}/')
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_file_validation_workflow(self):
        """Test file validation and security checks."""
        self.authenticate_user(self.job_seeker_user)
        
        # Test invalid file type
        invalid_file = self.create_test_file('malicious.exe', b'Executable content')
        
        response = self.client.post('/api/v1/files/upload/', {
            'file': invalid_file,
            'file_type': 'resume'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Test file size limit
        large_file = self.create_test_file('large.pdf', b'x' * (11 * 1024 * 1024))  # 11MB
        
        response = self.client.post('/api/v1/files/upload/', {
            'file': large_file,
            'file_type': 'resume'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


class ProfileManagementIntegrationTests(BaseIntegrationTestCase):
    """Integration tests for user profile management."""
    
    def test_job_seeker_profile_workflow(self):
        """Test job seeker profile management workflow."""
        self.authenticate_user(self.job_seeker_user)
        
        # Get current profile
        response = self.client.get('/api/v1/job-seeker-profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Update profile
        update_data = {
            'location': 'New York, NY',
            'experience_level': 'senior',
            'expected_salary': 150000,
            'skills': 'Python, Django, React, PostgreSQL',
            'bio': 'Experienced full-stack developer...'
        }
        
        update_response = self.client.patch('/api/v1/job-seeker-profiles/me/', update_data)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['location'], update_data['location'])
        
        # Test skills management
        skill_data = {
            'skill': self.skills[0].id,
            'proficiency_level': 'expert',
            'years_of_experience': 5
        }
        
        skill_response = self.client.post('/api/v1/user-skills/', skill_data)
        self.assertEqual(skill_response.status_code, status.HTTP_201_CREATED)
    
    def test_recruiter_profile_workflow(self):
        """Test recruiter profile management workflow."""
        self.authenticate_user(self.recruiter_user)
        
        # Get current profile
        response = self.client.get('/api/v1/recruiter-profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Update profile
        update_data = {
            'company_name': 'Updated Tech Corp',
            'company_website': 'https://updatedtechcorp.com',
            'company_size': '100-500',
            'industry': 'Software Development',
            'company_description': 'We are a leading software company...'
        }
        
        update_response = self.client.patch('/api/v1/recruiter-profiles/me/', update_data)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['company_name'], update_data['company_name'])


class DashboardIntegrationTests(BaseIntegrationTestCase):
    """Integration tests for dashboard functionality."""
    
    def test_job_seeker_dashboard_workflow(self):
        """Test job seeker dashboard workflow."""
        # Create some applications and activities
        ApplicationFactory(job_seeker=self.job_seeker_user, job_post=self.job_post)
        
        self.authenticate_user(self.job_seeker_user)
        
        # Get dashboard stats
        response = self.client.get('/api/v1/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_applications', response.data)
        self.assertIn('pending_applications', response.data)
        
        # Get job recommendations
        with patch('matcher.services.get_job_recommendations') as mock_recommendations:
            mock_recommendations.return_value = [
                {
                    'job': self.job_post,
                    'match_score': 85.0,
                    'reasons': ['Skills match', 'Experience level']
                }
            ]
            
            rec_response = self.client.get('/api/v1/recommendations/')
            self.assertEqual(rec_response.status_code, status.HTTP_200_OK)
            self.assertIn('recommendations', rec_response.data)
    
    def test_recruiter_dashboard_workflow(self):
        """Test recruiter dashboard workflow."""
        # Create some applications
        ApplicationFactory(job_post=self.job_post, job_seeker=self.job_seeker_user)
        
        self.authenticate_user(self.recruiter_user)
        
        # Get dashboard stats
        response = self.client.get('/api/v1/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_jobs', response.data)
        self.assertIn('total_applications', response.data)
        self.assertIn('total_views', response.data)


class APIVersioningIntegrationTests(BaseIntegrationTestCase):
    """Integration tests for API versioning."""
    
    def test_versioned_endpoints(self):
        """Test that versioned endpoints work correctly."""
        self.authenticate_user(self.job_seeker_user)
        
        # Test v1 endpoint
        response_v1 = self.client.get('/api/v1/job-posts/')
        self.assertEqual(response_v1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v1['API-Version'], 'v1')
        
        # Test default endpoint (should default to v1)
        response_default = self.client.get('/api/job-posts/')
        self.assertEqual(response_default.status_code, status.HTTP_200_OK)
    
    def test_api_documentation_endpoints(self):
        """Test API documentation endpoints."""
        # Test schema endpoint
        response = self.client.get('/api/v1/schema/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test Swagger UI
        response = self.client.get('/api/v1/docs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test ReDoc
        response = self.client.get('/api/v1/redoc/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ErrorHandlingIntegrationTests(BaseIntegrationTestCase):
    """Integration tests for error handling."""
    
    def test_authentication_errors(self):
        """Test authentication error handling."""
        # Test unauthenticated request
        response = self.client.get('/api/v1/job-seeker-profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        
        # Test invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        response = self.client.get('/api/v1/job-seeker-profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_permission_errors(self):
        """Test permission error handling."""
        # Job seeker trying to access recruiter endpoint
        self.authenticate_user(self.job_seeker_user)
        
        response = self.client.get('/api/v1/recruiter-profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
    
    def test_validation_errors(self):
        """Test validation error handling."""
        self.authenticate_user(self.recruiter_user)
        
        # Invalid job post data
        invalid_data = {
            'title': '',  # Required field
            'description': 'Test description',
            'invalid_field': 'should not be accepted'
        }
        
        response = self.client.post('/api/v1/job-posts/', invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data['error'])
    
    def test_not_found_errors(self):
        """Test 404 error handling."""
        self.authenticate_user(self.job_seeker_user)
        
        # Non-existent job post
        response = self.client.get('/api/v1/job-posts/non-existent-id/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)


@pytest.mark.integration
class PerformanceIntegrationTests(BaseIntegrationTestCase):
    """Integration tests for performance-critical endpoints."""
    
    def test_job_listing_performance(self):
        """Test job listing endpoint performance with large dataset."""
        # Create many job posts
        jobs = [JobPostFactory(recruiter=self.recruiter_user) for _ in range(100)]
        
        self.authenticate_user(self.job_seeker_user)
        
        import time
        start_time = time.time()
        
        response = self.client.get('/api/v1/job-posts/')
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 2.0)  # Should respond within 2 seconds
        self.assertEqual(len(response.data['results']), 20)  # Pagination limit
    
    def test_search_performance(self):
        """Test search endpoint performance."""
        # Create jobs with various titles and descriptions
        for i in range(50):
            JobPostFactory(
                recruiter=self.recruiter_user,
                title=f'Developer Position {i}',
                description=f'Looking for developer with skills {i}'
            )
        
        self.authenticate_user(self.job_seeker_user)
        
        import time
        start_time = time.time()
        
        response = self.client.get('/api/v1/job-posts/?search=Developer')
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 1.0)  # Search should be fast