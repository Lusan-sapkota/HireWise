"""
Test fixtures and data management utilities for HireWise Backend.

This module provides fixtures, sample data, and utilities for testing
and development environments.
"""

import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.files.base import ContentFile
from faker import Faker
import uuid

from matcher.models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost,
    Application, AIAnalysisResult, InterviewSession, Skill, UserSkill,
    NotificationTemplate, NotificationPreference
)
from factories import (
    UserFactory, JobSeekerProfileFactory, RecruiterProfileFactory,
    ResumeFactory, JobPostFactory, ApplicationFactory, SkillFactory,
    InterviewSessionFactory, AIAnalysisResultFactory,
    NotificationTemplateFactory, NotificationPreferenceFactory,
    BatchUserFactory, BatchJobFactory
)

fake = Faker()


class TestDataManager:
    """Manager class for creating and managing test data."""
    
    def __init__(self):
        self.created_objects = {
            'users': [],
            'profiles': [],
            'jobs': [],
            'applications': [],
            'resumes': [],
            'skills': [],
            'interviews': [],
            'analyses': []
        }
    
    def create_minimal_dataset(self):
        """Create minimal dataset for basic testing."""
        with transaction.atomic():
            # Create basic skills
            skills = self._create_basic_skills()
            
            # Create users
            job_seeker = UserFactory(
                username='test_jobseeker',
                email='jobseeker@test.com',
                user_type='job_seeker'
            )
            recruiter = UserFactory(
                username='test_recruiter',
                email='recruiter@test.com',
                user_type='recruiter'
            )
            admin = UserFactory(
                username='test_admin',
                email='admin@test.com',
                user_type='admin',
                is_staff=True,
                is_superuser=True
            )
            
            # Create profiles
            job_seeker_profile = JobSeekerProfileFactory(user=job_seeker)
            recruiter_profile = RecruiterProfileFactory(user=recruiter)
            
            # Create job post
            job_post = JobPostFactory(recruiter=recruiter)
            
            # Create resume
            resume = ResumeFactory(job_seeker=job_seeker)
            
            # Create application
            application = ApplicationFactory(
                job_seeker=job_seeker,
                job_post=job_post,
                resume=resume
            )
            
            self.created_objects.update({
                'users': [job_seeker, recruiter, admin],
                'profiles': [job_seeker_profile, recruiter_profile],
                'jobs': [job_post],
                'applications': [application],
                'resumes': [resume],
                'skills': skills
            })
            
            return self.created_objects
    
    def create_comprehensive_dataset(self):
        """Create comprehensive dataset for full testing."""
        with transaction.atomic():
            # Create skills
            skills = self._create_comprehensive_skills()
            
            # Create users and profiles
            profiles_data = BatchUserFactory.create_complete_profiles(
                job_seeker_count=20,
                recruiter_count=5
            )
            
            # Create jobs with applications
            jobs_data = BatchJobFactory.create_jobs_with_applications(
                job_count=15,
                applications_per_job=4
            )
            
            # Create additional test data
            interviews = self._create_interview_sessions(jobs_data['applications'][:10])
            analyses = self._create_ai_analyses(
                jobs_data['applications'][:5]
            )
            
            # Create notification templates
            notification_templates = self._create_notification_templates()
            
            self.created_objects.update({
                'users': profiles_data['job_seekers'] + profiles_data['recruiters'],
                'profiles': profiles_data['job_seeker_profiles'] + profiles_data['recruiter_profiles'],
                'jobs': jobs_data['jobs'],
                'applications': jobs_data['applications'],
                'skills': skills,
                'interviews': interviews,
                'analyses': analyses,
                'notification_templates': notification_templates
            })
            
            return self.created_objects
    
    def create_performance_dataset(self):
        """Create large dataset for performance testing."""
        with transaction.atomic():
            # Create large number of users
            job_seekers = UserFactory.create_batch(100, user_type='job_seeker')
            recruiters = UserFactory.create_batch(20, user_type='recruiter')
            
            # Create profiles
            job_seeker_profiles = [
                JobSeekerProfileFactory(user=user) for user in job_seekers
            ]
            recruiter_profiles = [
                RecruiterProfileFactory(user=user) for user in recruiters
            ]
            
            # Create many jobs
            jobs = []
            for recruiter in recruiters:
                recruiter_jobs = JobPostFactory.create_batch(10, recruiter=recruiter)
                jobs.extend(recruiter_jobs)
            
            # Create many applications
            applications = []
            for i, job in enumerate(jobs[:50]):  # Only first 50 jobs to avoid too many applications
                job_seeker_subset = job_seekers[i*2:(i*2)+5]  # 5 applications per job
                for job_seeker in job_seeker_subset:
                    resume = ResumeFactory(job_seeker=job_seeker)
                    application = ApplicationFactory(
                        job_seeker=job_seeker,
                        job_post=job,
                        resume=resume
                    )
                    applications.append(application)
            
            self.created_objects.update({
                'users': job_seekers + recruiters,
                'profiles': job_seeker_profiles + recruiter_profiles,
                'jobs': jobs,
                'applications': applications
            })
            
            return self.created_objects
    
    def _create_basic_skills(self):
        """Create basic set of skills."""
        basic_skills = [
            ('Python', 'programming'),
            ('JavaScript', 'programming'),
            ('Django', 'framework'),
            ('React', 'framework'),
            ('PostgreSQL', 'database'),
            ('Git', 'tool'),
            ('Communication', 'soft_skill'),
            ('Problem Solving', 'soft_skill')
        ]
        
        skills = []
        for name, category in basic_skills:
            skill, created = Skill.objects.get_or_create(
                name=name,
                defaults={'category': category}
            )
            skills.append(skill)
        
        return skills
    
    def _create_comprehensive_skills(self):
        """Create comprehensive set of skills."""
        skill_data = {
            'programming': [
                'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust',
                'TypeScript', 'PHP', 'Ruby', 'Swift', 'Kotlin'
            ],
            'framework': [
                'Django', 'React', 'Angular', 'Vue.js', 'Express.js',
                'Spring Boot', 'Laravel', 'Rails', 'Flask', 'FastAPI'
            ],
            'database': [
                'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
                'SQLite', 'Oracle', 'SQL Server', 'Cassandra', 'DynamoDB'
            ],
            'tool': [
                'Git', 'Docker', 'Kubernetes', 'Jenkins', 'AWS', 'Azure',
                'GCP', 'Terraform', 'Ansible', 'Nginx', 'Apache'
            ],
            'soft_skill': [
                'Communication', 'Leadership', 'Problem Solving', 'Teamwork',
                'Time Management', 'Critical Thinking', 'Adaptability',
                'Project Management', 'Mentoring', 'Public Speaking'
            ]
        }
        
        skills = []
        for category, skill_names in skill_data.items():
            for name in skill_names:
                skill, created = Skill.objects.get_or_create(
                    name=name,
                    defaults={'category': category}
                )
                skills.append(skill)
        
        return skills
    
    def _create_interview_sessions(self, applications):
        """Create interview sessions for applications."""
        interviews = []
        for application in applications:
            if application.status in ['interview', 'accepted']:
                interview = InterviewSessionFactory(application=application)
                interviews.append(interview)
        
        return interviews
    
    def _create_ai_analyses(self, applications):
        """Create AI analysis results for applications."""
        analyses = []
        for application in applications:
            # Create resume parsing analysis
            parsing_analysis = AIAnalysisResultFactory(
                resume=application.resume,
                analysis_type='resume_parsing',
                analysis_result={
                    'personal_info': {
                        'name': f"{application.job_seeker.first_name} {application.job_seeker.last_name}",
                        'email': application.job_seeker.email
                    },
                    'skills': fake.words(nb=8),
                    'experience': fake.random_int(min=1, max=10),
                    'education': fake.sentence()
                }
            )
            analyses.append(parsing_analysis)
            
            # Create job matching analysis
            matching_analysis = AIAnalysisResultFactory(
                resume=application.resume,
                job_post=application.job_post,
                analysis_type='job_matching',
                analysis_result={
                    'overall_score': fake.random_int(min=60, max=95),
                    'skills_match': fake.random_int(min=70, max=100),
                    'experience_match': fake.random_int(min=50, max=90),
                    'matching_skills': fake.words(nb=5),
                    'missing_skills': fake.words(nb=3)
                }
            )
            analyses.append(matching_analysis)
        
        return analyses
    
    def _create_notification_templates(self):
        """Create notification templates."""
        templates_data = [
            {
                'name': 'job_posted',
                'template_type': 'job_posted',
                'subject_template': 'New Job Posted: {job_title}',
                'body_template': 'A new job "{job_title}" has been posted by {company_name}. Check it out!'
            },
            {
                'name': 'application_received',
                'template_type': 'application_received',
                'subject_template': 'New Application for {job_title}',
                'body_template': 'You have received a new application from {applicant_name} for {job_title}.'
            },
            {
                'name': 'application_status_changed',
                'template_type': 'application_status_changed',
                'subject_template': 'Application Status Update: {job_title}',
                'body_template': 'Your application status for {job_title} has been updated to {status}.'
            },
            {
                'name': 'interview_scheduled',
                'template_type': 'interview_scheduled',
                'subject_template': 'Interview Scheduled: {job_title}',
                'body_template': 'Your interview for {job_title} has been scheduled for {interview_date}.'
            }
        ]
        
        templates = []
        for template_data in templates_data:
            template, created = NotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            templates.append(template)
        
        return templates
    
    def cleanup_test_data(self):
        """Clean up all created test data."""
        with transaction.atomic():
            # Delete in reverse order to avoid foreign key constraints
            AIAnalysisResult.objects.filter(
                id__in=[obj.id for obj in self.created_objects.get('analyses', [])]
            ).delete()
            
            InterviewSession.objects.filter(
                id__in=[obj.id for obj in self.created_objects.get('interviews', [])]
            ).delete()
            
            Application.objects.filter(
                id__in=[obj.id for obj in self.created_objects.get('applications', [])]
            ).delete()
            
            Resume.objects.filter(
                id__in=[obj.id for obj in self.created_objects.get('resumes', [])]
            ).delete()
            
            JobPost.objects.filter(
                id__in=[obj.id for obj in self.created_objects.get('jobs', [])]
            ).delete()
            
            # Delete profiles
            for profile in self.created_objects.get('profiles', []):
                profile.delete()
            
            # Delete users
            User.objects.filter(
                id__in=[obj.id for obj in self.created_objects.get('users', [])]
            ).delete()
        
        self.created_objects = {key: [] for key in self.created_objects.keys()}


