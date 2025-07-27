#!/usr/bin/env python
"""
API Documentation Generator for HireWise backend.
Generates comprehensive API documentation with examples and testing guides.
"""
import os
import sys
import django
from pathlib import Path
import json
import subprocess

# Setup Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirewise.settings')
django.setup()

from django.urls import reverse
from django.conf import settings
from rest_framework.test import APIClient
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema


class APIDocumentationGenerator:
    """Generate comprehensive API documentation."""
    
    def __init__(self):
        self.client = APIClient()
        self.docs_dir = Path(__file__).parent / 'docs'
        self.docs_dir.mkdir(exist_ok=True)
    
    def generate_openapi_schema(self):
        """Generate OpenAPI schema file."""
        print("Generating OpenAPI schema...")
        
        # Generate schema using Django management command
        schema_file = self.docs_dir / 'openapi-schema.json'
        
        cmd = [
            sys.executable, 'manage.py', 'spectacular',
            '--color', '--file', str(schema_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ OpenAPI schema generated: {schema_file}")
            return True
        else:
            print(f"❌ Failed to generate OpenAPI schema: {result.stderr}")
            return False
    
    def generate_postman_collection(self):
        """Generate Postman collection from OpenAPI schema."""
        print("Generating Postman collection...")
        
        try:
            # Read OpenAPI schema
            schema_file = self.docs_dir / 'openapi-schema.json'
            if not schema_file.exists():
                print("❌ OpenAPI schema not found. Generate schema first.")
                return False
            
            with open(schema_file, 'r') as f:
                schema = json.load(f)
            
            # Convert to Postman collection format
            collection = self._convert_to_postman_collection(schema)
            
            # Save Postman collection
            collection_file = self.docs_dir / 'HireWise-API.postman_collection.json'
            with open(collection_file, 'w') as f:
                json.dump(collection, f, indent=2)
            
            print(f"✅ Postman collection generated: {collection_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to generate Postman collection: {e}")
            return False
    
    def _convert_to_postman_collection(self, schema):
        """Convert OpenAPI schema to Postman collection format."""
        collection = {
            "info": {
                "name": "HireWise API",
                "description": schema.get('info', {}).get('description', ''),
                "version": schema.get('info', {}).get('version', '1.0.0'),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{access_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "http://localhost:8000",
                    "type": "string"
                },
                {
                    "key": "access_token",
                    "value": "",
                    "type": "string"
                }
            ],
            "item": []
        }
        
        # Group endpoints by tags
        endpoints_by_tag = {}
        
        for path, methods in schema.get('paths', {}).items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
                    tags = details.get('tags', ['Uncategorized'])
                    tag = tags[0] if tags else 'Uncategorized'
                    
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    
                    endpoints_by_tag[tag].append({
                        'path': path,
                        'method': method.upper(),
                        'details': details
                    })
        
        # Create Postman folders and requests
        for tag, endpoints in endpoints_by_tag.items():
            folder = {
                "name": tag,
                "item": []
            }
            
            for endpoint in endpoints:
                request = self._create_postman_request(endpoint)
                folder["item"].append(request)
            
            collection["item"].append(folder)
        
        return collection
    
    def _create_postman_request(self, endpoint):
        """Create a Postman request from endpoint details."""
        details = endpoint['details']
        
        request = {
            "name": details.get('summary', f"{endpoint['method']} {endpoint['path']}"),
            "request": {
                "method": endpoint['method'],
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json",
                        "type": "text"
                    }
                ],
                "url": {
                    "raw": "{{base_url}}" + endpoint['path'],
                    "host": ["{{base_url}}"],
                    "path": endpoint['path'].strip('/').split('/')
                }
            },
            "response": []
        }
        
        # Add request body for POST/PUT/PATCH
        if endpoint['method'] in ['POST', 'PUT', 'PATCH']:
            request_body = details.get('requestBody', {})
            if request_body:
                content = request_body.get('content', {})
                json_content = content.get('application/json', {})
                schema_ref = json_content.get('schema', {})
                
                # Add example body if available
                if 'examples' in json_content:
                    example_key = list(json_content['examples'].keys())[0]
                    example_value = json_content['examples'][example_key].get('value', {})
                    
                    request["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(example_value, indent=2),
                        "options": {
                            "raw": {
                                "language": "json"
                            }
                        }
                    }
        
        # Add query parameters
        parameters = details.get('parameters', [])
        query_params = [p for p in parameters if p.get('in') == 'query']
        
        if query_params:
            request["request"]["url"]["query"] = []
            for param in query_params:
                request["request"]["url"]["query"].append({
                    "key": param['name'],
                    "value": "",
                    "description": param.get('description', ''),
                    "disabled": not param.get('required', False)
                })
        
        return request
    
    def generate_markdown_docs(self):
        """Generate comprehensive Markdown documentation."""
        print("Generating Markdown documentation...")
        
        try:
            # Read OpenAPI schema
            schema_file = self.docs_dir / 'openapi-schema.json'
            if not schema_file.exists():
                print("❌ OpenAPI schema not found. Generate schema first.")
                return False
            
            with open(schema_file, 'r') as f:
                schema = json.load(f)
            
            # Generate main documentation
            self._generate_main_readme(schema)
            self._generate_authentication_guide()
            self._generate_api_reference(schema)
            self._generate_testing_guide()
            self._generate_examples_guide()
            
            print("✅ Markdown documentation generated in docs/ directory")
            return True
            
        except Exception as e:
            print(f"❌ Failed to generate Markdown documentation: {e}")
            return False
    
    def _generate_main_readme(self, schema):
        """Generate main README for API documentation."""
        info = schema.get('info', {})
        
        content = f"""# {info.get('title', 'HireWise API')}

{info.get('description', 'AI-powered resume matching and job portal API')}

**Version:** {info.get('version', '1.0.0')}

## Quick Start

1. [Authentication Guide](authentication.md) - Learn how to authenticate with the API
2. [API Reference](api-reference.md) - Complete API endpoint documentation
3. [Testing Guide](testing.md) - How to test the API
4. [Examples](examples.md) - Code examples and use cases

## Base URL

- **Development:** `http://localhost:8000`
- **Production:** `https://api.hirewise.com`

## API Documentation

- **Interactive Docs (Swagger):** `/api/docs/`
- **ReDoc:** `/api/redoc/`
- **OpenAPI Schema:** `/api/schema/`

## Features

- 🔐 JWT Authentication
- 📝 Job Management
- 🤖 AI-Powered Resume Parsing
- 🎯 ML-Based Job Matching
- 📱 Real-time Notifications
- 🔒 Secure File Upload
- 📊 Analytics and Reporting

## Authentication

All API endpoints require authentication using JWT tokens. See the [Authentication Guide](authentication.md) for details.

```bash
# Example authenticated request
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
     https://api.hirewise.com/api/job-posts/
```

## Rate Limiting

- **Authenticated users:** 1000 requests per hour
- **Anonymous users:** 100 requests per hour

## Support

- **Documentation:** [docs.hirewise.com](https://docs.hirewise.com)
- **Support Email:** api-support@hirewise.com
- **GitHub Issues:** [github.com/hirewise/backend/issues](https://github.com/hirewise/backend/issues)

## License

This API is licensed under the MIT License.
"""
        
        with open(self.docs_dir / 'README.md', 'w') as f:
            f.write(content)
    
    def _generate_authentication_guide(self):
        """Generate authentication guide."""
        content = """# Authentication Guide

HireWise API uses JWT (JSON Web Tokens) for authentication. This guide explains how to authenticate and manage tokens.

## Registration

Register a new user account:

```bash
curl -X POST http://localhost:8000/api/auth/jwt/register/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "johndoe",
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "job_seeker",
    "phone_number": "+1234567890"
  }'
```

**Response:**
```json
{
  "user": {
    "id": "uuid-string",
    "username": "johndoe",
    "email": "john.doe@example.com",
    "user_type": "job_seeker"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Login

Login with existing credentials:

```bash
curl -X POST http://localhost:8000/api/auth/jwt/login/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!"
  }'
```

## Using Access Tokens

Include the access token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
     http://localhost:8000/api/job-posts/
```

## Token Refresh

Access tokens expire after 1 hour. Use the refresh token to get a new access token:

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

## Logout

Blacklist the refresh token to logout:

```bash
curl -X POST http://localhost:8000/api/auth/token/blacklist/ \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

## User Types

- **job_seeker**: Can browse jobs, apply to positions, upload resumes
- **recruiter**: Can post jobs, manage applications, view candidate profiles
- **admin**: Full system access

## Error Handling

Authentication errors return appropriate HTTP status codes:

- **401 Unauthorized**: Invalid or missing token
- **403 Forbidden**: Valid token but insufficient permissions
- **400 Bad Request**: Invalid login credentials

```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid or expired token",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```
"""
        
        with open(self.docs_dir / 'authentication.md', 'w') as f:
            f.write(content)
    
    def _generate_api_reference(self, schema):
        """Generate API reference documentation."""
        content = """# API Reference

Complete reference for all HireWise API endpoints.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://api.hirewise.com`

## Common Headers

```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

## Pagination

List endpoints support pagination:

```
GET /api/job-posts/?page=2&page_size=20
```

**Response:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/job-posts/?page=3",
  "previous": "http://localhost:8000/api/job-posts/?page=1",
  "results": [...]
}
```

## Filtering and Search

Many endpoints support filtering and search:

```
GET /api/job-posts/?search=python&location=san+francisco&experience_level=senior
```

## Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field_name": ["Field-specific error messages"]
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Endpoints

"""
        
        # Group endpoints by tags
        endpoints_by_tag = {}
        
        for path, methods in schema.get('paths', {}).items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
                    tags = details.get('tags', ['Uncategorized'])
                    tag = tags[0] if tags else 'Uncategorized'
                    
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    
                    endpoints_by_tag[tag].append({
                        'path': path,
                        'method': method.upper(),
                        'details': details
                    })
        
        # Generate documentation for each tag
        for tag, endpoints in endpoints_by_tag.items():
            content += f"\\n### {tag}\\n\\n"
            
            for endpoint in endpoints:
                details = endpoint['details']
                content += f"#### {endpoint['method']} {endpoint['path']}\\n\\n"
                content += f"**Summary:** {details.get('summary', 'No summary')}\\n\\n"
                
                if details.get('description'):
                    content += f"**Description:** {details['description']}\\n\\n"
                
                # Parameters
                parameters = details.get('parameters', [])
                if parameters:
                    content += "**Parameters:**\\n\\n"
                    for param in parameters:
                        required = " (required)" if param.get('required') else ""
                        content += f"- `{param['name']}`{required}: {param.get('description', 'No description')}\\n"
                    content += "\\n"
                
                # Request body
                request_body = details.get('requestBody')
                if request_body:
                    content += "**Request Body:**\\n\\n"
                    content += "```json\\n"
                    content += "// Example request body\\n"
                    content += "{}\\n"
                    content += "```\\n\\n"
                
                # Responses
                responses = details.get('responses', {})
                if responses:
                    content += "**Responses:**\\n\\n"
                    for status_code, response_details in responses.items():
                        description = response_details.get('description', 'No description')
                        content += f"- `{status_code}`: {description}\\n"
                    content += "\\n"
                
                content += "---\\n\\n"
        
        with open(self.docs_dir / 'api-reference.md', 'w') as f:
            f.write(content)
    
    def _generate_testing_guide(self):
        """Generate testing guide."""
        content = """# Testing Guide

This guide explains how to test the HireWise API using various tools and methods.

## Running Tests

### Unit Tests

```bash
python test_runner.py unit
```

### Integration Tests

```bash
python test_runner.py integration
```

### Performance Tests

```bash
python test_runner.py performance
```

### All Tests

```bash
python test_runner.py all
```

## Manual Testing

### Using cURL

Test authentication:

```bash
# Register
curl -X POST http://localhost:8000/api/auth/jwt/register/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirm": "testpass123",
    "user_type": "job_seeker"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/jwt/login/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'

# Use token
curl -H "Authorization: Bearer YOUR_TOKEN" \\
     http://localhost:8000/api/job-posts/
```

### Using Postman

1. Import the Postman collection: `docs/HireWise-API.postman_collection.json`
2. Set up environment variables:
   - `base_url`: `http://localhost:8000`
   - `access_token`: Your JWT access token
3. Run the collection tests

### Using Python Requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/api/auth/jwt/login/", json={
    "username": "testuser",
    "password": "testpass123"
})

token = response.json()["access"]

# Make authenticated request
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/api/job-posts/", headers=headers)

print(response.json())
```

## Test Data

### Creating Test Users

```python
from factories import UserFactory, JobSeekerProfileFactory

# Create job seeker
job_seeker = UserFactory(user_type='job_seeker')
profile = JobSeekerProfileFactory(user=job_seeker)

# Create recruiter
recruiter = UserFactory(user_type='recruiter')
```

### Creating Test Jobs

```python
from factories import JobPostFactory

job = JobPostFactory(
    title='Python Developer',
    skills_required='Python,Django,React'
)
```

## Performance Testing

### Using Locust

```bash
# Install locust
pip install locust

# Run performance tests
locust -f matcher/tests_performance.py --host=http://localhost:8000
```

### Load Testing Scenarios

1. **User Registration Load**
   - 100 users registering simultaneously
   - Expected: < 2 seconds response time

2. **Job Search Load**
   - 500 concurrent job searches
   - Expected: < 1 second response time

3. **Application Submission Load**
   - 200 concurrent job applications
   - Expected: < 3 seconds response time

## Test Coverage

Generate coverage report:

```bash
python test_runner.py coverage
```

View coverage report:
```bash
open htmlcov/index.html
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Main branch commits
- Scheduled daily runs

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python test_runner.py all
```

## Debugging Tests

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Reset test database
   python manage.py migrate --run-syncdb
   ```

2. **Authentication Failures**
   ```python
   # Check token expiration
   from rest_framework_simplejwt.tokens import AccessToken
   token = AccessToken("your_token_here")
   print(token.payload)
   ```

3. **File Upload Issues**
   ```python
   # Check file permissions
   import os
   print(os.access('/path/to/media', os.W_OK))
   ```

### Test Debugging Tools

```python
import pytest

# Run specific test with debugging
pytest -xvs matcher/tests_api_integration.py::TestAuthenticationWorkflow::test_user_registration

# Run with pdb debugger
pytest --pdb matcher/tests_api_integration.py
```
"""
        
        with open(self.docs_dir / 'testing.md', 'w') as f:
            f.write(content)
    
    def _generate_examples_guide(self):
        """Generate examples guide."""
        content = """# API Examples

Practical examples for common HireWise API use cases.

## Complete User Journey

### 1. Job Seeker Registration and Job Application

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Register as job seeker
registration_data = {
    "username": "johndoe",
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "job_seeker",
    "phone_number": "+1234567890"
}

response = requests.post(f"{BASE_URL}/api/auth/jwt/register/", json=registration_data)
auth_data = response.json()
access_token = auth_data["access"]

headers = {"Authorization": f"Bearer {access_token}"}

# 2. Create job seeker profile
profile_data = {
    "location": "San Francisco, CA",
    "experience_level": "mid",
    "current_position": "Software Engineer",
    "expected_salary": 90000,
    "skills": "Python,Django,React,JavaScript",
    "bio": "Passionate software engineer with 3 years of experience"
}

response = requests.post(f"{BASE_URL}/api/job-seeker-profiles/", 
                        json=profile_data, headers=headers)

# 3. Upload and parse resume
resume_data = {
    "original_filename": "john_doe_resume.pdf",
    "parsed_text": "John Doe\\nSoftware Engineer\\nPython, Django, React experience",
    "is_primary": True
}

response = requests.post(f"{BASE_URL}/api/resumes/", 
                        json=resume_data, headers=headers)
resume_id = response.json()["id"]

# 4. Browse available jobs
response = requests.get(f"{BASE_URL}/api/job-posts/", headers=headers)
jobs = response.json()["results"]

# 5. Search for Python jobs
response = requests.get(f"{BASE_URL}/api/job-posts/?search=Python", headers=headers)
python_jobs = response.json()["results"]

# 6. Apply to a job
if python_jobs:
    job_id = python_jobs[0]["id"]
    application_data = {
        "job_post": job_id,
        "resume": resume_id,
        "cover_letter": "I am very interested in this Python developer position..."
    }
    
    response = requests.post(f"{BASE_URL}/api/applications/", 
                            json=application_data, headers=headers)
    print("Application submitted:", response.json())
```

### 2. Recruiter Job Posting and Application Management

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Register as recruiter
registration_data = {
    "username": "recruiter1",
    "email": "recruiter@techcorp.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Jane",
    "last_name": "Smith",
    "user_type": "recruiter",
    "phone_number": "+1234567891"
}

response = requests.post(f"{BASE_URL}/api/auth/jwt/register/", json=registration_data)
auth_data = response.json()
access_token = auth_data["access"]

headers = {"Authorization": f"Bearer {access_token}"}

# 2. Create recruiter profile
profile_data = {
    "company_name": "Tech Corp",
    "company_website": "https://techcorp.com",
    "company_size": "51-200",
    "industry": "Technology",
    "company_description": "Leading technology company",
    "location": "San Francisco, CA"
}

response = requests.post(f"{BASE_URL}/api/recruiter-profiles/", 
                        json=profile_data, headers=headers)

# 3. Post a job
job_data = {
    "title": "Senior Python Developer",
    "description": "We are looking for an experienced Python developer...",
    "requirements": "Python, Django, REST APIs, 5+ years experience",
    "location": "San Francisco, CA",
    "job_type": "full_time",
    "experience_level": "senior",
    "salary_min": 120000,
    "salary_max": 150000,
    "skills_required": "Python,Django,REST APIs,PostgreSQL"
}

response = requests.post(f"{BASE_URL}/api/job-posts/", 
                        json=job_data, headers=headers)
job_id = response.json()["id"]

# 4. View applications for the job
response = requests.get(f"{BASE_URL}/api/applications/?job_post={job_id}", 
                       headers=headers)
applications = response.json()["results"]

# 5. Update application status
if applications:
    application_id = applications[0]["id"]
    update_data = {
        "status": "interview",
        "recruiter_notes": "Promising candidate, schedule interview"
    }
    
    response = requests.patch(f"{BASE_URL}/api/applications/{application_id}/", 
                             json=update_data, headers=headers)
    print("Application updated:", response.json())
```

## AI Features

### Resume Parsing

```python
import requests

# Parse resume text with AI
parse_data = {
    "text_content": '''
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
    '''
}

response = requests.post(f"{BASE_URL}/api/parse-resume/", 
                        json=parse_data, headers=headers)

parsed_data = response.json()
print("Parsed Skills:", parsed_data["key_skills"])
print("Experience Years:", parsed_data["experience_years"])
print("Summary:", parsed_data["summary"])
```

### Job Matching

```python
# Calculate match score between resume and job
match_data = {
    "resume_id": "resume-uuid",
    "job_id": "job-uuid"
}

response = requests.post(f"{BASE_URL}/api/calculate-match-score/", 
                        json=match_data, headers=headers)

match_result = response.json()
print(f"Match Score: {match_result['score']}%")
print("Matching Skills:", match_result["matching_skills"])
print("Missing Skills:", match_result["missing_skills"])
```

## File Upload

### Secure Resume Upload

```python
import requests

# Upload resume file
files = {
    'file': ('resume.pdf', open('path/to/resume.pdf', 'rb'), 'application/pdf')
}

data = {
    'original_filename': 'john_doe_resume.pdf',
    'is_primary': True
}

response = requests.post(f"{BASE_URL}/api/files/upload-resume/", 
                        files=files, data=data, headers=headers)

if response.status_code == 201:
    print("Resume uploaded successfully")
    resume_data = response.json()
    print("Resume ID:", resume_data["id"])
else:
    print("Upload failed:", response.json())
```

## WebSocket Notifications

### Real-time Notifications

```javascript
// JavaScript WebSocket client
const ws = new WebSocket('ws://localhost:8000/ws/notifications/');

ws.onopen = function(event) {
    console.log('Connected to notifications');
    
    // Send authentication
    ws.send(JSON.stringify({
        'type': 'authenticate',
        'token': 'your-jwt-token'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Notification received:', data);
    
    switch(data.type) {
        case 'job_posted':
            console.log('New job posted:', data.job_title);
            break;
        case 'application_status_changed':
            console.log('Application status changed:', data.status);
            break;
        case 'match_score_calculated':
            console.log('Match score calculated:', data.score);
            break;
    }
};

ws.onclose = function(event) {
    console.log('Disconnected from notifications');
};
```

## Error Handling

### Handling API Errors

```python
import requests

def make_api_request(url, method='GET', data=None, headers=None):
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        
        # Check for HTTP errors
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            error_data = response.json()
            print("Validation Error:", error_data["error"]["details"])
        elif response.status_code == 401:
            print("Authentication Error: Invalid or expired token")
        elif response.status_code == 403:
            print("Permission Error: Insufficient permissions")
        elif response.status_code == 404:
            print("Not Found: Resource does not exist")
        else:
            print(f"HTTP Error {response.status_code}: {e}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        
    return None

# Usage
result = make_api_request(
    f"{BASE_URL}/api/job-posts/",
    headers={"Authorization": f"Bearer {access_token}"}
)
```

## Batch Operations

### Bulk Job Applications

```python
import requests
import concurrent.futures

def apply_to_job(job_id, resume_id, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    application_data = {
        "job_post": job_id,
        "resume": resume_id,
        "cover_letter": f"Application for job {job_id}"
    }
    
    response = requests.post(f"{BASE_URL}/api/applications/", 
                            json=application_data, headers=headers)
    return response.status_code == 201

# Apply to multiple jobs concurrently
job_ids = ["job-1", "job-2", "job-3"]
resume_id = "resume-uuid"

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(apply_to_job, job_id, resume_id, access_token)
        for job_id in job_ids
    ]
    
    results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
print(f"Successfully applied to {sum(results)} out of {len(job_ids)} jobs")
```

## Analytics and Reporting

### Job Analytics

```python
# Get job analytics
response = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=headers)
stats = response.json()

print("Dashboard Statistics:")
print(f"Total Jobs Posted: {stats['total_jobs']}")
print(f"Total Applications: {stats['total_applications']}")
print(f"Average Match Score: {stats['avg_match_score']}")
```

These examples demonstrate the most common use cases for the HireWise API. For more detailed information, refer to the [API Reference](api-reference.md).
"""
        
        with open(self.docs_dir / 'examples.md', 'w') as f:
            f.write(content)
    
    def generate_all_documentation(self):
        """Generate all documentation files."""
        print("🚀 Generating HireWise API Documentation")
        print("=" * 50)
        
        success = True
        
        # Generate OpenAPI schema
        if not self.generate_openapi_schema():
            success = False
        
        # Generate Postman collection
        if not self.generate_postman_collection():
            success = False
        
        # Generate Markdown documentation
        if not self.generate_markdown_docs():
            success = False
        
        if success:
            print("\n✅ All documentation generated successfully!")
            print(f"📁 Documentation available in: {self.docs_dir}")
            print("\nGenerated files:")
            print("- README.md - Main documentation")
            print("- authentication.md - Authentication guide")
            print("- api-reference.md - Complete API reference")
            print("- testing.md - Testing guide")
            print("- examples.md - Code examples")
            print("- openapi-schema.json - OpenAPI schema")
            print("- HireWise-API.postman_collection.json - Postman collection")
        else:
            print("\n❌ Some documentation generation failed")
        
        return success


def main():
    """Main entry point."""
    generator = APIDocumentationGenerator()
    success = generator.generate_all_documentation()
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()