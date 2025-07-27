# HireWise Backend API Testing Documentation

Generated on: 2025-07-27 21:19:43

## Overview

This document provides comprehensive documentation for testing the HireWise Backend API, including endpoint specifications, test coverage requirements, performance benchmarks, and testing strategies.

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description | Authentication | Performance Target |
|----------|--------|-------------|----------------|-------------------|
| `/api/v1/auth/jwt/register/` | POST | Register new user | None | < 300ms |
| `/api/v1/auth/jwt/login/` | POST | User login | None | < 200ms |
| `/api/v1/auth/jwt/logout/` | POST | User logout | JWT Bearer | < 100ms |

### Job Management Endpoints

| Endpoint | Method | Description | Authentication | Performance Target |
|----------|--------|-------------|----------------|-------------------|
| `/api/v1/job-posts/` | GET | List job postings | Optional | < 500ms |
| `/api/v1/job-posts/` | POST | Create job posting | JWT Bearer (recruiter) | < 200ms |
| `/api/v1/job-posts/{id}/` | GET | Get job details | Optional | < 100ms |

### Application Endpoints

| Endpoint | Method | Description | Authentication | Performance Target |
|----------|--------|-------------|----------------|-------------------|
| `/api/v1/applications/` | POST | Apply to job | JWT Bearer (job_seeker) | < 300ms |
| `/api/v1/applications/` | GET | List applications | JWT Bearer | < 200ms |

### AI Integration Endpoints

| Endpoint | Method | Description | Authentication | Performance Target |
|----------|--------|-------------|----------------|-------------------|
| `/api/v1/parse-resume/` | POST | Parse resume with AI | JWT Bearer (job_seeker) | < 5s |
| `/api/v1/calculate-match-score/` | POST | Calculate match score | JWT Bearer | < 2s |

## Test Coverage Requirements

### Overall Coverage Target: 90%

- **Unit Tests**: 95% coverage target
- **Integration Tests**: 85% coverage target
- **Performance Tests**: Benchmark compliance

### Test Files

- `tests_user_management.py` - User and profile management
- `tests_job_management.py` - Job CRUD operations
- `tests_application_system.py` - Application workflow
- `tests_jwt_auth.py` - JWT authentication
- `tests_ml_integration.py` - AI/ML services
- `tests_resume_parsing.py` - Resume parsing
- `tests_secure_file_upload.py` - File upload security
- `tests_websocket.py` - Real-time notifications
- `tests_comprehensive_integration.py` - End-to-end workflows
- `tests_performance.py` - Performance benchmarks

## Performance Benchmarks

### Response Time Targets

- Authentication: < 300ms average
- Job listing: < 500ms with pagination
- Job search: < 800ms with complex filters
- Resume parsing: < 5s for files up to 10MB
- Match score calculation: < 2s average

### Scalability Targets

- 100+ concurrent users
- 1000+ requests per second for read operations
- < 5 database queries per API call
- Support for 100K+ job postings

## Running Tests

### All Tests
```bash
python test_runner.py --verbose
```

### Unit Tests Only
```bash
python test_runner.py --unit-only
```

### Integration Tests Only
```bash
python test_runner.py --integration-only
```

### Performance Tests
```bash
python test_runner.py --performance --verbose
```

### Coverage Analysis
```bash
python test_runner.py --coverage-only
```

## API Documentation

- **Swagger UI**: `/api/v1/docs/`
- **ReDoc**: `/api/v1/redoc/`
- **OpenAPI Schema**: `/api/v1/schema/`

## Testing Tools

- **pytest**: Primary testing framework
- **factory_boy**: Test data generation
- **coverage.py**: Code coverage measurement
- **django.test**: Django-specific testing utilities
- **locust**: Load testing (optional)

## Continuous Integration

Tests are automatically run on:
- Pre-commit hooks (fast tests)
- Pull request creation (full test suite)
- Before deployment (all tests must pass)

## Security Testing

All endpoints are tested for:
- Authentication bypass attempts
- Authorization violations
- Input validation
- File upload security
- Rate limiting compliance

## Contact

For questions about testing or to report issues:
- API Support: api-support@hirewise.com
- Documentation: https://docs.hirewise.com/