class SampleDataGenerator:
    """Generator for creating realistic sample data."""
    
    @staticmethod
    def generate_realistic_resume_text(job_seeker):
        """Generate realistic resume text."""
        return f"""
{job_seeker.first_name} {job_seeker.last_name}
Email: {job_seeker.email}
Phone: {job_seeker.phone_number}

PROFESSIONAL SUMMARY
{fake.text(max_nb_chars=200)}

EXPERIENCE
Senior Software Engineer | Tech Corp | 2020-2024
• {fake.sentence()}
• {fake.sentence()}
• {fake.sentence()}

Software Engineer | StartupXYZ | 2018-2020
• {fake.sentence()}
• {fake.sentence()}

EDUCATION
Bachelor of Science in Computer Science
University of Technology | 2018

SKILLS
Technical: Python, Django, JavaScript, React, PostgreSQL, AWS
Soft Skills: Leadership, Communication, Problem Solving

CERTIFICATIONS
• AWS Certified Developer
• Scrum Master Certification
"""
    
    @staticmethod
    def generate_realistic_job_description(job_title, company_name):
        """Generate realistic job description."""
        return f"""
About {company_name}:
{fake.text(max_nb_chars=300)}

Job Description:
We are seeking a talented {job_title} to join our growing team. 

Responsibilities:
• {fake.sentence()}
• {fake.sentence()}
• {fake.sentence()}
• {fake.sentence()}

Requirements:
• Bachelor's degree in Computer Science or related field
• {fake.random_int(min=2, max=8)}+ years of experience
• Strong knowledge of relevant technologies
• Excellent communication skills

Benefits:
• Competitive salary and equity
• Health, dental, and vision insurance
• Flexible work arrangements
• Professional development opportunities
"""
    
    @staticmethod
    def generate_cover_letter(job_seeker, job_post):
        """Generate realistic cover letter."""
        return f"""
Dear Hiring Manager,

I am writing to express my strong interest in the {job_post.title} position at {job_post.recruiter.recruiterprofile.company_name}. 

{fake.text(max_nb_chars=300)}

I am particularly excited about this opportunity because {fake.sentence()}

{fake.text(max_nb_chars=200)}

Thank you for considering my application. I look forward to hearing from you.

Best regards,
{job_seeker.first_name} {job_seeker.last_name}
"""


