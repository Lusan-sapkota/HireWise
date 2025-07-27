import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import Mock, patch
import csv
import io
from datetime import datetime, timedelta
from django.utils import timezone

from .models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost, 
    Application, AIAnalysisResult, InterviewSession, Skill, UserSkill,
    EmailVerificationToken, PasswordResetToken, JobAnalytics, JobView,
    Notification, NotificationPreference, NotificationTemplate
)
from .admin import (
    UserAdmin, JobSeekerProfileAdmin, RecruiterProfileAdmin, ResumeAdmin,
    JobPostAdmin, ApplicationAdmin, AIAnalysisResultAdmin, InterviewSessionAdmin,
    SkillAdmin, UserSkillAdmin, EmailVerificationTokenAdmin, PasswordResetTokenAdmin,
    JobAnalyticsAdmin, JobViewAdmin, NotificationAdmin, NotificationPreferenceAdmin,
    NotificationTemplateAdmin
)


class AdminTestCase(TestCase):
    """Base test case for admin functionality"""
    
    def setUp(self):
        self.site = AdminSite()
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            user_type='admin',
            is_staff=True,
            is_superuser=True,
            is_verified=True
        )
        
        # Create test users
        self.job_seeker = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker',
            is_verified=True
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter',
            is_verified=True
        )
        
        # Create profiles
        self.job_seeker_profile = JobSeekerProfile.objects.create(
            user=self.job_seeker,
            current_position='Software Developer',
            experience_level='mid',
            location='New York',
            skills='Python, Django, React',
            availability=True
        )
        
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Corp',
            industry='Technology',
            location='San Francisco'
        )
        
        # Create job post
        self.job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Senior Python Developer',
            description='Looking for a senior Python developer',
            location='Remote',
            job_type='full_time',
            experience_level='senior',
            salary_min=80000,
            salary_max=120000,
            skills_required='Python, Django, PostgreSQL',
            is_active=True
        )
        
        # Create resume
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker,
            original_filename='test_resume.pdf',
            is_primary=True,
            parsed_text='Software developer with 5 years experience',
            file_size=1024
        )
        
        # Create application
        self.application = Application.objects.create(
            job_seeker=self.job_seeker,
            job_post=self.job_post,
            resume=self.resume,
            status='pending',
            match_score=85.5
        )
        
        # Login admin user
        self.client.login(username='admin', password='testpass123')


class UserAdminTest(AdminTestCase):
    """Test cases for User admin interface"""
    
    def setUp(self):
        super().setUp()
        self.user_admin = UserAdmin(User, self.site)
        
    def test_user_admin_list_display(self):
        """Test user admin list display fields"""
        request = HttpRequest()
        request.user = self.admin_user
        
        # Test user type badge
        badge = self.user_admin.user_type_badge(self.job_seeker)
        self.assertIn('job_seeker', badge)
        self.assertIn('#28a745', badge)  # Green color for job seeker
        
        # Test verification status
        status = self.user_admin.verification_status(self.job_seeker)
        self.assertIn('✓ Verified', status)
        
        # Test profile completion
        completion = self.user_admin.profile_completion(self.job_seeker)
        self.assertIn('%', completion)
        
    def test_user_admin_bulk_actions(self):
        """Test user admin bulk actions"""
        request = HttpRequest()
        request.user = self.admin_user
        request._messages = FallbackStorage(request)
        
        # Create unverified user
        unverified_user = User.objects.create_user(
            username='unverified',
            email='unverified@test.com',
            password='testpass123',
            user_type='job_seeker',
            is_verified=False
        )
        
        queryset = User.objects.filter(id=unverified_user.id)
        
        # Test verify users action
        self.user_admin.verify_users(request, queryset)
        unverified_user.refresh_from_db()
        self.assertTrue(unverified_user.is_verified)
        
        # Test deactivate users action
        self.user_admin.deactivate_users(request, queryset)
        unverified_user.refresh_from_db()
        self.assertFalse(unverified_user.is_active)
        
    def test_user_admin_csv_export(self):
        """Test user CSV export functionality"""
        request = HttpRequest()
        request.user = self.admin_user
        
        queryset = User.objects.filter(id=self.job_seeker.id)
        response = self.user_admin.export_users_csv(request, queryset)
        
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Check header
        self.assertEqual(rows[0][0], 'Username')
        self.assertEqual(rows[0][1], 'Email')
        
        # Check data
        self.assertEqual(rows[1][0], 'jobseeker')
        self.assertEqual(rows[1][1], 'jobseeker@test.com')


class JobSeekerProfileAdminTest(AdminTestCase):
    """Test cases for JobSeekerProfile admin interface"""
    
    def setUp(self):
        super().setUp()
        self.profile_admin = JobSeekerProfileAdmin(JobSeekerProfile, self.site)
        
    def test_profile_admin_display_methods(self):
        """Test profile admin display methods"""
        # Test availability status
        status = self.profile_admin.availability_status(self.job_seeker_profile)
        self.assertIn('✓ Available', status)
        
        # Test skills count
        skills_count = self.profile_admin.skills_count(self.job_seeker_profile)
        self.assertEqual(skills_count, 3)  # Python, Django, React
        
        # Test resume count
        resume_count = self.profile_admin.resume_count(self.job_seeker_profile)
        self.assertEqual(resume_count, 1)
        
    def test_profile_admin_bulk_actions(self):
        """Test profile admin bulk actions"""
        request = HttpRequest()
        request.user = self.admin_user
        request._messages = FallbackStorage(request)
        
        queryset = JobSeekerProfile.objects.filter(id=self.job_seeker_profile.id)
        
        # Test mark unavailable
        self.profile_admin.mark_unavailable(request, queryset)
        self.job_seeker_profile.refresh_from_db()
        self.assertFalse(self.job_seeker_profile.availability)
        
        # Test mark available
        self.profile_admin.mark_available(request, queryset)
        self.job_seeker_profile.refresh_from_db()
        self.assertTrue(self.job_seeker_profile.availability)


class ResumeAdminTest(AdminTestCase):
    """Test cases for Resume admin interface"""
    
    def setUp(self):
        super().setUp()
        self.resume_admin = ResumeAdmin(Resume, self.site)
        
    def test_resume_admin_display_methods(self):
        """Test resume admin display methods"""
        # Test primary status
        status = self.resume_admin.primary_status(self.resume)
        self.assertIn('★ Primary', status)
        
        # Test file size formatted
        size = self.resume_admin.file_size_formatted(self.resume)
        self.assertEqual(size, '1.0 KB')
        
        # Test parsed status
        parsed = self.resume_admin.parsed_status(self.resume)
        self.assertIn('✓ Parsed', parsed)
        
        # Test applications count
        count = self.resume_admin.applications_count(self.resume)
        self.assertEqual(count, 1)
        
    def test_resume_admin_mark_as_primary(self):
        """Test mark as primary resume action"""
        request = HttpRequest()
        request.user = self.admin_user
        request._messages = FallbackStorage(request)
        
        # Create secondary resume
        secondary_resume = Resume.objects.create(
            job_seeker=self.job_seeker,
            original_filename='secondary_resume.pdf',
            is_primary=False,
            file_size=2048
        )
        
        queryset = Resume.objects.filter(id=secondary_resume.id)
        self.resume_admin.mark_as_primary(request, queryset)
        
        # Check that secondary is now primary
        secondary_resume.refresh_from_db()
        self.assertTrue(secondary_resume.is_primary)
        
        # Check that original primary is now secondary
        self.resume.refresh_from_db()
        self.assertFalse(self.resume.is_primary)


