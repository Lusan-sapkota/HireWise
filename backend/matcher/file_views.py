"""
Secure file upload and serving views for the HireWise platform.
"""

import os
import mimetypes
from pathlib import Path
from typing import Dict, Any

from django.http import HttpResponse, Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import logging

from .file_utils import FileSecurityValidator, SecureFileStorage, FileAccessController
from .models import User, Resume
from .permissions import IsJobSeeker, IsRecruiter

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def secure_file_upload(request):
    """
    Secure file upload endpoint with comprehensive validation and security checks.
    
    Supports multiple file types: PDF, DOCX, DOC, TXT, and images.
    """
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = request.FILES['file']
    file_type = request.data.get('file_type', 'pdf')  # Default to PDF
    
    # Validate file type parameter
    allowed_types = ['pdf', 'docx', 'doc', 'txt', 'image']
    if file_type not in allowed_types:
        return Response(
            {
                'error': f'Invalid file_type. Allowed types: {", ".join(allowed_types)}'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Perform comprehensive security validation
        validation_result = FileSecurityValidator.validate_file(uploaded_file, file_type)
        
        if not validation_result['is_valid']:
            logger.warning(
                f"File upload rejected for user {request.user.username}: "
                f"{validation_result['errors']}"
            )
            return Response(
                {
                    'error': 'File validation failed',
                    'details': validation_result['errors'],
                    'warnings': validation_result.get('warnings', [])
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store file securely
        storage_manager = SecureFileStorage()
        storage_result = storage_manager.store_file(uploaded_file, request.user, file_type)
        
        if not storage_result['success']:
            logger.error(f"File storage failed for user {request.user.username}: {storage_result['error']}")
            return Response(
                {'error': 'File storage failed', 'details': storage_result['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Generate secure access URL
        secure_url = FileAccessController.get_secure_file_url(
            storage_result['stored_path'],
            str(request.user.id),
            expires_in=3600  # 1 hour
        )
        
        # Prepare response
        response_data = {
            'success': True,
            'message': 'File uploaded successfully',
            'file_info': {
                'original_filename': storage_result['original_filename'],
                'secure_filename': storage_result['secure_filename'],
                'file_size': storage_result['file_size'],
                'file_type': file_type,
                'upload_timestamp': storage_result['storage_timestamp']
            },
            'security_info': {
                'file_hash': storage_result['file_hash'],
                'validation_passed': True,
                'warnings': validation_result.get('warnings', [])
            },
            'access_info': {
                'secure_url': secure_url,
                'expires_in': 3600
            }
        }
        
        logger.info(f"File uploaded successfully by user {request.user.username}: {storage_result['stored_path']}")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsJobSeeker])
def upload_resume(request):
    """
    Specialized endpoint for resume uploads with automatic parsing.
    """
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No resume file provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = request.FILES['file']
    
    try:
        # Validate resume file (PDF, DOCX, DOC only)
        file_extension = Path(uploaded_file.name).suffix.lower()
        if file_extension == '.pdf':
            file_type = 'pdf'
        elif file_extension == '.docx':
            file_type = 'docx'
        elif file_extension == '.doc':
            file_type = 'doc'
        else:
            return Response(
                {
                    'error': 'Invalid resume format. Only PDF, DOCX, and DOC files are supported.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform security validation
        validation_result = FileSecurityValidator.validate_file(uploaded_file, file_type)
        
        if not validation_result['is_valid']:
            return Response(
                {
                    'error': 'Resume validation failed',
                    'details': validation_result['errors']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store resume securely
        storage_manager = SecureFileStorage()
        storage_result = storage_manager.store_file(uploaded_file, request.user, 'resume')
        
        if not storage_result['success']:
            return Response(
                {'error': 'Resume storage failed', 'details': storage_result['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Create Resume record
        resume = Resume.objects.create(
            job_seeker=request.user,
            file=storage_result['stored_path'],
            original_filename=storage_result['original_filename'],
            file_size=storage_result['file_size']
        )
        
        # Generate secure access URL
        secure_url = FileAccessController.get_secure_file_url(
            storage_result['stored_path'],
            str(request.user.id)
        )
        
        response_data = {
            'success': True,
            'message': 'Resume uploaded successfully',
            'resume_id': str(resume.id),
            'file_info': {
                'original_filename': storage_result['original_filename'],
                'file_size': storage_result['file_size'],
                'upload_timestamp': storage_result['storage_timestamp']
            },
            'access_info': {
                'secure_url': secure_url
            }
        }
        
        logger.info(f"Resume uploaded successfully by user {request.user.username}: {resume.id}")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def serve_secure_file(request, file_path):
    """
    Serve files with access control and secure URL verification.
    """
    # Extract URL parameters
    expires_at = request.GET.get('expires')
    signature = request.GET.get('signature')
    user_id = request.GET.get('user')
    
    if not all([expires_at, signature, user_id]):
        return Response(
            {'error': 'Invalid secure URL parameters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        expires_at = int(expires_at)
    except ValueError:
        return Response(
            {'error': 'Invalid expiration timestamp'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify secure URL
    url_valid, reason = FileAccessController.verify_secure_url(
        file_path, user_id, expires_at, signature
    )
    
    if not url_valid:
        logger.warning(f"Secure URL verification failed: {reason}")
        return Response(
            {'error': f'URL verification failed: {reason}'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check file access permissions
    can_access, access_reason = FileAccessController.can_access_file(
        request.user, file_path, user_id
    )
    
    if not can_access:
        logger.warning(
            f"File access denied for user {request.user.username}: {access_reason}"
        )
        return Response(
            {'error': f'Access denied: {access_reason}'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Serve the file
    try:
        if not default_storage.exists(file_path):
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get file content and metadata
        file_content = default_storage.open(file_path, 'rb').read()
        file_size = default_storage.size(file_path)
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Create response
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Length'] = file_size
        response['Content-Disposition'] = f'inline; filename="{Path(file_path).name}"'
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
        
        logger.info(f"File served successfully: {file_path} to user {request.user.username}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving file {file_path}: {str(e)}")
        return Response(
            {'error': 'Error serving file', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_file(request, file_id):
    """
    Delete a file with proper authorization checks.
    """
    try:
        # For resume files, check Resume model
        try:
            resume = get_object_or_404(Resume, id=file_id)
            
            # Check ownership
            if resume.job_seeker != request.user and not request.user.is_staff:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Delete file from storage
            storage_manager = SecureFileStorage()
            file_deleted = storage_manager.delete_file(resume.file.name)
            
            if file_deleted:
                # Delete database record
                resume.delete()
                
                logger.info(f"Resume deleted successfully: {file_id} by user {request.user.username}")
                
                return Response(
                    {'success': True, 'message': 'File deleted successfully'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'File deletion failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Resume.DoesNotExist:
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_files(request):
    """
    List all files belonging to the authenticated user.
    """
    try:
        files_list = []
        
        # Get user's resumes
        if request.user.user_type == 'job_seeker':
            resumes = Resume.objects.filter(job_seeker=request.user).order_by('-uploaded_at')
            
            for resume in resumes:
                # Generate secure URL for each file
                secure_url = FileAccessController.get_secure_file_url(
                    resume.file.name,
                    str(request.user.id)
                )
                
                files_list.append({
                    'id': str(resume.id),
                    'type': 'resume',
                    'original_filename': resume.original_filename,
                    'file_size': resume.file_size,
                    'uploaded_at': resume.uploaded_at.isoformat(),
                    'is_primary': resume.is_primary,
                    'secure_url': secure_url
                })
        
        return Response(
            {
                'success': True,
                'files': files_list,
                'total_count': len(files_list)
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error listing user files: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cleanup_old_files(request):
    """
    Admin endpoint to clean up old files.
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        days_old = int(request.data.get('days_old', 30))
        file_type = request.data.get('file_type')  # Optional filter
        
        storage_manager = SecureFileStorage()
        cleanup_stats = storage_manager.cleanup_old_files(days_old, file_type)
        
        logger.info(f"File cleanup completed by admin {request.user.username}: {cleanup_stats}")
        
        return Response(
            {
                'success': True,
                'message': 'File cleanup completed',
                'statistics': cleanup_stats
            },
            status=status.HTTP_200_OK
        )
        
    except ValueError:
        return Response(
            {'error': 'Invalid days_old parameter'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def file_validation_info(request):
    """
    Get information about file validation rules and limits.
    """
    try:
        validation_info = {
            'allowed_file_types': {},
            'security_checks': [
                'Filename security validation',
                'File size limits',
                'Magic bytes verification',
                'Content scanning for malicious patterns',
                'MIME type validation'
            ],
            'max_file_sizes': {},
            'supported_extensions': {}
        }
        
        # Extract information from FileSecurityValidator
        for file_type, config in FileSecurityValidator.ALLOWED_FILE_TYPES.items():
            validation_info['allowed_file_types'][file_type] = {
                'extensions': config['extensions'],
                'mime_types': config['mime_types'],
                'max_size_bytes': config['max_size'],
                'max_size_mb': round(config['max_size'] / (1024 * 1024), 2)
            }
            
            validation_info['max_file_sizes'][file_type] = config['max_size']
            validation_info['supported_extensions'].update({
                ext: file_type for ext in config['extensions']
            })
        
        return Response(validation_info, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting validation info: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )