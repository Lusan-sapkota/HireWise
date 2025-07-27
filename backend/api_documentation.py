"""
Comprehensive API documentation with examples for HireWise Backend.

This module contains detailed documentation, examples, and schema definitions
for all API endpoints using drf_spectacular decorators.
"""

from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter,
    OpenApiResponse, OpenApiTypes
)
from drf_spectacular.openapi import AutoSchema
from rest_framework import status


# Common response examples
AUTHENTICATION_ERROR_EXAMPLE = OpenApiExample(
    'Authentication Error',
    summary='Authentication failed',
    description='Returned when JWT token is invalid or expired',
    value={
        'error': {
            'code': 'AUTHENTICATION_FAILED',
            'message': 'Invalid or expired token',
            'timestamp': '2024-01-15T10:30:00Z'
        }
    },
    response_only=True,
    status_codes=[status.HTTP_401_UNAUTHORIZED]
)

PERMISSION_ERROR_EXAMPLE = OpenApiExample(
    'Permission Denied',
    summary='Permission denied',
    description='Returned when user lacks required permissions',
    value={
        'error': {
            'code': 'PERMISSION_DENIED',
            'message': 'You do not have permission to perform this action',
            'timestamp': '2024-01-15T10:30:00Z'
        }
    },
    response_only=True,
    status_codes=[status.HTTP_403_FORBIDDEN]
)

VALIDATION_ERROR_EXAMPLE = OpenApiExample(
    'Validation Error',
    summary='Input validation failed',
    description='Returned when request data is invalid',
    value={
        'error': {
            'code': 'VALIDATION_ERROR',
            'message': 'Invalid input data',
            'details': {
                'email': ['This field is required'],
                'password': ['Password must be at least 8 characters long']
            },
            'timestamp': '2024-01-15T10:30:00Z'
        }
    },
    response_only=True,
    status_codes=[status.HTTP_400_BAD_REQUEST]
)

SERVER_ERROR_EXAMPLE = OpenApiExample(
    'Server Error',
    summary='Internal server error',
    description='Returned when an unexpected error occurs',
    value={
        'error': {
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An unexpected error occurred',
            'timestamp': '2024-01-15T10:30:00Z'
        }
    },
    response_only=True,
    status_codes=[status.HTTP_500_INTERNAL_SERVER_ERROR]
)

# Authentication endpoint documentation
JWT_REGISTER_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='Register new user with JWT',
    description='''
    Register a new user account and receive JWT tokens.
    
    **User Types:**
    - `job_seeker`: For candidates looking for jobs
    - `recruiter`: For employers posting jobs
    
    **Response includes:**
    - Access token (expires in 1 hour by default)
    - Refresh token (expires in 7 days by default)
    - User profile information
    ''',
    examples=[
        OpenApiExample(
            'Job Seeker Registration',
            summary='Register as job seeker',
            description='Example registration for a job seeker',
            value={
                'username': 'john_doe',
                'email': 'john@example.com',
                'password': 'securepassword123',
                'password_confirm': 'securepassword123',
                'first_name': 'John',
                'last_name': 'Doe',
                'user_type': 'job_seeker',
                'phone_number': '+1234567890'
            },
            request_only=True
        ),
        OpenApiExample(
            'Recruiter Registration',
            summary='Register as recruiter',
            description='Example registration for a recruiter',
            value={
                'username': 'hr_manager',
                'email': 'hr@company.com',
                'password': 'securepassword123',
                'password_confirm': 'securepassword123',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'user_type': 'recruiter',
                'phone_number': '+1234567890'
            },
            request_only=True
        ),
        OpenApiExample(
            'Successful Registration',
            summary='Registration success response',
            description='Response after successful user registration',
            value={
                'user': {
                    'id': 'uuid-string',
                    'username': 'john_doe',
                    'email': 'john@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'user_type': 'job_seeker',
                    'is_verified': False,
                    'created_at': '2024-01-15T10:30:00Z'
                },
                'tokens': {
                    'access': 'jwt-access-token',
                    'refresh': 'jwt-refresh-token'
                },
                'message': 'User registered successfully. Please check your email for verification.'
            },
            response_only=True,
            status_codes=[status.HTTP_201_CREATED]
        ),
        VALIDATION_ERROR_EXAMPLE
    ],
    responses={
        201: OpenApiResponse(description='User registered successfully'),
        400: OpenApiResponse(description='Validation error'),
        409: OpenApiResponse(description='User already exists')
    }
)

