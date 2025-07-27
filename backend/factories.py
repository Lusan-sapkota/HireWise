"""
Factory classes for creating test data.
"""

import factory
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from faker import Faker
import uuid

from matcher.models import (
    JobSeekerProfile, RecruiterProfile, Resume, JobPost, Application,
    AIAnalysisResult, Notification, Skill, UserSkill
)

User = get_user_model()
fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""
    
    class Meta:
        model = User
    
    # Let Django handle UUID generation automatically
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    user_type = 'job_seeker'
    is_active = True
    is_verified = True


class JobSeekerProfileFactory(factory.django.DjangoModelFactory):
    """Factory for JobSeekerProfile model."""
    
    class Meta:
        model = JobSeekerProfile
    
    user = factory.SubFactory(UserFactory, user_type='job_seeker')
    location = factory.Faker('city')
    experience_level = factory.Iterator(['entry', 'mid', 'senior', 'lead'])
    current_position = factory.Faker('job')
    expected_salary = factory.Faker('random_int', min=40000, max=150000)
    skills = factory.Faker('words', nb=5)
    bio = factory.Faker('text', max_nb_chars=500)
    linkedin_url = factory.LazyAttribute(lambda obj: f"https://linkedin.com/in/{obj.user.username}")
    github_url = factory.LazyAttribute(lambda obj: f"https://github.com/{obj.user.username}")
    availability = True


class RecruiterProfileFactory(factory.django.DjangoModelFactory):
    """Factory for RecruiterProfile model."""
    
    class Meta:
        model = RecruiterProfile
    
    user = factory.SubFactory(UserFactory, user_type='recruiter')
    company_name = factory.Faker('company')
    company_website = factory.Faker('url')
    company_size = factory.Iterator(['1-10', '11-50', '51-200', '201-500', '500+'])
    industry = factory.Faker('bs')
    company_description = factory.Faker('text', max_nb_chars=1000)
    location = factory.Faker('city')


class ResumeFactory(factory.django.DjangoModelFactory):
    """Factory for Resume model."""
    
    class Meta:
        model = Resume
    
    # Let Django handle UUID generation automatically
    job_seeker = factory.SubFactory(UserFactory, user_type='job_seeker')
    file = factory.LazyAttribute(
        lambda obj: ContentFile(
            fake.text(max_nb_chars=2000).encode('utf-8'),
            name=f"{obj.job_seeker.username}_resume.pdf"
        )
    )
    original_filename = factory.LazyAttribute(lambda obj: f"{obj.job_seeker.username}_resume.pdf")
    parsed_text = factory.Faker('text', max_nb_chars=2000)
    is_primary = False
    file_size = factory.Faker('random_int', min=50000, max=500000)


class JobPostFactory(factory.django.DjangoModelFactory):
    """Factory for JobPost model."""
    
    class Meta:
        model = JobPost
    
    # Let Django handle UUID generation automatically
    recruiter = factory.SubFactory(UserFactory, user_type='recruiter')
    title = factory.Faker('job')
    description = factory.Faker('text', max_nb_chars=2000)
    requirements = factory.Faker('text', max_nb_chars=1000)
    location = factory.Faker('city')
    job_type = factory.Iterator(['full_time', 'part_time', 'contract', 'internship'])
    experience_level = factory.Iterator(['entry', 'mid', 'senior', 'lead'])
    salary_min = factory.Faker('random_int', min=40000, max=100000)
    salary_max = factory.LazyAttribute(lambda obj: obj.salary_min + fake.random_int(min=10000, max=50000))
    skills_required = factory.List([
        factory.Faker('word') for _ in range(5)
    ])
    is_active = True
    remote_work_allowed = factory.Faker('boolean')
    views_count = factory.Faker('random_int', min=0, max=1000)


class ApplicationFactory(factory.django.DjangoModelFactory):
    """Factory for Application model."""
    
    class Meta:
        model = Application
    
    # Let Django handle UUID generation automatically
    job_seeker = factory.SubFactory(UserFactory, user_type='job_seeker')
    job_post = factory.SubFactory(JobPostFactory)
    resume = factory.SubFactory(ResumeFactory)
    cover_letter = factory.Faker('text', max_nb_chars=1000)
    status = factory.Iterator(['pending', 'reviewed', 'interview', 'rejected', 'accepted'])
    match_score = factory.Faker('random_int', min=0, max=100)
    recruiter_notes = factory.Faker('text', max_nb_chars=500)


class AIAnalysisResultFactory(factory.django.DjangoModelFactory):
    """Factory for AIAnalysisResult model."""
    
    class Meta:
        model = AIAnalysisResult
    
    # Let Django handle UUID generation automatically
    resume = factory.SubFactory(ResumeFactory)
    job_post = factory.SubFactory(JobPostFactory)
    analysis_type = factory.Iterator(['resume_parse', 'job_match', 'career_insights'])
    input_data = factory.Faker('text', max_nb_chars=1000)
    analysis_result = factory.LazyFunction(lambda: {
        'skills': fake.words(nb=5),
        'score': fake.random_int(min=0, max=100),
        'confidence': fake.random_int(min=70, max=100)
    })
    confidence_score = factory.Faker('pyfloat', left_digits=1, right_digits=2, positive=True, max_value=1)
    processing_time = factory.Faker('pyfloat', left_digits=1, right_digits=2, positive=True, max_value=10)


class NotificationFactory(factory.django.DjangoModelFactory):
    """Factory for Notification model."""
    
    class Meta:
        model = Notification
    
    # Let Django handle UUID generation automatically
    user = factory.SubFactory(UserFactory)
    notification_type = factory.Iterator([
        'new_job', 'application_status', 'match_found', 'interview_scheduled'
    ])
    message = factory.Faker('sentence')
    data = factory.LazyFunction(lambda: {
        'job_id': str(uuid.uuid4()),
        'additional_info': fake.sentence()
    })
    is_read = False


class SkillFactory(factory.django.DjangoModelFactory):
    """Factory for Skill model."""
    
    class Meta:
        model = Skill
    
    name = factory.Faker('word')
    category = factory.Iterator(['programming', 'framework', 'tool', 'soft_skill'])
    description = factory.Faker('sentence')


class UserSkillFactory(factory.django.DjangoModelFactory):
    """Factory for UserSkill model."""
    
    class Meta:
        model = UserSkill
    
    user = factory.SubFactory(UserFactory)
    skill = factory.SubFactory(SkillFactory)
    proficiency_level = factory.Iterator(['beginner', 'intermediate', 'advanced', 'expert'])
    years_of_experience = factory.Faker('random_int', min=0, max=20)
    is_verified = factory.Faker('boolean')