class JobPostAdminTest(AdminTestCase):
    """Test cases for JobPost admin interface"""
    
    def setUp(self):
        super().setUp()
        self.job_admin = JobPostAdmin(JobPost, self.site)
        
    def test_job_admin_display_methods(self):
        """Test job admin display methods"""
        # Test recruiter company
        company = self.job_admin.recruiter_company(self.job_post)
        self.assertEqual(company, 'Tech Corp')
        
        # Test status badge
        badge = self.job_admin.status_badge(self.job_post)
        self.assertIn('Active', badge)
        self.assertIn('#28a745', badge)  # Green color for active
        
        # Test salary range
        salary = self.job_admin.salary_range(self.job_post)
        self.assertEqual(salary, 'USD 80,000 - 120,000')
        
    def test_job_admin_bulk_actions(self):
        """Test job admin bulk actions"""
        request = HttpRequest()
        request.user = self.admin_user
        request._messages = FallbackStorage(request)
        
        queryset = JobPost.objects.filter(id=self.job_post.id)
        
        # Test deactivate jobs
        self.job_admin.deactivate_jobs(request, queryset)
        self.job_post.refresh_from_db()
        self.assertFalse(self.job_post.is_active)
        
        # Test activate jobs
        self.job_admin.activate_jobs(request, queryset)
        self.job_post.refresh_from_db()
        self.assertTrue(self.job_post.is_active)
        
        # Test mark featured
        self.job_admin.mark_featured(request, queryset)
        self.job_post.refresh_from_db()
        self.assertTrue(self.job_post.is_featured)


class ApplicationAdminTest(AdminTestCase):
    """Test cases for Application admin interface"""
    
    def setUp(self):
        super().setUp()
        self.app_admin = ApplicationAdmin(Application, self.site)
        
    def test_application_admin_display_methods(self):
        """Test application admin display methods"""
        # Test job post title
        title = self.app_admin.job_post_title(self.application)
        self.assertEqual(title, 'Senior Python Developer')
        
        # Test company name
        company = self.app_admin.company_name(self.application)
        self.assertEqual(company, 'Tech Corp')
        
        # Test status badge
        badge = self.app_admin.status_badge(self.application)
        self.assertIn('Pending', badge)
        self.assertIn('#ffc107', badge)  # Yellow color for pending
        
        # Test match score display
        score = self.app_admin.match_score_display(self.application)
        self.assertIn('85.5%', score)
        self.assertIn('#28a745', score)  # Green color for high score
        
        # Test days since applied
        days = self.app_admin.days_since_applied(self.application)
        self.assertEqual(days, 'Today')
        
    def test_application_admin_bulk_actions(self):
        """Test application admin bulk actions"""
        request = HttpRequest()
        request.user = self.admin_user
        request._messages = FallbackStorage(request)
        
        queryset = Application.objects.filter(id=self.application.id)
        
        # Test mark reviewed
        self.app_admin.mark_reviewed(request, queryset)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'reviewed')
        
        # Test mark shortlisted
        self.app_admin.mark_shortlisted(request, queryset)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'shortlisted')
        
        # Test mark rejected
        self.app_admin.mark_rejected(request, queryset)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'rejected')


