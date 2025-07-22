"""
Comprehensive tests for secure file upload system.
Tests file validation, security checks, storage, and access control.
"""

import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import BytesIO

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .file_utils import FileSecurityValidator, SecureFileStorage, FileAccessController
from .models import Resume

User = get_user_model()


class FileSecurityValidatorTests(TestCase):
    """Test file security validation functionality"""
    
    def setUp(self):
        self.validator = FileSecurityValidator()
    
    def create_test_file(self, content: bytes, filename: str, content_type: str = 'application/pdf'):
        """Helper to create test files"""
        return SimpleUploadedFile(
            filename,
            content,
            content_type=content_type
        )
    
    def test_valid_pdf_file(self):
        """Test validation of a valid PDF file"""
        # Create a mock PDF file with proper magic bytes
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF'
        test_file = self.create_test_file(pdf_content, 'test_resume.pdf', 'application/pdf')
        
        result = FileSecurityValidator.validate_file(test_file, 'pdf')
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(result['file_info']['extension'], '.pdf')
    
    def test_invalid_file_extension(self):
        """Test rejection of dangerous file extensions"""
        malicious_content = b'malicious content'
        test_file = self.create_test_file(malicious_content, 'malware.exe', 'application/octet-stream')
        
        result = FileSecurityValidator.validate_file(test_file, 'pdf')
        
        self.assertFalse(result['is_valid'])
        self.assertIn('Dangerous file extension', str(result['errors']))
    
    def test_file_size_validation(self):
        """Test file size limits"""
        # Create a file that's too large (11MB for PDF which has 10MB limit)
        large_content = b'x' * (11 * 1024 * 1024)
        test_file = self.create_test_file(large_content, 'large_file.pdf', 'application/pdf')
        
        result = FileSecurityValidator.validate_file(test_file, 'pdf')
        
        self.assertFalse(result['is_valid'])
        self.assertIn('exceeds maximum allowed size', str(result['errors']))
    
    def test_empty_file_rejection(self):
        """Test rejection of empty files"""
        empty_file = self.create_test_file(b'', 'empty.pdf', 'application/pdf')
        
        result = FileSecurityValidator.validate_file(empty_file, 'pdf')
        
        self.assertFalse(result['is_valid'])
        self.assertIn('empty', str(result['errors']).lower())
    
    def test_suspicious_filename_patterns(self):
        """Test detection of suspicious filename patterns"""
        # Note: Django's SimpleUploadedFile automatically sanitizes filenames,
        # so directory traversal patterns like '../../../etc/passwd.pdf' become 'passwd.pdf'
        # We test the patterns that would actually reach our validator
        suspicious_files = [
            'file<script>.pdf',         # HTML injection
            'CON.pdf',                  # Windows reserved name
            '.hidden.pdf',              # Hidden file
        ]
        
        for filename in suspicious_files:
            with self.subTest(filename=filename):
                test_file = self.create_test_file(b'%PDF-1.4', filename, 'application/pdf')
                result = FileSecurityValidator.validate_file(test_file, 'pdf')
                
                self.assertFalse(result['is_valid'], f"File '{filename}' should be invalid but was marked as valid")
                self.assertTrue(len(result['errors']) > 0)
    
    def test_directory_traversal_detection_direct(self):
        """Test directory traversal detection by calling the security check directly"""
        # Test the filename security check directly to verify it works
        from matcher.file_utils import FileSecurityValidator
        
        dangerous_filenames = [
            '../../../etc/passwd.pdf',
            '..\\..\\windows\\system32\\config\\sam',
            'normal/../../../etc/passwd.pdf',
            'file/with/path.pdf',
            'file\\with\\backslash.pdf'
        ]
        
        for filename in dangerous_filenames:
            with self.subTest(filename=filename):
                result = FileSecurityValidator._check_filename_security(filename)
                self.assertFalse(result['is_safe'], f"Filename '{filename}' should be detected as unsafe")
                self.assertTrue(len(result['errors']) > 0)
    
    def test_magic_bytes_validation(self):
        """Test magic bytes validation for different file types"""
        # Test PDF with wrong magic bytes
        fake_pdf = self.create_test_file(b'Not a PDF file', 'fake.pdf', 'application/pdf')
        result = FileSecurityValidator.validate_file(fake_pdf, 'pdf')
        
        self.assertFalse(result['is_valid'])
        self.assertIn('magic bytes mismatch', str(result['errors']))
    
    def test_malicious_content_detection(self):
        """Test detection of malicious content patterns"""
        malicious_patterns = [
            b'<script>alert("xss")</script>',  # JavaScript
            b'<?php system($_GET["cmd"]); ?>',  # PHP
            b'MZ\x90\x00',                     # PE executable header
        ]
        
        for pattern in malicious_patterns:
            with self.subTest(pattern=pattern):
                test_file = self.create_test_file(pattern, 'malicious.pdf', 'application/pdf')
                result = FileSecurityValidator.validate_file(test_file, 'pdf')
                
                self.assertFalse(result['is_valid'])
                self.assertTrue(len(result['errors']) > 0)
    
    def test_docx_file_validation(self):
        """Test DOCX file validation"""
        # DOCX files are ZIP-based, so they start with PK
        docx_content = b'PK\x03\x04' + b'x' * 100  # Mock DOCX content
        test_file = self.create_test_file(
            docx_content, 
            'resume.docx', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        result = FileSecurityValidator.validate_file(test_file, 'docx')
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['file_info']['extension'], '.docx')
    
    def test_text_file_validation(self):
        """Test text file validation"""
        text_content = b'This is a plain text resume.\nName: John Doe\nSkills: Python, Django'
        test_file = self.create_test_file(text_content, 'resume.txt', 'text/plain')
        
        result = FileSecurityValidator.validate_file(test_file, 'txt')
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['file_info']['extension'], '.txt')