JWT_LOGIN_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='Login with JWT',
    description='''
    Authenticate user and receive JWT tokens.
    
    **Login Methods:**
    - Username and password
    - Email and password
    
    **Response includes:**
    - Access token for API authentication
    - Refresh token for token renewal
    - User profile information
    ''',
    examples=[
        OpenApiExample(
            'Login Request',
            summary='User login',
            description='Login with username/email and password',
            value={
                'username': 'john_doe',  # or email
                'password': 'securepassword123'
            },
            request_only=True
        ),
        OpenApiExample(
            'Login Success',
            summary='Login success response',
            description='Response after successful authentication',
            value={
                'user': {
                    'id': 'uuid-string',
                    'username': 'john_doe',
                    'email': 'john@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'user_type': 'job_seeker',
                    'is_verified': True
                },
                'tokens': {
                    'access': 'jwt-access-token',
                    'refresh': 'jwt-refresh-token'
                },
                'message': 'Login successful'
            },
            response_only=True,
            status_codes=[status.HTTP_200_OK]
        ),
        OpenApiExample(
            'Invalid Credentials',
            summary='Login failed',
            description='Response when credentials are invalid',
            value={
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid username or password',
                    'timestamp': '2024-01-15T10:30:00Z'
                }
            },
            response_only=True,
            status_codes=[status.HTTP_401_UNAUTHORIZED]
        )
    ]
)

# Job management documentation
JOB_POST_LIST_SCHEMA = extend_schema(
    tags=['Jobs'],
    summary='List job postings',
    description='''
    Retrieve a paginated list of job postings with filtering and search capabilities.
    
    **Filtering Options:**
    - `search`: Full-text search in title and description
    - `location`: Filter by job location
    - `job_type`: Filter by job type (full_time, part_time, contract, internship)
    - `experience_level`: Filter by required experience level
    - `skills`: Filter by required skills (comma-separated)
    - `salary_min` / `salary_max`: Filter by salary range
    - `is_active`: Filter active/inactive jobs (recruiters only)
    
    **Ordering:**
    - `created_at`: Sort by creation date (default: newest first)
    - `views_count`: Sort by popularity
    - `applications_count`: Sort by number of applications
    ''',
    parameters=[
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search in job title and description'
        ),
        OpenApiParameter(
            name='location',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by job location'
        ),
        OpenApiParameter(
            name='job_type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by job type',
            enum=['full_time', 'part_time', 'contract', 'internship', 'remote']
        ),
        OpenApiParameter(
            name='experience_level',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by experience level',
            enum=['entry', 'junior', 'mid', 'senior', 'lead', 'executive']
        ),
        OpenApiParameter(
            name='skills',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by skills (comma-separated)'
        ),
        OpenApiParameter(
            name='salary_min',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Minimum salary filter'
        ),
        OpenApiParameter(
            name='salary_max',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Maximum salary filter'
        ),
        OpenApiParameter(
            name='ordering',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Order results by field',
            enum=['created_at', '-created_at', 'views_count', '-views_count']
        )
    ],
    examples=[
        OpenApiExample(
            'Job Listings Response',
            summary='Paginated job listings',
            description='Example response with job listings',
            value={
                'count': 150,
                'next': 'http://localhost:8000/api/v1/job-posts/?page=2',
                'previous': None,
                'results': [
                    {
                        'id': 'uuid-string',
                        'title': 'Senior Python Developer',
                        'description': 'We are looking for an experienced Python developer...',
                        'location': 'San Francisco, CA',
                        'job_type': 'full_time',
                        'experience_level': 'senior',
                        'salary_min': 120000,
                        'salary_max': 180000,
                        'skills_required': ['Python', 'Django', 'PostgreSQL', 'AWS'],
                        'is_active': True,
                        'created_at': '2024-01-15T10:30:00Z',
                        'views_count': 45,
                        'applications_count': 12,
                        'recruiter': {
                            'id': 'uuid-string',
                            'company_name': 'Tech Corp',
                            'company_website': 'https://techcorp.com'
                        }
                    }
                ]
            },
            response_only=True,
            status_codes=[status.HTTP_200_OK]
        )
    ]
)

