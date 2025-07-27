"""
Comprehensive API Testing Documentation for HireWise Backend.

This module provides documentation for all testing aspects including
API endpoints, test coverage, performance benchmarks, and testing strategies.
"""

import json
import os
from datetime import datetime
from pathlib import Path


class APITestDocumentationGenerator:
    """Generator for comprehensive API testing documentation."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.documentation = {
            'api_endpoints': {},
            'test_coverage': {},
            'performance_benchmarks': {},
            'testing_strategies': {},
            'examples': {}
        }
    
    def generate_endpoint_documentation(self):
        """Generate documentation for all API endpoints."""
        endpoints = {
            'Authentication': {
                'POST /api/v1/auth/jwt/register/': {
                    'description': 'Register new user with JWT tokens',
                    'authentication': 'None',
                    'parameters': ['username', 'email', 'password', 'user_type'],
                    'responses': {
                        '201': 'User created successfully with tokens',
                        '400': 'Validation error',
                        '409': 'User already exists'
                    },
                    'test_coverage': 'tests_jwt_auth.py::TestJWTRegistration',
                    'performance_target': '< 300ms average response time'
                },
                'POST /api/v1/auth/jwt/login/': {
                    'description': 'Authenticate user and receive JWT tokens',
                    'authentication': 'None',
                    'parameters': ['username', 'password'],
                    'responses': {
                        '200': 'Login successful with tokens',
                        '401': 'Invalid credentials'
                    },
                    'test_coverage': 'tests_jwt_auth.py::TestJWTLogin',
                    'performance_target': '< 200ms average response time'
                },
                'POST /api/v1/auth/jwt/logout/': {
                    'description': 'Logout user and blacklist refresh token',
                    'authentication': 'JWT Bearer Token',
                    'parameters': ['refresh_token'],
                    'responses': {
                        '200': 'Logout successful',
                        '401': 'Authentication required'
                    },
                    'test_coverage': 'tests_jwt_auth.py::TestJWTLogout',
                    'performance_target': '< 100ms average response time'
                }
            },
            'Job Management': {
                'GET /api/v1/job-posts/': {
                    'description': 'List job postings with filtering and search',
                    'authentication': 'Optional (public endpoint)',
                    'parameters': ['search', 'location', 'job_type', 'skills', 'page', 'page_size'],
                    'responses': {
                        '200': 'Paginated list of job postings'
                    },
                    'test_coverage': 'tests_job_management.py::TestJobPostList',
                    'performance_target': '< 500ms with 1000+ jobs'
                },
                'POST /api/v1/job-posts/': {
                    'description': 'Create new job posting (recruiters only)',
                    'authentication': 'JWT Bearer Token (recruiter)',
                    'parameters': ['title', 'description', 'location', 'job_type', 'skills_required'],
                    'responses': {
                        '201': 'Job posting created',
                        '400': 'Validation error',
                        '403': 'Permission denied'
                    },
                    'test_coverage': 'tests_job_management.py::TestJobPostCreate',
                    'performance_target': '< 200ms average response time'
                },
                'GET /api/v1/job-posts/{id}/': {
                    'description': 'Retrieve specific job posting',
                    'authentication': 'Optional',
                    'parameters': ['id (path parameter)'],
                    'responses': {
                        '200': 'Job posting details',
                        '404': 'Job not found'
                    },
                    'test_coverage': 'tests_job_management.py::TestJobPostDetail',
                    'performance_target': '< 100ms average response time'
                }
            },
            'Applications': {
                'POST /api/v1/applications/': {
                    'description': 'Apply to job posting',
                    'authentication': 'JWT Bearer Token (job_seeker)',
                    'parameters': ['job_post', 'resume', 'cover_letter'],
                    'responses': {
                        '201': 'Application submitted',
                        '400': 'Validation error or duplicate application',
                        '403': 'Permission denied'
                    },
                    'test_coverage': 'tests_application_system.py::TestApplicationCreate',
                    'performance_target': '< 300ms average response time'
                },
                'GET /api/v1/applications/': {
                    'description': 'List user applications',
                    'authentication': 'JWT Bearer Token',
                    'parameters': ['status', 'page', 'page_size'],
                    'responses': {
                        '200': 'Paginated list of applications'
                    },
                    'test_coverage': 'tests_application_system.py::TestApplicationList',
                    'performance_target': '< 200ms average response time'
                }
            },
            'Resume Parsing': {
                'POST /api/v1/parse-resume/': {
                    'description': 'Upload and parse resume with AI',
                    'authentication': 'JWT Bearer Token (job_seeker)',
                    'parameters': ['resume_file (multipart)'],
                    'responses': {
                        '200': 'Resume parsed successfully',
                        '400': 'Invalid file format',
                        '413': 'File too large',
                        '503': 'AI service unavailable'
                    },
                    'test_coverage': 'tests_resume_parsing.py::TestResumeParsingAPI',
                    'performance_target': '< 5s for files up to 10MB'
                },
                'POST /api/v1/parse-resume-async/': {
                    'description': 'Submit resume for asynchronous parsing',
                    'authentication': 'JWT Bearer Token (job_seeker)',
                    'parameters': ['resume_file (multipart)'],
                    'responses': {
                        '202': 'Parsing task submitted',
                        '400': 'Invalid file format'
                    },
                    'test_coverage': 'tests_resume_parsing.py::TestAsyncResumeParsingAPI',
                    'performance_target': '< 500ms task submission'
                }
            },
            'Match Scoring': {
                'POST /api/v1/calculate-match-score/': {
                    'description': 'Calculate AI-powered job match score',
                    'authentication': 'JWT Bearer Token',
                    'parameters': ['resume_id', 'job_id'],
                    'responses': {
                        '200': 'Match score calculated',
                        '404': 'Resume or job not found',
                        '503': 'ML service unavailable'
                    },
                    'test_coverage': 'tests_ml_integration.py::TestMatchScoreAPI',
                    'performance_target': '< 2s average calculation time'
                },
                'POST /api/v1/batch-calculate-match-scores/': {
                    'description': 'Calculate match scores for multiple resume-job pairs',
                    'authentication': 'JWT Bearer Token',
                    'parameters': ['resume_ids', 'job_ids'],
                    'responses': {
                        '202': 'Batch calculation task submitted'
                    },
                    'test_coverage': 'tests_ml_integration.py::TestBatchMatchScoreAPI',
                    'performance_target': '< 1s task submission'
                }
            },
            'File Management': {
                'POST /api/v1/files/upload/': {
                    'description': 'Secure file upload with validation',
                    'authentication': 'JWT Bearer Token',
                    'parameters': ['file (multipart)', 'file_type'],
                    'responses': {
                        '201': 'File uploaded successfully',
                        '400': 'Invalid file type or size',
                        '413': 'File too large'
                    },
                    'test_coverage': 'tests_secure_file_upload.py::TestSecureFileUpload',
                    'performance_target': '< 2s per MB uploaded'
                },
                'GET /api/v1/files/list/': {
                    'description': 'List user uploaded files',
                    'authentication': 'JWT Bearer Token',
                    'parameters': ['file_type', 'page', 'page_size'],
                    'responses': {
                        '200': 'Paginated list of files'
                    },
                    'test_coverage': 'tests_secure_file_upload.py::TestFileList',
                    'performance_target': '< 200ms average response time'
                }
            }
        }
        
        self.documentation['api_endpoints'] = endpoints
        return endpoints
    
    def generate_test_coverage_report(self):
        """Generate comprehensive test coverage documentation."""
        coverage_report = {
            'overall_coverage': {
                'target': '90%',
                'current': 'Run `python test_runner.py --coverage-only` to get current coverage',
                'critical_paths': [
                    'Authentication flows',
                    'Job CRUD operations',
                    'Application workflow',
                    'AI service integrations',
                    'File upload security'
                ]
            },
            'test_categories': {
                'unit_tests': {
                    'description': 'Test individual functions and methods in isolation',
                    'files': [
                        'tests_user_management.py',
                        'tests_job_management.py',
                        'tests_application_system.py',
                        'tests_jwt_auth.py',
                        'tests_ml_integration.py',
                        'tests_notification_system.py',
                        'tests_resume_parsing.py',
                        'tests_secure_file_upload.py',
                        'tests_websocket.py'
                    ],
                    'coverage_target': '95%'
                },
                'integration_tests': {
                    'description': 'Test complete workflows and API endpoint interactions',
                    'files': [
                        'tests_comprehensive_integration.py',
                        'tests_api_integration.py'
                    ],
                    'coverage_target': '85%'
                },
                'performance_tests': {
                    'description': 'Test response times, throughput, and scalability',
                    'files': [
                        'tests_performance.py'
                    ],
                    'coverage_target': 'Performance benchmarks met'
                }
            },
            'testing_tools': {
                'pytest': 'Primary testing framework',
                'factory_boy': 'Test data generation',
                'django_test': 'Django-specific testing utilities',
                'coverage.py': 'Code coverage measurement',
                'locust': 'Load testing (optional)'
            }
        }
        
        self.documentation['test_coverage'] = coverage_report
        return coverage_report
    
    def generate_performance_benchmarks(self):
        """Generate performance benchmark documentation."""
        benchmarks = {
            'response_time_targets': {
                'authentication': '< 300ms average',
                'job_listing': '< 500ms with pagination',
                'job_search': '< 800ms with complex filters',
                'application_creation': '< 300ms average',
                'resume_parsing': '< 5s for files up to 10MB',
                'match_score_calculation': '< 2s average',
                'file_upload': '< 2s per MB'
            },
            'throughput_targets': {
                'concurrent_users': '100+ simultaneous users',
                'requests_per_second': '1000+ RPS for read operations',
                'database_queries': '< 5 queries per API call',
                'memory_usage': '< 512MB for typical workload'
            },
            'scalability_metrics': {
                'database_records': 'Tested with 100K+ job postings',
                'file_storage': 'Supports TB-scale file storage',
                'websocket_connections': '1000+ concurrent connections',
                'background_tasks': 'Celery-based async processing'
            },
            'performance_testing': {
                'tools': ['pytest-benchmark', 'locust', 'django-debug-toolbar'],
                'environments': ['development', 'staging', 'production-like'],
                'monitoring': ['response times', 'error rates', 'resource usage'],
                'alerts': ['response time > 2s', 'error rate > 1%', 'memory usage > 80%']
            }
        }
        
        self.documentation['performance_benchmarks'] = benchmarks
        return benchmarks
    
    def generate_testing_strategies(self):
        """Generate testing strategy documentation."""
        strategies = {
            'test_driven_development': {
                'approach': 'Write tests before implementation',
                'benefits': ['Better design', 'Higher coverage', 'Fewer bugs'],
                'implementation': [
                    'Write failing test',
                    'Implement minimal code to pass',
                    'Refactor while keeping tests green'
                ]
            },
            'api_testing_strategy': {
                'levels': {
                    'unit': 'Test individual functions and methods',
                    'integration': 'Test API endpoints and workflows',
                    'contract': 'Test API schema and documentation',
                    'performance': 'Test response times and scalability'
                },
                'test_data_management': {
                    'factories': 'Use factory_boy for consistent test data',
                    'fixtures': 'Predefined data sets for specific scenarios',
                    'cleanup': 'Automatic cleanup after each test',
                    'isolation': 'Tests should not depend on each other'
                }
            },
            'continuous_testing': {
                'pre_commit_hooks': 'Run fast tests before commits',
                'ci_pipeline': 'Full test suite on pull requests',
                'deployment_gates': 'All tests must pass before deployment',
                'monitoring': 'Continuous monitoring in production'
            },
            'security_testing': {
                'authentication': 'Test JWT token validation',
                'authorization': 'Test role-based permissions',
                'input_validation': 'Test against injection attacks',
                'file_upload': 'Test malicious file detection',
                'rate_limiting': 'Test API rate limits'
            }
        }
        
        self.documentation['testing_strategies'] = strategies
        return strategies
    
    def generate_api_examples(self):
        """Generate comprehensive API usage examples."""
        examples = {
            'authentication_flow': {
                'description': 'Complete user authentication workflow',
                'steps': [
                    {
                        'step': 1,
                        'action': 'Register new user',
                        'request': {
                            'method': 'POST',
                            'url': '/api/v1/auth/jwt/register/',
                            'body': {
                                'username': 'john_doe',
                                'email': 'john@example.com',
                                'password': 'securepassword123',
                                'password_confirm': 'securepassword123',
                                'user_type': 'job_seeker'
                            }
                        },
                        'response': {
                            'status': 201,
                            'body': {
                                'user': {'id': 'uuid', 'username': 'john_doe'},
                                'tokens': {'access': 'jwt-token', 'refresh': 'refresh-token'}
                            }
                        }
                    },
                    {
                        'step': 2,
                        'action': 'Use access token for authenticated requests',
                        'request': {
                            'method': 'GET',
                            'url': '/api/v1/auth/profile/',
                            'headers': {'Authorization': 'Bearer jwt-token'}
                        },
                        'response': {
                            'status': 200,
                            'body': {'id': 'uuid', 'username': 'john_doe', 'email': 'john@example.com'}
                        }
                    }
                ]
            },
            'job_application_workflow': {
                'description': 'Complete job application process',
                'steps': [
                    {
                        'step': 1,
                        'action': 'Search for jobs',
                        'request': {
                            'method': 'GET',
                            'url': '/api/v1/job-posts/?search=Python&location=Remote'
                        }
                    },
                    {
                        'step': 2,
                        'action': 'Upload resume',
                        'request': {
                            'method': 'POST',
                            'url': '/api/v1/parse-resume/',
                            'body': 'multipart/form-data with resume file'
                        }
                    },
                    {
                        'step': 3,
                        'action': 'Apply to job',
                        'request': {
                            'method': 'POST',
                            'url': '/api/v1/applications/',
                            'body': {
                                'job_post': 'job-uuid',
                                'resume': 'resume-uuid',
                                'cover_letter': 'I am interested in this position...'
                            }
                        }
                    }
                ]
            },
            'ai_integration_example': {
                'description': 'AI-powered resume parsing and job matching',
                'steps': [
                    {
                        'step': 1,
                        'action': 'Parse resume with AI',
                        'request': {
                            'method': 'POST',
                            'url': '/api/v1/parse-resume/',
                            'body': 'multipart file upload'
                        },
                        'response': {
                            'parsed_data': {
                                'personal_info': {'name': 'John Doe'},
                                'skills': ['Python', 'Django'],
                                'experience': [{'company': 'Tech Corp'}]
                            }
                        }
                    },
                    {
                        'step': 2,
                        'action': 'Calculate match score',
                        'request': {
                            'method': 'POST',
                            'url': '/api/v1/calculate-match-score/',
                            'body': {'resume_id': 'uuid', 'job_id': 'uuid'}
                        },
                        'response': {
                            'overall_score': 87.5,
                            'matching_skills': ['Python', 'Django'],
                            'missing_skills': ['Docker']
                        }
                    }
                ]
            }
        }
        
        self.documentation['examples'] = examples
        return examples
    
    def generate_complete_documentation(self):
        """Generate complete API testing documentation."""
        print("Generating comprehensive API testing documentation...")
        
        self.generate_endpoint_documentation()
        self.generate_test_coverage_report()
        self.generate_performance_benchmarks()
        self.generate_testing_strategies()
        self.generate_api_examples()
        
        # Save documentation to file
        doc_path = self.base_dir / 'API_TESTING_DOCUMENTATION.json'
        with open(doc_path, 'w') as f:
            json.dump(self.documentation, f, indent=2, default=str)
        
        # Generate markdown documentation
        self._generate_markdown_documentation()
        
        print(f"Documentation generated:")
        print(f"- {doc_path}")
        print(f"- {self.base_dir / 'API_TESTING_DOCUMENTATION.md'}")
        
        return self.documentation
    
    def _generate_markdown_documentation(self):
        """Generate markdown version of the documentation."""
        md_content = f"""# HireWise Backend API Testing Documentation

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

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
| `/api/v1/job-posts/{{id}}/` | GET | Get job details | Optional | < 100ms |

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
"""
        
        md_path = self.base_dir / 'API_TESTING_DOCUMENTATION.md'
        with open(md_path, 'w') as f:
            f.write(md_content)


def main():
    """Generate comprehensive API testing documentation."""
    generator = APITestDocumentationGenerator()
    documentation = generator.generate_complete_documentation()
    
    print("\nDocumentation Summary:")
    print(f"- API Endpoints: {len(documentation['api_endpoints'])} categories")
    print(f"- Test Coverage: {len(documentation['test_coverage']['test_categories'])} test types")
    print(f"- Performance Benchmarks: {len(documentation['performance_benchmarks'])} categories")
    print(f"- Testing Strategies: {len(documentation['testing_strategies'])} strategies")
    print(f"- API Examples: {len(documentation['examples'])} workflow examples")


if __name__ == '__main__':
    main()