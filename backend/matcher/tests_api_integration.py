"""
Comprehensive API integration tests for HireWise backend.
Tests complete user workflows and API endpoint interactions.
"""
import pytest
import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from matcher.models import JobPost, Application, Resume
from factories import (
    UserFactory, 
    JobSeekerProfileFactory, 
    RecruiterProfileFactory,
    JobPostFactory,
    ResumeFactory,
    ApplicationFactory
)

User = get_user_model()


@pytest.mark.integration
class TestAuthenticationWorkflow(APITestCase):
    """Test complete authentication workflow."""
    
    def test_user_registration_and_login_workflow(self):
        """Test complete user registration and login process."""
        # Test job seeker registration
        registration_data = {
            'username': 'testjobseeker',
            'email': 'jobseeker@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'user_type': 'job_seeker',
            'phone_number': '+1234567890'
        }
        
        response = self.client.post('/api/auth/jwt/register/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Test login
        login_data = {
            'username': 'testjobseeker',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/auth/jwt/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Test token refresh
        refresh_token = response.data['refresh']
        response = self.client.post('/api/auth/token/refresh/', {'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_recruiter_registration_workflow(self):
        """Test recruiter registration with profile creation."""
        registration_data = {
            'username': 'testrecruiter',
            'email': 'recruiter@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'user_type': 'recruiter',
            'phone_number': '+1234567891'
        }
        
        response = self.client.post('/api/auth/jwt/register/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created with correct type
        user = User.objects.get(username='testrecruiter')
        self.assertEqual(user.user_type, 'recruiter')


@pytest.mark.integration
class TestJobManagementWorkflow(APITestCase):
    """Test complete job management workflow."""
    
    def setUp(self):
        self.recruiter = UserFactory(user_type='recruiter')
        self.recruiter_profile = RecruiterProfileFactory(user=self.recruiter)
        self.job_seeker = UserFactory(user_type='job_seeker')
        self.job_seeker_profile = JobSeekerProfileFactory(user=self.job_seeker)
    
    def test_job_posting_workflow(self):
        """Test complete job posting workflow."""
        # Authenticate as recruiter
        self.client.force_authenticate(user=self.recruiter)
        
        # Create job post
        job_data = {
            'title': 'Senior Python Developer',
            'description': 'We are looking for an experienced Python developer...',
            'requirements': 'Python, Django, REST APIs, 5+ years experience',
            'location': 'San Francisco, CA',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'salary_min': 120000,
            'salary_max': 150000,
            'skills_required': 'Python,Django,REST APIs,PostgreSQL'
        }
        
        response = self.client.post('/api/job-posts/', job_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job_id = response.data['id']
        
        # Verify job was created
        job = JobPost.objects.get(id=job_id)
        self.assertEqual(job.title, 'Senior Python Developer')
        self.assertEqual(job.recruiter, self.recruiter)
        
        # Test job listing (public access)
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/job-posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test job search
        response = self.client.get('/api/job-posts/?search=Python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test job filtering
        response = self.client.get('/api/job-posts/?location=San Francisco')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_job_application_workflow(self):
        """Test complete job application workflow."""
        # Create a job post
        job_post = JobPostFactory(recruiter=self.recruiter)
        
        # Create resume for job seeker
        self.client.force_authenticate(user=self.job_seeker)
        
        # Upload resume first
        resume_data = {
            'original_filename': 'test_resume.pdf',
            'parsed_text': 'John Doe\nSoftware Engineer\nPython, Django, React',
            'is_primary': True
        }
        
        response = self.client.post('/api/resumes/', resume_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resume_id = response.data['id']
        
        # Apply to job
        application_data = {
            'job_post': str(job_post.id),
            'resume': resume_id,
            'cover_letter': 'I am very interested in this position...'
        }
        
        response = self.client.post('/api/applications/', application_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify application was created
        application = Application.objects.get(id=response.data['id'])
        self.assertEqual(application.job_seeker, self.job_seeker)
        self.assertEqual(application.job_post, job_post)
        
        # Test application listing for job seeker
        response = self.client.get('/api/applications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test application management for recruiter
        self.client.force_authenticate(user=self.recruiter)
        response = self.client.get(f'/api/applications/?job_post={job_post.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Update application status
        application_id = response.data['results'][0]['id']
        update_data = {
            'status': 'interview',
            'recruiter_notes': 'Good candidate, schedule interview'
        }
        
        response = self.client.patch(f'/api/applications/{application_id}/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'interview')


@pytest.mark.integration
class TestResumeParsingWorkflow(APITestCase):
    """Test AI-powered resume parsing workflow."""
    
    def setUp(self):
        self.job_seeker = UserFactory(user_type='job_seeker')
        self.job_seeker_profile = JobSeekerProfileFactory(user=self.job_seeker)
    
    @pytest.mark.ml
    def test_resume_parsing_workflow(self):
        """Test complete resume parsing workflow."""
        self.client.force_authenticate(user=self.job_seeker)
        
        # Mock file upload (in real test, would use actual file)
        resume_content = """
        John Doe
        Software Engineer
        
        Experience:
        - 5 years of Python development
        - Django and Flask frameworks
        - React and JavaScript frontend
        
        Skills: Python, Django, React, JavaScript, SQL, Git
        
        Education:
        Bachelor of Science in Computer Science
        University of Technology, 2018
        """
        
        # Test resume parsing endpoint
        parse_data = {
            'text_content': resume_content
        }
        
        response = self.client.post('/api/parse-resume/', parse_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify parsed data structure
        self.assertIn('parsed_text', response.data)
        self.assertIn('key_skills', response.data)
        self.assertIn('summary', response.data)
    
    @pytest.mark.ml
    def test_match_score_calculation_workflow(self):
        """Test job matching score calculation workflow."""
        # Create job post and resume
        recruiter = UserFactory(user_type='recruiter')
        job_post = JobPostFactory(
            recruiter=recruiter,
            title='Python Developer',
            skills_required='Python,Django,React,SQL'
        )
        
        resume = ResumeFactory(
            job_seeker=self.job_seeker,
            parsed_text='Python developer with Django and React experience'
        )
        
        self.client.force_authenticate(user=self.job_seeker)
        
        # Calculate match score
        match_data = {
            'resume_id': str(resume.id),
            'job_id': str(job_post.id)
        }
        
        response = self.client.post('/api/calculate-match-score/', match_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify match score response
        self.assertIn('score', response.data)
        self.assertIsInstance(response.data['score'], (int, float))
        self.assertGreaterEqual(response.data['score'], 0)
        self.assertLessEqual(response.data['score'], 100)


@pytest.mark.integration
class TestProfileManagementWorkflow(APITestCase):
    """Test user profile management workflow."""
    
    def setUp(self):
        self.job_seeker = UserFactory(user_type='job_seeker')
        self.recruiter = UserFactory(user_type='recruiter')
    
    def test_job_seeker_profile_workflow(self):
        """Test job seeker profile management."""
        self.client.force_authenticate(user=self.job_seeker)
        
        # Create profile
        profile_data = {
            'location': 'New York, NY',
            'experience_level': 'mid',
            'current_position': 'Software Engineer',
            'expected_salary': 90000,
            'skills': 'Python,Django,React,JavaScript',
            'bio': 'Passionate software engineer with 3 years of experience',
            'linkedin_url': 'https://linkedin.com/in/johndoe',
            'github_url': 'https://github.com/johndoe',
            'availability': True
        }
        
        response = self.client.post('/api/job-seeker-profiles/', profile_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Update profile
        update_data = {
            'expected_salary': 95000,
            'current_position': 'Senior Software Engineer'
        }
        
        profile_id = response.data['id']
        response = self.client.patch(f'/api/job-seeker-profiles/{profile_id}/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['expected_salary'], 95000)
    
    def test_recruiter_profile_workflow(self):
        """Test recruiter profile management."""
        self.client.force_authenticate(user=self.recruiter)
        
        # Create profile
        profile_data = {
            'company_name': 'Tech Innovations Inc',
            'company_website': 'https://techinnovations.com',
            'company_size': '51-200',
            'industry': 'Technology',
            'company_description': 'Leading technology company specializing in AI solutions',
            'location': 'San Francisco, CA'
        }
        
        response = self.client.post('/api/recruiter-profiles/', profile_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify profile data
        self.assertEqual(response.data['company_name'], 'Tech Innovations Inc')
        self.assertEqual(response.data['industry'], 'Technology')


@pytest.mark.integration
class TestFileUploadWorkflow(APITestCase):
    """Test secure file upload workflow."""
    
    def setUp(self):
        self.job_seeker = UserFactory(user_type='job_seeker')
    
    def test_secure_file_upload_workflow(self):
        """Test secure file upload and validation."""
        self.client.force_authenticate(user=self.job_seeker)
        
        # Test file validation info endpoint
        response = self.client.get('/api/files/validation-info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('max_file_size', response.data)
        self.assertIn('allowed_extensions', response.data)
        
        # Test file listing
        response = self.client.get('/api/files/list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)


@pytest.mark.integration
class TestAPIVersioningWorkflow(APITestCase):
    """Test API versioning functionality."""
    
    def test_api_versioning(self):
        """Test that API versioning works correctly."""
        # Test v1 endpoint
        response = self.client.get('/api/v1/job-posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test default version (should be v1)
        response = self.client.get('/api/job-posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_api_documentation_endpoints(self):
        """Test that API documentation endpoints are accessible."""
        # Test schema endpoint
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test Swagger UI
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test ReDoc
        response = self.client.get('/api/redoc/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@pytest.mark.integration
class TestErrorHandlingWorkflow(APITestCase):
    """Test API error handling and validation."""
    
    def test_authentication_errors(self):
        """Test authentication error handling."""
        # Test unauthenticated access to protected endpoint
        response = self.client.post('/api/job-posts/', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get('/api/applications/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_validation_errors(self):
        """Test input validation error handling."""
        user = UserFactory(user_type='recruiter')
        self.client.force_authenticate(user=user)
        
        # Test invalid job post data
        invalid_data = {
            'title': '',  # Required field
            'salary_min': 'invalid',  # Should be integer
        }
        
        response = self.client.post('/api/job-posts/', invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_permission_errors(self):
        """Test permission error handling."""
        job_seeker = UserFactory(user_type='job_seeker')
        recruiter = UserFactory(user_type='recruiter')
        job_post = JobPostFactory(recruiter=recruiter)
        
        # Job seeker trying to update recruiter's job post
        self.client.force_authenticate(user=job_seeker)
        response = self.client.patch(f'/api/job-posts/{job_post.id}/', {'title': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@pytest.mark.integration
class TestCompleteUserJourney(APITestCase):
    """Test complete user journey from registration to job application."""
    
    def test_complete_job_seeker_journey(self):
        """Test complete job seeker journey."""
        # 1. Register as job seeker
        registration_data = {
            'username': 'jobseeker_journey',
            'email': 'journey@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Journey',
            'last_name': 'Test',
            'user_type': 'job_seeker',
            'phone_number': '+1234567890'
        }
        
        response = self.client.post('/api/auth/jwt/register/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        access_token = response.data['access']
        
        # 2. Create profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_data = {
            'location': 'Boston, MA',
            'experience_level': 'mid',
            'current_position': 'Software Developer',
            'expected_salary': 85000,
            'skills': 'Python,Django,React',
            'bio': 'Experienced developer looking for new opportunities'
        }
        
        response = self.client.post('/api/job-seeker-profiles/', profile_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. Upload resume
        resume_data = {
            'original_filename': 'journey_resume.pdf',
            'parsed_text': 'Journey Test\nSoftware Developer\nPython, Django, React experience',
            'is_primary': True
        }
        
        response = self.client.post('/api/resumes/', resume_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resume_id = response.data['id']
        
        # 4. Browse jobs
        # First create a job (as recruiter)
        recruiter = UserFactory(user_type='recruiter')
        job_post = JobPostFactory(
            recruiter=recruiter,
            title='Python Developer',
            skills_required='Python,Django'
        )
        
        response = self.client.get('/api/job-posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        
        # 5. Apply to job
        application_data = {
            'job_post': str(job_post.id),
            'resume': resume_id,
            'cover_letter': 'I am very interested in this Python developer position.'
        }
        
        response = self.client.post('/api/applications/', application_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 6. Check application status
        response = self.client.get('/api/applications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'pending')
    
    def test_complete_recruiter_journey(self):
        """Test complete recruiter journey."""
        # 1. Register as recruiter
        registration_data = {
            'username': 'recruiter_journey',
            'email': 'recruiter_journey@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Recruiter',
            'last_name': 'Journey',
            'user_type': 'recruiter',
            'phone_number': '+1234567891'
        }
        
        response = self.client.post('/api/auth/jwt/register/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        access_token = response.data['access']
        
        # 2. Create company profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_data = {
            'company_name': 'Journey Tech',
            'company_website': 'https://journeytech.com',
            'company_size': '11-50',
            'industry': 'Technology',
            'company_description': 'Innovative tech startup',
            'location': 'Austin, TX'
        }
        
        response = self.client.post('/api/recruiter-profiles/', profile_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. Post job
        job_data = {
            'title': 'Full Stack Developer',
            'description': 'Looking for a talented full stack developer...',
            'requirements': 'Python, Django, React, 3+ years experience',
            'location': 'Austin, TX',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'salary_min': 80000,
            'salary_max': 100000,
            'skills_required': 'Python,Django,React,JavaScript'
        }
        
        response = self.client.post('/api/job-posts/', job_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job_id = response.data['id']
        
        # 4. Create a job seeker and application for testing
        job_seeker = UserFactory(user_type='job_seeker')
        resume = ResumeFactory(job_seeker=job_seeker)
        application = ApplicationFactory(
            job_seeker=job_seeker,
            job_post_id=job_id,
            resume=resume
        )
        
        # 5. Review applications
        response = self.client.get(f'/api/applications/?job_post={job_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 6. Update application status
        if response.data['results']:
            application_id = response.data['results'][0]['id']
            update_data = {
                'status': 'interview',
                'recruiter_notes': 'Promising candidate'
            }
            
            response = self.client.patch(f'/api/applications/{application_id}/', update_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)