# Pytest fixtures
import pytest
from django.test import TestCase


@pytest.fixture
def test_data_manager():
    """Pytest fixture for test data manager."""
    manager = TestDataManager()
    yield manager
    manager.cleanup_test_data()


@pytest.fixture
def minimal_test_data(test_data_manager):
    """Pytest fixture for minimal test data."""
    return test_data_manager.create_minimal_dataset()


@pytest.fixture
def comprehensive_test_data(test_data_manager):
    """Pytest fixture for comprehensive test data."""
    return test_data_manager.create_comprehensive_dataset()


@pytest.fixture
def performance_test_data(test_data_manager):
    """Pytest fixture for performance test data."""
    return test_data_manager.create_performance_dataset()


# Django test case mixins
class TestDataMixin:
    """Mixin for Django test cases to provide test data."""
    
    def setUp(self):
        super().setUp()
        self.test_data_manager = TestDataManager()
        self.test_data = self.test_data_manager.create_minimal_dataset()
    
    def tearDown(self):
        self.test_data_manager.cleanup_test_data()
        super().tearDown()


class ComprehensiveTestDataMixin:
    """Mixin for Django test cases with comprehensive test data."""
    
    def setUp(self):
        super().setUp()
        self.test_data_manager = TestDataManager()
        self.test_data = self.test_data_manager.create_comprehensive_dataset()
    
    def tearDown(self):
        self.test_data_manager.cleanup_test_data()
        super().tearDown()


# Management command for creating test data
class Command(BaseCommand):
    """Django management command for creating test data."""
    
    help = 'Create test data for development and testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['minimal', 'comprehensive', 'performance'],
            default='minimal',
            help='Type of test data to create'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up existing test data first'
        )
    
    def handle(self, *args, **options):
        manager = TestDataManager()
        
        if options['cleanup']:
            self.stdout.write('Cleaning up existing test data...')
            manager.cleanup_test_data()
        
        data_type = options['type']
        self.stdout.write(f'Creating {data_type} test data...')
        
        if data_type == 'minimal':
            data = manager.create_minimal_dataset()
        elif data_type == 'comprehensive':
            data = manager.create_comprehensive_dataset()
        elif data_type == 'performance':
            data = manager.create_performance_dataset()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {data_type} test data:\n'
                f'- Users: {len(data["users"])}\n'
                f'- Jobs: {len(data["jobs"])}\n'
                f'- Applications: {len(data["applications"])}\n'
                f'- Skills: {len(data["skills"])}'
            )
        )