class AdminIntegrationTest(AdminTestCase):
    """Integration tests for admin interface"""
    
    def test_admin_pages_load(self):
        """Test that admin pages load without errors"""
        # Test main admin index
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        
        # Test user changelist
        response = self.client.get('/admin/matcher/user/')
        self.assertEqual(response.status_code, 200)
        
        # Test user change form
        response = self.client.get(f'/admin/matcher/user/{self.job_seeker.id}/change/')
        self.assertEqual(response.status_code, 200)
        
        # Test job post changelist
        response = self.client.get('/admin/matcher/jobpost/')
        self.assertEqual(response.status_code, 200)
        
        # Test application changelist
        response = self.client.get('/admin/matcher/application/')
        self.assertEqual(response.status_code, 200)
        
    def test_admin_search_functionality(self):
        """Test admin search functionality"""
        # Test user search
        response = self.client.get('/admin/matcher/user/?q=jobseeker')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'jobseeker')
        
        # Test job post search
        response = self.client.get('/admin/matcher/jobpost/?q=Python')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Senior Python Developer')
        
    def test_admin_filters(self):
        """Test admin filter functionality"""
        # Test user type filter
        response = self.client.get('/admin/matcher/user/?user_type=job_seeker')
        self.assertEqual(response.status_code, 200)
        
        # Test job status filter
        response = self.client.get('/admin/matcher/jobpost/?is_active__exact=1')
        self.assertEqual(response.status_code, 200)
        
        # Test application status filter
        response = self.client.get('/admin/matcher/application/?status__exact=pending')
        self.assertEqual(response.status_code, 200)
        
    def test_admin_bulk_actions_integration(self):
        """Test bulk actions through admin interface"""
        # Test user verification bulk action
        response = self.client.post('/admin/matcher/user/', {
            'action': 'verify_users',
            '_selected_action': [str(self.job_seeker.id)],
        })
        self.assertEqual(response.status_code, 302)  # Redirect after action
        
        # Test job activation bulk action
        response = self.client.post('/admin/matcher/jobpost/', {
            'action': 'activate_jobs',
            '_selected_action': [str(self.job_post.id)],
        })
        self.assertEqual(response.status_code, 302)
        
    def test_admin_csv_export_integration(self):
        """Test CSV export through admin interface"""
        # Test user CSV export
        response = self.client.post('/admin/matcher/user/', {
            'action': 'export_users_csv',
            '_selected_action': [str(self.job_seeker.id)],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
        # Test job post CSV export
        response = self.client.post('/admin/matcher/jobpost/', {
            'action': 'export_jobs_csv',
            '_selected_action': [str(self.job_post.id)],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')


class AdminPermissionsTest(AdminTestCase):
    """Test admin permissions and access control"""
    
    def test_non_admin_access_denied(self):
        """Test that non-admin users cannot access admin"""
        # Logout admin
        self.client.logout()
        
        # Try to access admin as job seeker
        self.client.login(username='jobseeker', password='testpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_staff_user_access(self):
        """Test that staff users can access admin"""
        # Create staff user
        staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            user_type='admin',
            is_staff=True,
            is_verified=True
        )
        
        self.client.logout()
        self.client.login(username='staff', password='testpass123')
        
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)


class AdminCustomizationTest(AdminTestCase):
    """Test admin interface customizations"""
    
    def test_admin_site_customization(self):
        """Test admin site header and title customization"""
        response = self.client.get('/admin/')
        self.assertContains(response, 'HireWise Admin Dashboard')
        
    def test_admin_fieldsets(self):
        """Test admin fieldset organization"""
        response = self.client.get(f'/admin/matcher/user/{self.job_seeker.id}/change/')
        self.assertContains(response, 'Additional Info')
        self.assertContains(response, 'Profile Links')
        
        response = self.client.get(f'/admin/matcher/jobpost/{self.job_post.id}/change/')
        self.assertContains(response, 'Basic Information')
        self.assertContains(response, 'Job Details')
        self.assertContains(response, 'Requirements & Responsibilities')
        
    def test_admin_readonly_fields(self):
        """Test readonly fields in admin"""
        response = self.client.get(f'/admin/matcher/resume/{self.resume.id}/change/')
        self.assertContains(response, 'readonly')
        
        response = self.client.get(f'/admin/matcher/application/{self.application.id}/change/')
        self.assertContains(response, 'readonly')


@pytest.mark.django_db
class AdminPerformanceTest:
    """Test admin interface performance"""
    
    def test_admin_queryset_optimization(self):
        """Test that admin querysets are optimized"""
        # This would test for N+1 queries and other performance issues
        # Implementation would depend on specific performance requirements
        pass
    
    def test_admin_pagination(self):
        """Test admin pagination with large datasets"""
        # Create multiple test objects
        users = []
        for i in range(50):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123',
                user_type='job_seeker'
            )
            users.append(user)
        
        client = Client()
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        client.login(username='admin', password='testpass123')
        
        response = client.get('/admin/matcher/user/')
        assert response.status_code == 200
        assert 'paginator' in response.context


if __name__ == '__main__':
    pytest.main([__file__])