JOB_POST_CREATE_SCHEMA = extend_schema(
    tags=['Jobs'],
    summary='Create job posting',
    description='''
    Create a new job posting. Only recruiters can create job postings.
    
    **Required Fields:**
    - title: Job title
    - description: Detailed job description
    - location: Job location
    - job_type: Type of employment
    - experience_level: Required experience level
    - skills_required: Array of required skills
    
    **Optional Fields:**
    - salary_min/salary_max: Salary range
    - requirements: Additional requirements
    - benefits: Job benefits
    - company_description: About the company
    ''',
    examples=[
        OpenApiExample(
            'Create Job Request',
            summary='Create new job posting',
            description='Example request to create a job posting',
            value={
                'title': 'Senior Python Developer',
                'description': 'We are looking for an experienced Python developer to join our team...',
                'requirements': 'Bachelor\'s degree in Computer Science or related field...',
                'location': 'San Francisco, CA',
                'job_type': 'full_time',
                'experience_level': 'senior',
                'salary_min': 120000,
                'salary_max': 180000,
                'skills_required': ['Python', 'Django', 'PostgreSQL', 'AWS', 'Docker'],
                'benefits': 'Health insurance, 401k, flexible hours, remote work options',
                'company_description': 'We are a fast-growing tech company...'
            },
            request_only=True
        ),
        OpenApiExample(
            'Job Created Response',
            summary='Job creation success',
            description='Response after successful job creation',
            value={
                'id': 'uuid-string',
                'title': 'Senior Python Developer',
                'description': 'We are looking for an experienced Python developer...',
                'location': 'San Francisco, CA',
                'job_type': 'full_time',
                'experience_level': 'senior',
                'salary_min': 120000,
                'salary_max': 180000,
                'skills_required': ['Python', 'Django', 'PostgreSQL', 'AWS', 'Docker'],
                'is_active': True,
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-15T10:30:00Z',
                'views_count': 0,
                'applications_count': 0,
                'recruiter': 'uuid-string'
            },
            response_only=True,
            status_codes=[status.HTTP_201_CREATED]
        ),
        VALIDATION_ERROR_EXAMPLE,
        PERMISSION_ERROR_EXAMPLE
    ]
)

