"""
Secure file upload utilities for the HireWise platform.
Implements comprehensive file validation, secure storage, and access control.
"""

import os
import hashlib
import mimetypes
import tempfile
import shutil

# Optional import for python-magic (for enhanced file type detection)
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import uuid
import logging

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Custom exception for security-related file upload errors"""
    pass


class FileSecurityValidator:
    """
    Comprehensive file security validator with malware detection,
    content validation, and security checks.
    """
    
    # Allowed file types with their MIME types and extensions
    ALLOWED_FILE_TYPES = {
        'pdf': {
            'extensions': ['.pdf'],
            'mime_types': ['application/pdf'],
            'max_size': 10 * 1024 * 1024,  # 10MB
            'magic_bytes': [b'%PDF']
        },
        'docx': {
            'extensions': ['.docx'],
            'mime_types': [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ],
            'max_size': 10 * 1024 * 1024,  # 10MB
            'magic_bytes': [b'PK\x03\x04']  # ZIP signature (DOCX is ZIP-based)
        },
        'doc': {
            'extensions': ['.doc'],
            'mime_types': ['application/msword'],
            'max_size': 10 * 1024 * 1024,  # 10MB
            'magic_bytes': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1']  # OLE signature
        },
        'txt': {
            'extensions': ['.txt'],
            'mime_types': ['text/plain'],
            'max_size': 1 * 1024 * 1024,  # 1MB
            'magic_bytes': []  # Text files don't have specific magic bytes
        },
        'image': {
            'extensions': ['.jpg', '.jpeg', '.png', '.gif'],
            'mime_types': ['image/jpeg', 'image/png', 'image/gif'],
            'max_size': 5 * 1024 * 1024,  # 5MB
            'magic_bytes': [
                b'\xff\xd8\xff',  # JPEG
                b'\x89PNG\r\n\x1a\n',  # PNG
                b'GIF87a',  # GIF87a
                b'GIF89a'   # GIF89a
            ]
        }
    }
    
    # Dangerous file extensions that should never be allowed
    DANGEROUS_EXTENSIONS = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.app', '.deb', '.pkg', '.dmg', '.iso', '.msi', '.sh',
        '.ps1', '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl'
    ]
    
    # Suspicious patterns in filenames
    SUSPICIOUS_PATTERNS = [
        r'\.\.',  # Directory traversal (any .. pattern)
        r'[<>:"|?*]',  # Invalid filename characters
        r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)',  # Windows reserved names
        r'^\.',  # Hidden files (Unix)
    ]
    
    @classmethod
    def validate_file(cls, uploaded_file, file_type: str = 'pdf') -> Dict[str, Any]:
        """
        Comprehensive file validation including security checks.
        
        Args:
            uploaded_file: Django UploadedFile object
            file_type: Expected file type ('pdf', 'docx', 'doc', 'txt', 'image')
            
        Returns:
            Dict with validation results and security analysis
        """
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'file_info': {},
            'security_checks': {}
        }
        
        try:
            # Basic file information
            file_info = cls._extract_file_info(uploaded_file)
            validation_result['file_info'] = file_info
            
            # Security checks
            security_checks = cls._perform_security_checks(uploaded_file, file_type)
            validation_result['security_checks'] = security_checks
            
            # Validate file type and content
            type_validation = cls._validate_file_type(uploaded_file, file_type)
            
            # Combine all validation results
            all_errors = security_checks.get('errors', []) + type_validation.get('errors', [])
            all_warnings = security_checks.get('warnings', []) + type_validation.get('warnings', [])
            
            validation_result['errors'] = all_errors
            validation_result['warnings'] = all_warnings
            validation_result['is_valid'] = len(all_errors) == 0
            
            # Log validation results
            if validation_result['is_valid']:
                logger.info(f"File validation passed: {file_info['original_name']}")
            else:
                logger.warning(f"File validation failed: {file_info['original_name']}, errors: {all_errors}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error during file validation: {str(e)}")
            validation_result['errors'].append(f"Validation error: {str(e)}")
            return validation_result
    
    @classmethod
    def _extract_file_info(cls, uploaded_file) -> Dict[str, Any]:
        """Extract basic file information"""
        return {
            'original_name': uploaded_file.name,
            'size': uploaded_file.size,
            'content_type': uploaded_file.content_type,
            'extension': Path(uploaded_file.name).suffix.lower(),
            'name_without_ext': Path(uploaded_file.name).stem,
            'upload_timestamp': timezone.now().isoformat()
        }
    
    @classmethod
    def _perform_security_checks(cls, uploaded_file, file_type: str) -> Dict[str, Any]:
        """Perform comprehensive security checks"""
        security_result = {
            'errors': [],
            'warnings': [],
            'checks_performed': []
        }
        
        # Check 1: Filename security
        filename_check = cls._check_filename_security(uploaded_file.name)
        security_result['checks_performed'].append('filename_security')
        
        if not filename_check['is_safe']:
            security_result['errors'].extend(filename_check['errors'])
        
        # Check 2: File size validation
        size_check = cls._check_file_size(uploaded_file, file_type)
        security_result['checks_performed'].append('file_size')
        if not size_check['is_valid']:
            security_result['errors'].extend(size_check['errors'])
        
        # Check 3: Magic bytes validation
        magic_check = cls._check_magic_bytes(uploaded_file, file_type)
        security_result['checks_performed'].append('magic_bytes')
        if not magic_check['is_valid']:
            security_result['errors'].extend(magic_check['errors'])
        
        # Check 4: Content scanning
        content_check = cls._scan_file_content(uploaded_file)
        security_result['checks_performed'].append('content_scan')
        if not content_check['is_safe']:
            security_result['errors'].extend(content_check['errors'])
            security_result['warnings'].extend(content_check['warnings'])
        
        return security_result
    
    @classmethod
    def _check_filename_security(cls, filename: str) -> Dict[str, Any]:
        """Check filename for security issues"""
        import re
        
        result = {
            'is_safe': True,
            'errors': []
        }
        

        
        # Check for dangerous extensions
        file_ext = Path(filename).suffix.lower()
        if file_ext in cls.DANGEROUS_EXTENSIONS:
            result['is_safe'] = False
            result['errors'].append(f"Dangerous file extension: {file_ext}")
        
        # Check for suspicious patterns in the full filename (including path)
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                result['is_safe'] = False
                result['errors'].append(f"Suspicious filename pattern detected: {pattern}")
        
        # Additional check for directory traversal patterns
        if '..' in filename or '/' in filename or '\\' in filename:
            result['is_safe'] = False
            result['errors'].append("Directory traversal or path characters detected in filename")
        
        # Check filename length
        if len(filename) > 255:
            result['is_safe'] = False
            result['errors'].append("Filename too long (max 255 characters)")
        
        # Check for null bytes
        if '\x00' in filename:
            result['is_safe'] = False
            result['errors'].append("Null bytes detected in filename")
        
        return result
    
    @classmethod
    def _check_file_size(cls, uploaded_file, file_type: str) -> Dict[str, Any]:
        """Validate file size against limits"""
        result = {
            'is_valid': True,
            'errors': []
        }
        
        if file_type not in cls.ALLOWED_FILE_TYPES:
            result['is_valid'] = False
            result['errors'].append(f"Unknown file type: {file_type}")
            return result
        
        max_size = cls.ALLOWED_FILE_TYPES[file_type]['max_size']
        
        if uploaded_file.size > max_size:
            result['is_valid'] = False
            result['errors'].append(
                f"File size ({uploaded_file.size} bytes) exceeds maximum "
                f"allowed size ({max_size} bytes) for {file_type} files"
            )
        
        if uploaded_file.size == 0:
            result['is_valid'] = False
            result['errors'].append("File is empty")
        
        return result
    
    @classmethod
    def _check_magic_bytes(cls, uploaded_file, file_type: str) -> Dict[str, Any]:
        """Validate file content using magic bytes"""
        result = {
            'is_valid': True,
            'errors': []
        }
        
        if file_type not in cls.ALLOWED_FILE_TYPES:
            result['is_valid'] = False
            result['errors'].append(f"Unknown file type: {file_type}")
            return result
        
        try:
            # Read first 512 bytes for magic byte checking
            uploaded_file.seek(0)
            file_header = uploaded_file.read(512)
            uploaded_file.seek(0)
            
            magic_bytes_list = cls.ALLOWED_FILE_TYPES[file_type]['magic_bytes']
            
            # Skip magic byte check for text files
            if not magic_bytes_list and file_type == 'txt':
                return result
            
            # Check if file starts with any of the expected magic bytes
            magic_match = False
            for magic_bytes in magic_bytes_list:
                if file_header.startswith(magic_bytes):
                    magic_match = True
                    break
            
            if not magic_match and magic_bytes_list:
                result['is_valid'] = False
                result['errors'].append(
                    f"File content doesn't match expected {file_type} format "
                    "(magic bytes mismatch)"
                )
        
        except Exception as e:
            logger.error(f"Error checking magic bytes: {str(e)}")
            result['is_valid'] = False
            result['errors'].append(f"Error validating file content: {str(e)}")
        
        return result
    
    @classmethod
    def _validate_file_type(cls, uploaded_file, file_type: str) -> Dict[str, Any]:
        """Validate file type against allowed types"""
        result = {
            'errors': [],
            'warnings': []
        }
        
        if file_type not in cls.ALLOWED_FILE_TYPES:
            result['errors'].append(f"File type '{file_type}' is not supported")
            return result
        
        file_config = cls.ALLOWED_FILE_TYPES[file_type]
        file_ext = Path(uploaded_file.name).suffix.lower()
        
        # Check extension
        if file_ext not in file_config['extensions']:
            result['errors'].append(
                f"File extension '{file_ext}' not allowed for {file_type} files. "
                f"Allowed extensions: {', '.join(file_config['extensions'])}"
            )
        
        # Check MIME type
        if uploaded_file.content_type not in file_config['mime_types']:
            result['warnings'].append(
                f"MIME type '{uploaded_file.content_type}' doesn't match expected "
                f"types for {file_type}: {', '.join(file_config['mime_types'])}"
            )
        
        return result
    
    @classmethod
    def _scan_file_content(cls, uploaded_file) -> Dict[str, Any]:
        """Scan file content for malicious patterns"""
        result = {
            'is_safe': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Read file content for scanning
            uploaded_file.seek(0)
            content = uploaded_file.read(1024 * 1024)  # Read first 1MB
            uploaded_file.seek(0)
            
            # Check for embedded executables or scripts
            suspicious_patterns = [
                b'<script',  # JavaScript
                b'<?php',    # PHP
                b'<%',       # ASP
                b'MZ',       # PE executable header
                b'\x7fELF',  # ELF executable header
            ]
            
            for pattern in suspicious_patterns:
                if pattern in content:
                    result['is_safe'] = False
                    result['errors'].append(f"Suspicious content pattern detected: {pattern.decode('utf-8', errors='ignore')}")
            
            # Check for excessive null bytes (potential binary content in text files)
            null_byte_count = content.count(b'\x00')
            if null_byte_count > 10:  # Allow some null bytes but not excessive
                result['warnings'].append(f"High number of null bytes detected: {null_byte_count}")
        
        except Exception as e:
            logger.error(f"Error scanning file content: {str(e)}")
            result['warnings'].append(f"Content scanning error: {str(e)}")
        
        return result


class SecureFileStorage:
    """
    Secure file storage manager with access control and cleanup utilities.
    """
    
    def __init__(self):
        self.storage = default_storage
        self.base_path = getattr(settings, 'MEDIA_ROOT', '/tmp')
    
    def store_file(self, uploaded_file, user, file_type: str = 'resume') -> Dict[str, Any]:
        """
        Securely store uploaded file with proper permissions and organization.
        
        Args:
            uploaded_file: Django UploadedFile object
            user: User object who owns the file
            file_type: Type of file being stored
            
        Returns:
            Dict with storage information
        """
        try:
            # Generate secure filename
            secure_filename = self._generate_secure_filename(uploaded_file.name, user.id)
            
            # Create user-specific directory path
            file_path = self._get_user_file_path(user, file_type, secure_filename)
            
            # Ensure directory exists with proper permissions
            self._ensure_directory_exists(os.path.dirname(file_path))
            
            # Store file
            stored_path = self.storage.save(file_path, uploaded_file)
            
            # Set file permissions
            self._set_file_permissions(stored_path)
            
            # Generate file hash for integrity checking
            file_hash = self._calculate_file_hash(stored_path)
            
            storage_info = {
                'success': True,
                'stored_path': stored_path,
                'secure_filename': secure_filename,
                'original_filename': uploaded_file.name,
                'file_size': uploaded_file.size,
                'file_hash': file_hash,
                'storage_timestamp': timezone.now().isoformat(),
                'user_id': str(user.id)
            }
            
            logger.info(f"File stored successfully: {stored_path} for user {user.username}")
            return storage_info
            
        except Exception as e:
            logger.error(f"Error storing file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_secure_filename(self, original_filename: str, user_id) -> str:
        """Generate a secure filename to prevent conflicts and attacks"""
        # Extract extension
        file_ext = Path(original_filename).suffix.lower()
        
        # Create secure base name
        timestamp = int(timezone.now().timestamp())
        unique_id = str(uuid.uuid4())[:8]
        user_hash = hashlib.md5(str(user_id).encode()).hexdigest()[:8]
        
        secure_name = f"{user_hash}_{timestamp}_{unique_id}{file_ext}"
        
        return secure_name
    
    def _get_user_file_path(self, user, file_type: str, filename: str) -> str:
        """Generate user-specific file path"""
        # Create path: file_type/user_id_hash/year/month/filename
        user_hash = hashlib.md5(str(user.id).encode()).hexdigest()[:16]
        now = timezone.now()
        
        path = os.path.join(
            file_type,
            user_hash,
            str(now.year),
            f"{now.month:02d}",
            filename
        )
        
        return path
    
    def _ensure_directory_exists(self, directory_path: str):
        """Ensure directory exists with proper permissions"""
        full_path = os.path.join(self.base_path, directory_path)
        os.makedirs(full_path, mode=0o755, exist_ok=True)
    
    def _set_file_permissions(self, file_path: str):
        """Set secure file permissions"""
        try:
            full_path = os.path.join(self.base_path, file_path)
            if os.path.exists(full_path):
                os.chmod(full_path, 0o644)  # Read/write for owner, read for group/others
        except Exception as e:
            logger.warning(f"Could not set file permissions for {file_path}: {str(e)}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of stored file for integrity checking"""
        try:
            full_path = os.path.join(self.base_path, file_path)
            hash_sha256 = hashlib.sha256()
            
            with open(full_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {str(e)}")
            return ""
    
    def delete_file(self, file_path: str) -> bool:
        """Securely delete a file"""
        try:
            if self.storage.exists(file_path):
                self.storage.delete(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def cleanup_old_files(self, days_old: int = 30, file_type: str = None) -> Dict[str, Any]:
        """
        Clean up old files based on age.
        
        Args:
            days_old: Files older than this many days will be deleted
            file_type: Optional file type filter
            
        Returns:
            Dict with cleanup statistics
        """
        cleanup_stats = {
            'files_scanned': 0,
            'files_deleted': 0,
            'space_freed': 0,
            'errors': []
        }
        
        try:
            cutoff_date = timezone.now() - timedelta(days=days_old)
            
            # Scan for old files
            base_scan_path = file_type if file_type else ''
            scan_path = os.path.join(self.base_path, base_scan_path)
            
            if not os.path.exists(scan_path):
                return cleanup_stats
            
            for root, dirs, files in os.walk(scan_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    cleanup_stats['files_scanned'] += 1
                    
                    try:
                        # Check file modification time
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        file_mtime = timezone.make_aware(file_mtime)
                        
                        if file_mtime < cutoff_date:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleanup_stats['files_deleted'] += 1
                            cleanup_stats['space_freed'] += file_size
                            logger.info(f"Cleaned up old file: {file_path}")
                    
                    except Exception as e:
                        error_msg = f"Error processing file {file_path}: {str(e)}"
                        cleanup_stats['errors'].append(error_msg)
                        logger.error(error_msg)
            
            logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            error_msg = f"Error during cleanup: {str(e)}"
            cleanup_stats['errors'].append(error_msg)
            logger.error(error_msg)
            return cleanup_stats


class FileAccessController:
    """
    File access control manager for secure file serving.
    """
    
    @staticmethod
    def can_access_file(user, file_path: str, file_owner_id: str) -> Tuple[bool, str]:
        """
        Check if user can access a specific file.
        
        Args:
            user: User requesting access
            file_path: Path to the file
            file_owner_id: ID of the file owner
            
        Returns:
            Tuple of (can_access: bool, reason: str)
        """
        # Anonymous users cannot access files
        if not user or not user.is_authenticated:
            return False, "Authentication required"
        
        # Users can access their own files
        if str(user.id) == str(file_owner_id):
            return True, "Owner access"
        
        # Admins can access all files
        if user.is_staff or user.is_superuser:
            return True, "Admin access"
        
        # Recruiters can access resumes of applicants
        if user.user_type == 'recruiter':
            # Check if this is a resume file and user has applied to recruiter's jobs
            if 'resume' in file_path.lower():
                from .models import Application, Resume
                try:
                    # Find resume by file path (this is a simplified check)
                    # In production, you'd want a more robust way to link file paths to resume records
                    resumes = Resume.objects.filter(job_seeker_id=file_owner_id)
                    for resume in resumes:
                        if Application.objects.filter(
                            resume=resume,
                            job_post__recruiter=user
                        ).exists():
                            return True, "Recruiter access to applicant resume"
                except Exception as e:
                    logger.error(f"Error checking recruiter access: {str(e)}")
        
        return False, "Access denied"
    
    @staticmethod
    def get_secure_file_url(file_path: str, user_id: str, expires_in: int = 3600) -> str:
        """
        Generate a secure, time-limited URL for file access.
        
        Args:
            file_path: Path to the file
            user_id: ID of the user requesting access
            expires_in: URL expiration time in seconds
            
        Returns:
            Secure URL string
        """
        import hmac
        
        # Create expiration timestamp
        expires_at = int(timezone.now().timestamp()) + expires_in
        
        # Create signature
        secret_key = getattr(settings, 'SECRET_KEY', 'default-key')
        message = f"{file_path}:{user_id}:{expires_at}"
        signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Generate secure URL
        secure_url = f"/api/files/secure/{file_path}?expires={expires_at}&signature={signature}&user={user_id}"
        
        return secure_url
    
    @staticmethod
    def verify_secure_url(file_path: str, user_id: str, expires_at: int, signature: str) -> Tuple[bool, str]:
        """
        Verify a secure file URL.
        
        Returns:
            Tuple of (is_valid: bool, reason: str)
        """
        import hmac
        
        try:
            # Check expiration
            current_time = int(timezone.now().timestamp())
            if current_time > expires_at:
                return False, "URL expired"
            
            # Verify signature
            secret_key = getattr(settings, 'SECRET_KEY', 'default-key')
            message = f"{file_path}:{user_id}:{expires_at}"
            expected_signature = hmac.new(
                secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return False, "Invalid signature"
            
            return True, "Valid URL"
            
        except Exception as e:
            logger.error(f"Error verifying secure URL: {str(e)}")
            return False, f"Verification error: {str(e)}"