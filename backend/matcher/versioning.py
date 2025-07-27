"""
API versioning utilities for HireWise Backend.

This module provides utilities for managing API versions, deprecation warnings,
and version-specific behavior.
"""

from rest_framework.versioning import URLPathVersioning
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import warnings


class HireWiseAPIVersioning(URLPathVersioning):
    """
    Custom API versioning class with deprecation support.
    """
    default_version = 'v1'
    allowed_versions = ['v1']
    version_param = 'version'
    
    # Version deprecation information
    DEPRECATED_VERSIONS = {
        # Example: 'v0': {'deprecated_date': '2024-01-01', 'sunset_date': '2024-06-01'}
    }
    
    def determine_version(self, request, *args, **kwargs):
        """
        Determine the API version and add deprecation warnings if needed.
        """
        version = super().determine_version(request, *args, **kwargs)
        
        # Add deprecation warning if version is deprecated
        if version in self.DEPRECATED_VERSIONS:
            deprecation_info = self.DEPRECATED_VERSIONS[version]
            warning_message = (
                f"API version {version} is deprecated. "
                f"Please migrate to the latest version. "
                f"This version will be sunset on {deprecation_info.get('sunset_date', 'TBD')}."
            )
            warnings.warn(warning_message, DeprecationWarning)
            
            # Add deprecation header to response
            if hasattr(request, '_request'):
                request._request.META['HTTP_API_DEPRECATION_WARNING'] = warning_message
        
        return version


def add_version_headers(response, request):
    """
    Add version-related headers to API responses.
    """
    if hasattr(request, 'version'):
        response['API-Version'] = request.version
        response['API-Supported-Versions'] = ','.join(settings.REST_FRAMEWORK.get('ALLOWED_VERSIONS', ['v1']))
        
        # Add deprecation warning header if applicable
        if hasattr(request, '_request') and 'HTTP_API_DEPRECATION_WARNING' in request._request.META:
            response['API-Deprecation-Warning'] = request._request.META['HTTP_API_DEPRECATION_WARNING']
    
    return response


class VersionedAPIResponse(Response):
    """
    Custom response class that automatically adds version headers.
    """
    def __init__(self, data=None, status=None, template_name=None, headers=None, 
                 exception=False, content_type=None, request=None):
        super().__init__(data, status, template_name, headers, exception, content_type)
        
        if request:
            self = add_version_headers(self, request)


def version_specific_behavior(version, behaviors):
    """
    Decorator for implementing version-specific behavior in views.
    
    Usage:
    @version_specific_behavior('v1', {
        'v1': lambda self, request: self.handle_v1(request),
        'v2': lambda self, request: self.handle_v2(request),
    })
    def my_view(self, request):
        # Default behavior
        pass
    """
    def decorator(func):
        def wrapper(self, request, *args, **kwargs):
            request_version = getattr(request, 'version', 'v1')
            
            if request_version in behaviors:
                return behaviors[request_version](self, request, *args, **kwargs)
            
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


class APIVersionInfo:
    """
    Class to manage API version information and compatibility.
    """
    
    VERSIONS = {
        'v1': {
            'release_date': '2024-01-15',
            'status': 'stable',
            'description': 'Initial stable release with core functionality',
            'features': [
                'JWT Authentication',
                'Job Management',
                'Resume Parsing with Google Gemini',
                'ML-based Job Matching',
                'Real-time Notifications',
                'File Upload System'
            ],
            'breaking_changes': [],
            'deprecated_features': []
        }
        # Future versions can be added here
    }
    
    @classmethod
    def get_version_info(cls, version):
        """Get information about a specific API version."""
        return cls.VERSIONS.get(version, {})
    
    @classmethod
    def get_all_versions(cls):
        """Get information about all API versions."""
        return cls.VERSIONS
    
    @classmethod
    def is_version_supported(cls, version):
        """Check if a version is currently supported."""
        version_info = cls.get_version_info(version)
        return version_info.get('status') in ['stable', 'beta']
    
    @classmethod
    def get_latest_version(cls):
        """Get the latest stable version."""
        stable_versions = [
            v for v, info in cls.VERSIONS.items() 
            if info.get('status') == 'stable'
        ]
        return max(stable_versions) if stable_versions else 'v1'


def create_version_info_response():
    """
    Create a response with API version information.
    """
    return Response({
        'api_name': 'HireWise API',
        'current_version': APIVersionInfo.get_latest_version(),
        'supported_versions': list(APIVersionInfo.VERSIONS.keys()),
        'versions': APIVersionInfo.get_all_versions(),
        'documentation_url': '/api/docs/',
        'contact': {
            'email': 'api-support@hirewise.com',
            'documentation': 'https://docs.hirewise.com/'
        }
    })


# Middleware for adding version headers to all responses
class APIVersionMiddleware:
    """
    Middleware to add API version headers to all responses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only add headers to API responses
        if request.path.startswith('/api/'):
            response = add_version_headers(response, request)
        
        return response