# Resume parsing documentation
RESUME_PARSE_SCHEMA = extend_schema(
    tags=['Resume Parsing'],
    summary='Parse resume with AI',
    description='''
    Upload and parse a resume file using Google Gemini AI.
    
    **Supported Formats:**
    - PDF (.pdf)
    - Microsoft Word (.doc, .docx)
    - Plain text (.txt)
    
    **File Size Limit:** 10MB
    
    **Extracted Information:**
    - Personal information (name, email, phone)
    - Work experience
    - Education
    - Skills
    - Certifications
    - Summary/objective
    
    **Processing:**
    - Synchronous processing for files < 1MB
    - Asynchronous processing for larger files
    ''',
    examples=[
        OpenApiExample(
            'Resume Parse Success',
            summary='Successful resume parsing',
            description='Response after successful resume parsing',
            value={
                'id': 'uuid-string',
                'parsed_text': 'John Doe\nSoftware Engineer\n...',
                'parsed_data': {
                    'personal_info': {
                        'name': 'John Doe',
                        'email': 'john@example.com',
                        'phone': '+1234567890',
                        'location': 'San Francisco, CA'
                    },
                    'summary': 'Experienced software engineer with 5+ years...',
                    'experience': [
                        {
                            'company': 'Tech Corp',
                            'position': 'Senior Developer',
                            'duration': '2020-2024',
                            'description': 'Led development of web applications...'
                        }
                    ],
                    'education': [
                        {
                            'institution': 'University of California',
                            'degree': 'Bachelor of Science in Computer Science',
                            'year': '2020'
                        }
                    ],
                    'skills': ['Python', 'Django', 'JavaScript', 'React', 'PostgreSQL'],
                    'certifications': ['AWS Certified Developer']
                },
                'confidence_score': 0.95,
                'processing_time': 2.3,
                'created_at': '2024-01-15T10:30:00Z'
            },
            response_only=True,
            status_codes=[status.HTTP_200_OK]
        ),
        OpenApiExample(
            'File Too Large',
            summary='File size exceeded',
            description='Response when uploaded file is too large',
            value={
                'error': {
                    'code': 'FILE_TOO_LARGE',
                    'message': 'File size exceeds 10MB limit',
                    'details': {
                        'max_size': '10MB',
                        'uploaded_size': '15MB'
                    },
                    'timestamp': '2024-01-15T10:30:00Z'
                }
            },
            response_only=True,
            status_codes=[status.HTTP_413_REQUEST_ENTITY_TOO_LARGE]
        ),
        OpenApiExample(
            'AI Service Unavailable',
            summary='AI service error',
            description='Response when Gemini API is unavailable',
            value={
                'error': {
                    'code': 'AI_SERVICE_UNAVAILABLE',
                    'message': 'Resume parsing service is temporarily unavailable',
                    'timestamp': '2024-01-15T10:30:00Z'
                }
            },
            response_only=True,
            status_codes=[status.HTTP_503_SERVICE_UNAVAILABLE]
        )
    ]
)

# Match scoring documentation
MATCH_SCORE_SCHEMA = extend_schema(
    tags=['Match Scoring'],
    summary='Calculate job match score',
    description='''
    Calculate AI-powered match score between a resume and job posting.
    
    **Algorithm:**
    - Uses custom ML model trained on job matching data
    - Analyzes skills overlap, experience relevance, and requirements fit
    - Returns score from 0-100 with detailed breakdown
    
    **Input:**
    - resume_id: ID of parsed resume
    - job_id: ID of job posting
    
    **Output:**
    - Overall match score (0-100)
    - Skills analysis (matching/missing skills)
    - Experience relevance score
    - Recommendations for improvement
    ''',
    examples=[
        OpenApiExample(
            'Match Score Request',
            summary='Calculate match score',
            description='Request to calculate match score',
            value={
                'resume_id': 'uuid-string',
                'job_id': 'uuid-string'
            },
            request_only=True
        ),
        OpenApiExample(
            'Match Score Response',
            summary='Match score calculation result',
            description='Detailed match score analysis',
            value={
                'overall_score': 87.5,
                'breakdown': {
                    'skills_match': 92.0,
                    'experience_match': 85.0,
                    'education_match': 88.0,
                    'location_match': 85.0
                },
                'matching_skills': [
                    'Python', 'Django', 'PostgreSQL', 'AWS'
                ],
                'missing_skills': [
                    'Docker', 'Kubernetes', 'Redis'
                ],
                'recommendations': [
                    'Consider gaining experience with containerization (Docker)',
                    'Cloud orchestration skills (Kubernetes) would strengthen your profile'
                ],
                'confidence': 0.94,
                'calculated_at': '2024-01-15T10:30:00Z'
            },
            response_only=True,
            status_codes=[status.HTTP_200_OK]
        ),
        OpenApiExample(
            'Resume Not Found',
            summary='Resume not found',
            description='Response when resume ID is invalid',
            value={
                'error': {
                    'code': 'RESUME_NOT_FOUND',
                    'message': 'Resume with the specified ID was not found',
                    'timestamp': '2024-01-15T10:30:00Z'
                }
            },
            response_only=True,
            status_codes=[status.HTTP_404_NOT_FOUND]
        )
    ]
)