class SecureFileStorageTests(TestCase):
    """Test secure file storage functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        self.storage = SecureFileStorage()
    
    def create_test_file(self, content: bytes = b'test content', filename: str = 'test.pdf'):
        """Helper to create test files"""
        return SimpleUploadedFile(filename, content, content_type='application/pdf')
    
    @override_settings(MEDIA_ROOT='/tmp/test_media')
    def test_secure_file_storage(self):
        """Test secure file storage with proper organization"""
        test_file = self.create_test_file(b'PDF content', 'resume.pdf')
        
        result = self.storage.store_file(test_file, self.user, 'resume')
        
        self.assertTrue(result['success'])
        self.assertIn('stored_path', result)
        self.assertIn('file_hash', result)
        self.assertEqual(result['original_filename'], 'resume.pdf')
        self.assertEqual(result['file_size'], len(b'PDF content'))
    
    def test_secure_filename_generation(self):
        """Test generation of secure filenames"""
        original_filename = 'my resume with spaces.pdf'
        secure_filename = self.storage._generate_secure_filename(original_filename, self.user.id)
        
        # Should contain user hash, timestamp, and unique ID
        self.assertTrue(secure_filename.endswith('.pdf'))
        self.assertNotIn(' ', secure_filename)  # No spaces
        self.assertNotIn('resume', secure_filename.lower())  # Original name obscured
    
    def test_user_specific_path_generation(self):
        """Test generation of user-specific file paths"""
        filename = 'secure_file.pdf'
        file_path = self.storage._get_user_file_path(self.user, 'resume', filename)
        
        # Should include file type, user hash, and date structure
        self.assertIn('resume', file_path)
        self.assertTrue(file_path.endswith(filename))
        # Should include year and month
        now = timezone.now()
        self.assertIn(str(now.year), file_path)
        self.assertIn(f"{now.month:02d}", file_path)
    
    def test_file_hash_calculation(self):
        """Test file integrity hash calculation"""
        test_content = b'test file content for hashing'
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file.flush()
            
            # Calculate hash using storage method
            calculated_hash = self.storage._calculate_file_hash(temp_file.name)
            
            # Clean up
            os.unlink(temp_file.name)
        
        self.assertEqual(calculated_hash, expected_hash)
    
    @override_settings(MEDIA_ROOT='/tmp/test_media')
    def test_file_deletion(self):
        """Test secure file deletion"""
        test_file = self.create_test_file(b'content to delete', 'delete_me.pdf')
        
        # Store file first
        store_result = self.storage.store_file(test_file, self.user, 'resume')
        self.assertTrue(store_result['success'])
        
        # Delete file
        delete_result = self.storage.delete_file(store_result['stored_path'])
        self.assertTrue(delete_result)
    
    @override_settings(MEDIA_ROOT='/tmp/test_media')
    def test_cleanup_old_files(self):
        """Test cleanup of old files"""
        # This test would require creating actual old files
        # For now, test that the method runs without error
        cleanup_stats = self.storage.cleanup_old_files(days_old=30)
        
        self.assertIn('files_scanned', cleanup_stats)
        self.assertIn('files_deleted', cleanup_stats)
        self.assertIn('space_freed', cleanup_stats)
        self.assertIsInstance(cleanup_stats['errors'], list)


class FileAccessControllerTests(TestCase):
    """Test file access control functionality"""
    
    def setUp(self):
        self.job_seeker = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@example.com',
            password='testpass123',
            user_type='recruiter'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
    
    def test_owner_file_access(self):
        """Test that users can access their own files"""
        file_path = 'resume/user123/2024/01/resume.pdf'
        
        can_access, reason = FileAccessController.can_access_file(
            self.job_seeker, file_path, str(self.job_seeker.id)
        )
        
        self.assertTrue(can_access)
        self.assertEqual(reason, "Owner access")
    
    def test_admin_file_access(self):
        """Test that admins can access all files"""
        file_path = 'resume/user123/2024/01/resume.pdf'
        
        can_access, reason = FileAccessController.can_access_file(
            self.admin, file_path, str(self.job_seeker.id)
        )
        
        self.assertTrue(can_access)
        self.assertEqual(reason, "Admin access")
    
    def test_unauthorized_file_access(self):
        """Test that unauthorized users cannot access files"""
        file_path = 'resume/user123/2024/01/resume.pdf'
        
        can_access, reason = FileAccessController.can_access_file(
            self.recruiter, file_path, str(self.job_seeker.id)
        )
        
        self.assertFalse(can_access)
        self.assertEqual(reason, "Access denied")
    
    def test_anonymous_user_access(self):
        """Test that anonymous users cannot access files"""
        file_path = 'resume/user123/2024/01/resume.pdf'
        
        can_access, reason = FileAccessController.can_access_file(
            None, file_path, str(self.job_seeker.id)
        )
        
        self.assertFalse(can_access)
        self.assertEqual(reason, "Authentication required")
    
    def test_secure_url_generation(self):
        """Test generation of secure file URLs"""
        file_path = 'resume/test.pdf'
        user_id = str(self.job_seeker.id)
        
        secure_url = FileAccessController.get_secure_file_url(file_path, user_id)
        
        self.assertIn('/api/files/secure/', secure_url)
        self.assertIn('expires=', secure_url)
        self.assertIn('signature=', secure_url)
        self.assertIn('user=', secure_url)
    
    def test_secure_url_verification(self):
        """Test verification of secure file URLs"""
        file_path = 'resume/test.pdf'
        user_id = str(self.job_seeker.id)
        
        # Generate URL
        secure_url = FileAccessController.get_secure_file_url(file_path, user_id, expires_in=3600)
        
        # Extract parameters
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(secure_url)
        params = parse_qs(parsed_url.query)
        
        expires_at = int(params['expires'][0])
        signature = params['signature'][0]
        
        # Verify URL
        is_valid, reason = FileAccessController.verify_secure_url(
            file_path, user_id, expires_at, signature
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(reason, "Valid URL")
    
    def test_expired_url_verification(self):
        """Test verification of expired URLs"""
        file_path = 'resume/test.pdf'
        user_id = str(self.job_seeker.id)
        expired_timestamp = int(timezone.now().timestamp()) - 3600  # 1 hour ago
        
        # Create signature for expired URL
        import hmac
        secret_key = getattr(settings, 'SECRET_KEY', 'default-key')
        message = f"{file_path}:{user_id}:{expired_timestamp}"
        signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        is_valid, reason = FileAccessController.verify_secure_url(
            file_path, user_id, expired_timestamp, signature
        )
        
        self.assertFalse(is_valid)
        self.assertEqual(reason, "URL expired")


class SecureFileUploadAPITests(APITestCase):
    """Test secure file upload API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.job_seeker = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@example.com',
            password='testpass123',
            user_type='recruiter'
        )
        
        # Get JWT tokens
        refresh = RefreshToken.for_user(self.job_seeker)
        self.job_seeker_token = str(refresh.access_token)
        
        refresh = RefreshToken.for_user(self.recruiter)
        self.recruiter_token = str(refresh.access_token)
    
    def create_test_file(self, content: bytes = b'%PDF-1.4\ntest content', filename: str = 'test.pdf'):
        """Helper to create test files"""
        return SimpleUploadedFile(filename, content, content_type='application/pdf')
    
    def test_secure_file_upload_success(self):
        """Test successful secure file upload"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        test_file = self.create_test_file(b'%PDF-1.4\nValid PDF content', 'resume.pdf')
        
        response = self.client.post('/api/files/upload/', {
            'file': test_file,
            'file_type': 'pdf'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('file_info', response.data)
        self.assertIn('security_info', response.data)
        self.assertIn('access_info', response.data)
    
    def test_file_upload_without_authentication(self):
        """Test file upload without authentication"""
        test_file = self.create_test_file()
        
        response = self.client.post('/api/files/upload/', {
            'file': test_file,
            'file_type': 'pdf'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_file_upload_validation_failure(self):
        """Test file upload with validation failure"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Upload malicious file
        malicious_file = SimpleUploadedFile(
            'malware.exe',
            b'malicious content',
            content_type='application/octet-stream'
        )
        
        response = self.client.post('/api/files/upload/', {
            'file': malicious_file,
            'file_type': 'pdf'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('validation failed', response.data['error'])
    
    def test_resume_upload_endpoint(self):
        """Test specialized resume upload endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        test_file = self.create_test_file(b'%PDF-1.4\nResume content', 'my_resume.pdf')
        
        response = self.client.post('/api/files/upload-resume/', {
            'file': test_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('resume_id', response.data)
        
        # Verify Resume object was created
        resume_id = response.data['resume_id']
        resume = Resume.objects.get(id=resume_id)
        self.assertEqual(resume.job_seeker, self.job_seeker)
        self.assertEqual(resume.original_filename, 'my_resume.pdf')
    
    def test_resume_upload_by_recruiter_forbidden(self):
        """Test that recruiters cannot upload resumes"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.recruiter_token}')
        
        test_file = self.create_test_file()
        
        response = self.client.post('/api/files/upload-resume/', {
            'file': test_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_user_files(self):
        """Test listing user's files"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # First upload a resume
        test_file = self.create_test_file(b'%PDF-1.4\nResume content', 'resume.pdf')
        upload_response = self.client.post('/api/files/upload-resume/', {
            'file': test_file
        }, format='multipart')
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        
        # List files
        response = self.client.get('/api/files/list/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['total_count'], 1)
        self.assertEqual(len(response.data['files']), 1)
        
        file_info = response.data['files'][0]
        self.assertEqual(file_info['type'], 'resume')
        self.assertEqual(file_info['original_filename'], 'resume.pdf')
        self.assertIn('secure_url', file_info)
    
    def test_file_deletion(self):
        """Test file deletion"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Upload a resume first
        test_file = self.create_test_file(b'%PDF-1.4\nResume to delete', 'delete_me.pdf')
        upload_response = self.client.post('/api/files/upload-resume/', {
            'file': test_file
        }, format='multipart')
        resume_id = upload_response.data['resume_id']
        
        # Delete the file
        response = self.client.delete(f'/api/files/delete/{resume_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify file is deleted from database
        with self.assertRaises(Resume.DoesNotExist):
            Resume.objects.get(id=resume_id)
    
    def test_unauthorized_file_deletion(self):
        """Test that users cannot delete other users' files"""
        # Upload file as job seeker
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        test_file = self.create_test_file(b'%PDF-1.4\nProtected resume', 'protected.pdf')
        upload_response = self.client.post('/api/files/upload-resume/', {
            'file': test_file
        }, format='multipart')
        resume_id = upload_response.data['resume_id']
        
        # Try to delete as recruiter
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.recruiter_token}')
        response = self.client.delete(f'/api/files/delete/{resume_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify file still exists
        resume = Resume.objects.get(id=resume_id)
        self.assertEqual(resume.job_seeker, self.job_seeker)
    
    def test_file_validation_info_endpoint(self):
        """Test file validation information endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        response = self.client.get('/api/files/validation-info/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('allowed_file_types', response.data)
        self.assertIn('security_checks', response.data)
        self.assertIn('max_file_sizes', response.data)
        self.assertIn('supported_extensions', response.data)
        
        # Check that PDF info is included
        self.assertIn('pdf', response.data['allowed_file_types'])
        pdf_info = response.data['allowed_file_types']['pdf']
        self.assertIn('extensions', pdf_info)
        self.assertIn('max_size_mb', pdf_info)
    
    @patch('matcher.file_views.default_storage')
    def test_secure_file_serving(self, mock_storage):
        """Test secure file serving with access control"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Mock file existence and content
        mock_storage.exists.return_value = True
        mock_storage.size.return_value = 1024
        mock_file = MagicMock()
        mock_file.read.return_value = b'%PDF-1.4\nfile content'
        mock_storage.open.return_value = mock_file
        
        # Generate secure URL
        file_path = 'resume/test.pdf'
        secure_url = FileAccessController.get_secure_file_url(
            file_path, str(self.job_seeker.id)
        )
        
        # Extract URL path and parameters
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(secure_url)
        params = parse_qs(parsed_url.query)
        
        # Make request to secure file endpoint
        response = self.client.get(
            f'/api/files/secure/{file_path}/',
            {
                'expires': params['expires'][0],
                'signature': params['signature'][0],
                'user': params['user'][0]
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)


class FileUploadIntegrationTests(APITestCase):
    """Integration tests for complete file upload workflows"""
    
    def setUp(self):
        self.client = APIClient()
        self.job_seeker = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        refresh = RefreshToken.for_user(self.job_seeker)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_complete_resume_upload_workflow(self):
        """Test complete workflow: upload -> list -> access -> delete"""
        # Step 1: Upload resume
        test_file = SimpleUploadedFile(
            'complete_test_resume.pdf',
            b'%PDF-1.4\nComplete test resume content',
            content_type='application/pdf'
        )
        
        upload_response = self.client.post('/api/files/upload-resume/', {
            'file': test_file
        }, format='multipart')
        
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        resume_id = upload_response.data['resume_id']
        
        # Step 2: List files to verify upload
        list_response = self.client.get('/api/files/list/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data['total_count'], 1)
        
        # Step 3: Verify file info
        file_info = list_response.data['files'][0]
        self.assertEqual(file_info['id'], resume_id)
        self.assertEqual(file_info['original_filename'], 'complete_test_resume.pdf')
        self.assertIn('secure_url', file_info)
        
        # Step 4: Delete file
        delete_response = self.client.delete(f'/api/files/delete/{resume_id}/')
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        
        # Step 5: Verify file is deleted
        final_list_response = self.client.get('/api/files/list/')
        self.assertEqual(final_list_response.data['total_count'], 0)
    
    def test_multiple_file_upload_and_management(self):
        """Test uploading and managing multiple files"""
        file_names = ['resume1.pdf', 'resume2.pdf', 'resume3.pdf']
        uploaded_ids = []
        
        # Upload multiple files
        for filename in file_names:
            test_file = SimpleUploadedFile(
                filename,
                b'%PDF-1.4\nResume content for ' + filename.encode(),
                content_type='application/pdf'
            )
            
            response = self.client.post('/api/files/upload-resume/', {
                'file': test_file
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            uploaded_ids.append(response.data['resume_id'])
        
        # Verify all files are listed
        list_response = self.client.get('/api/files/list/')
        self.assertEqual(list_response.data['total_count'], 3)
        
        # Delete one file
        delete_response = self.client.delete(f'/api/files/delete/{uploaded_ids[1]}/')
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        
        # Verify count decreased
        final_list_response = self.client.get('/api/files/list/')
        self.assertEqual(final_list_response.data['total_count'], 2)
        
        # Verify correct files remain
        remaining_files = final_list_response.data['files']
        remaining_names = [f['original_filename'] for f in remaining_files]
        self.assertIn('resume1.pdf', remaining_names)
        self.assertIn('resume3.pdf', remaining_names)
        self.assertNotIn('resume2.pdf', remaining_names)