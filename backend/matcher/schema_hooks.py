"""
Schema hooks for DRF Spectacular API documentation customization.
"""

def preprocess_exclude_paths(endpoints):
    """
    Preprocessing hook to exclude certain paths from the schema.
    """
    filtered = []
    excluded_patterns = [
        '/admin/',
        '/api-auth/',
        '/api/schema/',
    ]
    
    for (path, path_regex, method, callback) in endpoints:
        # Skip paths that match excluded patterns
        if not any(pattern in path for pattern in excluded_patterns):
            filtered.append((path, path_regex, method, callback))
    
    return filtered


def postprocess_schema_enums(result, generator, request, public):
    """
    Postprocessing hook to customize enum representations in the schema.
    """
    # Add custom enum descriptions
    if 'components' in result and 'schemas' in result['components']:
        schemas = result['components']['schemas']
        
        # Customize user type enum
        for schema_name, schema in schemas.items():
            if 'enum' in schema and 'properties' in schema:
                if 'user_type' in schema['properties']:
                    schema['properties']['user_type']['description'] = (
                        "User role type. 'job_seeker' for candidates looking for jobs, "
                        "'recruiter' for employers posting jobs, 'admin' for system administrators."
                    )
                
                if 'status' in schema['properties']:
                    schema['properties']['status']['description'] = (
                        "Application status. Possible values: 'pending', 'reviewed', "
                        "'interview_scheduled', 'rejected', 'accepted'."
                    )
    
    return result


def postprocess_schema_security(result, generator, request, public):
    """
    Postprocessing hook to add security requirements to endpoints.
    """
    if 'paths' in result:
        for path, methods in result['paths'].items():
            for method, operation in methods.items():
                # Skip OPTIONS method
                if method.upper() == 'OPTIONS':
                    continue
                
                # Add JWT security to all endpoints except auth endpoints
                if not any(auth_path in path for auth_path in ['/auth/jwt/login/', '/auth/jwt/register/', '/auth/register/', '/auth/login/']):
                    if 'security' not in operation:
                        operation['security'] = [{'jwtAuth': []}]
                
                # Add response examples for common error codes
                if 'responses' not in operation:
                    operation['responses'] = {}
                
                # Add common error responses
                if '401' not in operation['responses']:
                    operation['responses']['401'] = {
                        'description': 'Authentication credentials were not provided or are invalid.',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'error': {
                                            'type': 'object',
                                            'properties': {
                                                'code': {'type': 'string', 'example': 'AUTHENTICATION_FAILED'},
                                                'message': {'type': 'string', 'example': 'Invalid or expired token'},
                                                'timestamp': {'type': 'string', 'format': 'date-time'}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                
                if '403' not in operation['responses']:
                    operation['responses']['403'] = {
                        'description': 'Permission denied.',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'error': {
                                            'type': 'object',
                                            'properties': {
                                                'code': {'type': 'string', 'example': 'PERMISSION_DENIED'},
                                                'message': {'type': 'string', 'example': 'You do not have permission to perform this action'},
                                                'timestamp': {'type': 'string', 'format': 'date-time'}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                
                if '500' not in operation['responses']:
                    operation['responses']['500'] = {
                        'description': 'Internal server error.',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'error': {
                                            'type': 'object',
                                            'properties': {
                                                'code': {'type': 'string', 'example': 'INTERNAL_SERVER_ERROR'},
                                                'message': {'type': 'string', 'example': 'An unexpected error occurred'},
                                                'timestamp': {'type': 'string', 'format': 'date-time'}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
    
    return result