# Application workflow documentation
APPLICATION_CREATE_SCHEMA = extend_schema(
    tags=['Applications'],
    summary='Apply to job',
    description='''
    Submit a job application with resume and optional cover letter.
    
    **Requirements:**
    - User must be a job seeker
    - Job must be active
    - Cannot apply to the same job twice
    - Must have at least one resume uploaded
    
    **Process:**
    1. Application is created with 'pending' status
    2. Match score is calculated automatically
    3. Recruiter receives real-time notification
    4. Application appears in recruiter's dashboard
    ''',
    examples=[
        OpenApiExample(
            'Job Application Request',
            summary='Submit job application',
            description='Request to apply for a job',
            value={
                'job_post': 'uuid-string',
                'resume': 'uuid-string',
                'cover_letter': 'I am excited to apply for this position because...'
            },
            request_only=True
        ),
        OpenApiExample(
            'Application Success',
            summary='Application submitted successfully',
            description='Response after successful job application',
            value={
                'id': 'uuid-string',
                'job_post': {
                    'id': 'uuid-string',
                    'title': 'Senior Python Developer',
                    'company_name': 'Tech Corp'
                },
                'resume': 'uuid-string',
                'cover_letter': 'I am excited to apply for this position...',
                'status': 'pending',
                'match_score': 87.5,
                'applied_at': '2024-01-15T10:30:00Z',
                'recruiter_notes': null
            },
            response_only=True,
            status_codes=[status.HTTP_201_CREATED]
        ),
        OpenApiExample(
            'Already Applied',
            summary='Duplicate application',
            description='Response when user has already applied to this job',
            value={
                'error': {
                    'code': 'DUPLICATE_APPLICATION',
                    'message': 'You have already applied to this job',
                    'timestamp': '2024-01-15T10:30:00Z'
                }
            },
            response_only=True,
            status_codes=[status.HTTP_409_CONFLICT]
        )
    ]
)

# Common error responses for all endpoints
COMMON_ERROR_RESPONSES = {
    401: OpenApiResponse(
        description='Authentication required',
        examples=[AUTHENTICATION_ERROR_EXAMPLE]
    ),
    403: OpenApiResponse(
        description='Permission denied',
        examples=[PERMISSION_ERROR_EXAMPLE]
    ),
    500: OpenApiResponse(
        description='Internal server error',
        examples=[SERVER_ERROR_EXAMPLE]
    )
}

# WebSocket documentation (for reference, not OpenAPI)
WEBSOCKET_DOCUMENTATION = '''
# WebSocket API Documentation

## Connection
- **URL**: `ws://localhost:8000/ws/notifications/`
- **Authentication**: JWT token in query parameter or header
- **Protocol**: WebSocket with JSON messages

## Message Types

### Connection Events
```json
{
    "type": "connection.established",
    "data": {
        "user_id": "uuid-string",
        "connected_at": "2024-01-15T10:30:00Z"
    }
}
```

### Job Notifications
```json
{
    "type": "job.posted",
    "data": {
        "job_id": "uuid-string",
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "match_score": 87.5,
        "posted_at": "2024-01-15T10:30:00Z"
    }
}
```

### Application Notifications
```json
{
    "type": "application.status_changed",
    "data": {
        "application_id": "uuid-string",
        "job_title": "Senior Python Developer",
        "old_status": "pending",
        "new_status": "interview_scheduled",
        "recruiter_notes": "Please schedule interview for next week",
        "updated_at": "2024-01-15T10:30:00Z"
    }
}
```

### Match Score Notifications
```json
{
    "type": "match_score.calculated",
    "data": {
        "resume_id": "uuid-string",
        "job_id": "uuid-string",
        "score": 87.5,
        "calculated_at": "2024-01-15T10:30:00Z"
    }
}
```

## Error Handling
```json
{
    "type": "error",
    "data": {
        "code": "AUTHENTICATION_FAILED",
        "message": "Invalid token",
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```
'''