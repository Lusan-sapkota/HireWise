"""
Global pytest configuration and fixtures for HireWise backend tests.
"""
import pytest
import os
import sys
import tempfile
import django
from pathlib import Path

# Setup Django before importing Django modules
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirewise.settings')
django.setup()

from django.conf import settings
from django.test import override_settings
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from channels.testing import WebsocketCommunicator
from matcher.consumers import NotificationConsumer
from matcher.models import User, JobSeekerProfile, RecruiterProfile
from factories import (
    UserFactory, 
    JobSeekerProfileFactory, 
    RecruiterProfileFactory,
    JobPostFactory,
    ResumeFactory,
    ApplicationFactory
)


@pytest.fixture(scope='session')
def django_db_setup():
    """Set up test database."""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
        'CONN_MAX_AGE': 0,
        'OPTIONS': {},
        'TIME_ZONE': None,
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }


@pytest.fixture
def api_client():
    """Return DRF API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, job_seeker_user):
    """Return authenticated API client with job seeker user."""
    refresh = RefreshToken.for_user(job_seeker_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def recruiter_client(api_client, recruiter_user):
    """Return authenticated API client with recruiter user."""
    refresh = RefreshToken.for_user(recruiter_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return authenticated API client with admin user."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def job_seeker_user():
    """Create a job seeker user."""
    return UserFactory(user_type='job_seeker')


@pytest.fixture
def recruiter_user():
    """Create a recruiter user."""
    return UserFactory(user_type='recruiter')


@pytest.fixture
def admin_user():
    """Create an admin user."""
    return UserFactory(user_type='admin', is_staff=True, is_superuser=True)


@pytest.fixture
def job_seeker_profile(job_seeker_user):
    """Create a job seeker profile."""
    return JobSeekerProfileFactory(user=job_seeker_user)


@pytest.fixture
def recruiter_profile(recruiter_user):
    """Create a recruiter profile."""
    return RecruiterProfileFactory(user=recruiter_user)


@pytest.fixture
def sample_job_post(recruiter_user):
    """Create a sample job post."""
    return JobPostFactory(recruiter=recruiter_user)


@pytest.fixture
def sample_resume(job_seeker_user):
    """Create a sample resume."""
    return ResumeFactory(job_seeker=job_seeker_user)


@pytest.fixture
def sample_application(job_seeker_user, sample_job_post, sample_resume):
    """Create a sample job application."""
    return ApplicationFactory(
        job_seeker=job_seeker_user,
        job_post=sample_job_post,
        resume=sample_resume
    )


@pytest.fixture
def websocket_communicator():
    """Create WebSocket communicator for testing."""
    async def _create_communicator(user=None):
        communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            "/ws/notifications/"
        )
        if user:
            communicator.scope["user"] = user
        return communicator
    return _create_communicator


@pytest.fixture
def temp_media_root():
    """Create temporary media root for file upload tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with override_settings(MEDIA_ROOT=temp_dir):
            yield temp_dir


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    import io
    from reportlab.pdfgen import canvas
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, "Sample Resume")
    p.drawString(100, 730, "John Doe")
    p.drawString(100, 710, "Software Engineer")
    p.drawString(100, 690, "Skills: Python, Django, React")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


@pytest.fixture
def mock_gemini_response():
    """Mock response from Google Gemini API."""
    return {
        "parsed_text": "John Doe\nSoftware Engineer\nSkills: Python, Django, React\nExperience: 5 years",
        "key_skills": ["Python", "Django", "React", "JavaScript", "SQL"],
        "summary": "Experienced software engineer with 5 years of experience in web development",
        "experience_years": 5,
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "University of Technology",
                "year": "2018"
            }
        ],
        "contact_info": {
            "email": "john.doe@example.com",
            "phone": "+1234567890"
        }
    }


@pytest.fixture
def mock_ml_model_response():
    """Mock response from ML model."""
    return {
        "score": 87.5,
        "matching_skills": ["Python", "Django", "React"],
        "missing_skills": ["AWS", "Docker"],
        "recommendations": "Consider learning cloud technologies to improve match score"
    }


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass


@pytest.fixture
def disable_migrations():
    """Disable migrations for faster test execution."""
    settings.MIGRATION_MODULES = {
        'matcher': None,
        'auth': None,
        'contenttypes': None,
        'sessions': None,
        'admin': None,
        'messages': None,
        'staticfiles': None,
    }


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Create bulk test data for performance testing."""
    users = UserFactory.create_batch(100, user_type='job_seeker')
    recruiters = UserFactory.create_batch(20, user_type='recruiter')
    job_posts = []
    
    for recruiter in recruiters:
        job_posts.extend(JobPostFactory.create_batch(5, recruiter=recruiter))
    
    resumes = []
    for user in users:
        resumes.append(ResumeFactory(job_seeker=user))
    
    return {
        'users': users,
        'recruiters': recruiters,
        'job_posts': job_posts,
        'resumes': resumes
    }


# Mock external services
@pytest.fixture
def mock_redis(mocker):
    """Mock Redis connection."""
    return mocker.patch('django.core.cache.cache')


@pytest.fixture
def mock_celery_task(mocker):
    """Mock Celery task execution."""
    return mocker.patch('matcher.tasks.parse_resume_task.delay')


@pytest.fixture
def mock_gemini_api(mocker, mock_gemini_response):
    """Mock Google Gemini API calls."""
    mock = mocker.patch('matcher.services.GeminiResumeParser.parse_resume')
    mock.return_value = mock_gemini_response
    return mock


@pytest.fixture
def mock_ml_model(mocker, mock_ml_model_response):
    """Mock ML model predictions."""
    mock = mocker.patch('matcher.ml_services.JobMatchScorer.score_resume')
    mock.return_value = mock_ml_model_response['score']
    return mock