"""
Tests for resume parsing functionality using Google Gemini API
"""

import os
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Resume, AIAnalysisResult, JobSeekerProfile
from .services import GeminiResumeParser, FileValidator, GeminiAPIError

User = get_user_model()


class GeminiResumeParserTestCase(TestCase):
    """Test cases for GeminiResumeParser service"""
    
    def setUp(self):
        self.sample_resume_text = """
        John Doe
        Software Engineer
        john.doe@email.com
        (555) 123-4567
        
        EXPERIENCE
        Senior Software Engineer at Tech Corp (2020-2023)
        - Developed web applications using Python and Django
        - Led a team of 5 developers
        - Implemented CI/CD pipelines
        
        EDUCATION
        Bachelor of Science in Computer Science
        University of Technology (2016-2020)
        
        SKILLS
        Python, Django, JavaScript, React, AWS, Docker
        """
        
        self.sample_structured_data = {
            "personal_info": {
                "name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "(555) 123-4567",
                "location": None,
                "linkedin": None,
                "github": None,
                "portfolio": None
            },
            "summary": "Experienced software engineer with expertise in Python and web development",
            "experience": [
                {
                    "company": "Tech Corp",
                    "position": "Senior Software Engineer",
                    "duration": "2020-2023",
                    "description": "Developed web applications using Python and Django",
                    "technologies": ["Python", "Django"]
                }
            ],
            "education": [
                {
                    "institution": "University of Technology",
                    "degree": "Bachelor of Science in Computer Science",
                    "duration": "2016-2020",
                    "gpa": None
                }
            ],
            "skills": {
                "technical_skills": ["Python", "Django", "JavaScript", "React"],
                "programming_languages": ["Python", "JavaScript"],
                "frameworks": ["Django", "React"],
                "tools": ["AWS", "Docker"],
                "soft_skills": ["Leadership", "Team Management"]
            },
            "certifications": [],
            "projects": [],
            "languages": [],
            "total_experience_years": 3,
            "confidence_score": 0.9
        }
    
    @override_settings(GEMINI_API_KEY='test-api-key')
    @patch('matcher.services.genai.configure')
    @patch('matcher.services.genai.GenerativeModel')
    def test_parser_initialization_success(self, mock_model, mock_configure):
        """Test successful parser initialization"""
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance
        
        parser = GeminiResumeParser()
        
        mock_configure.assert_called_once_with(api_key='test-api-key')
        mock_model.assert_called_once_with('gemini-pro')
        self.assertEqual(parser.model, mock_model_instance)
    
    @override_settings(GEMINI_API_KEY='')
    def test_parser_initialization_no_api_key(self):
        """Test parser initialization fails without API key"""
        with self.assertRaises(GeminiAPIError) as context:
            GeminiResumeParser()
        
        self.assertIn('GEMINI_API_KEY not configured', str(context.exception))
    
    @override_settings(GEMINI_API_KEY='test-api-key')
    @patch('matcher.services.genai.configure')
    @patch('matcher.services.genai.GenerativeModel')
    def test_parser_initialization_api_error(self, mock_model, mock_configure):
        """Test parser initialization fails with API error"""
        mock_configure.side_effect = Exception("API configuration failed")
        
        with self.assertRaises(GeminiAPIError) as context:
            GeminiResumeParser()
        
        self.assertIn('Failed to initialize Gemini model', str(context.exception))
    
    @override_settings(GEMINI_API_KEY='test-api-key')
    @patch('matcher.services.genai.configure')
    @patch('matcher.services.genai.GenerativeModel')
    def test_extract_text_from_pdf_bytes(self, mock_model, mock_configure):
        """Test PDF text extraction from bytes"""
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance
        
        parser = GeminiResumeParser()
        
        # Mock PDF content
        with patch('matcher.services.PyPDF2.PdfReader') as mock_pdf_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Sample PDF text"
            mock_reader_instance = MagicMock()
            mock_reader_instance.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader_instance
            
            result = parser._extract_text_from_pdf_bytes(b"fake pdf content")
            
            self.assertEqual(result, "Sample PDF text")
    
    @override_settings(GEMINI_API_KEY='test-api-key')
    @patch('matcher.services.genai.configure')
    @patch('matcher.services.genai.GenerativeModel')
    def test_extract_text_from_docx_bytes(self, mock_model, mock_configure):
        """Test DOCX text extraction from bytes"""
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance
        
        parser = GeminiResumeParser()
        
        # Mock DOCX content
        with patch('matcher.services.docx.Document') as mock_docx:
            mock_paragraph = MagicMock()
            mock_paragraph.text = "Sample DOCX text"
            mock_doc_instance = MagicMock()
            mock_doc_instance.paragraphs = [mock_paragraph]
            mock_docx.return_value = mock_doc_instance
            
            result = parser._extract_text_from_docx_bytes(b"fake docx content")
            
            self.assertEqual(result, "Sample DOCX text")
    
    @override_settings(GEMINI_API_KEY='test-api-key')
    @patch('matcher.services.genai.configure')
    @patch('matcher.services.genai.GenerativeModel')
    def test_generate_structured_data_success(self, mock_model, mock_configure):
        """Test successful structured data generation"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.sample_structured_data)
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        parser = GeminiResumeParser()
        result = parser._generate_structured_data(self.sample_resume_text)
        
        self.assertEqual(result['personal_info']['name'], 'John Doe')
        self.assertEqual(result['total_experience_years'], 3)
        self.assertEqual(result['confidence_score'], 0.9)
    
    @override_settings(GEMINI_API_KEY='test-api-key')
    @patch('matcher.services.genai.configure')
    @patch('matcher.services.genai.GenerativeModel')
    def test_generate_structured_data_invalid_json(self, mock_model, mock_configure):
        """Test structured data generation with invalid JSON response"""
        mock_response = MagicMock()
        mock_response.text = "Invalid JSON response"
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        parser = GeminiResumeParser()
        result = parser._generate_structured_data(self.sample_resume_text)
        
        # Should return fallback structure
        self.assertIn('personal_info', result)
        self.assertIn('skills', result)
        self.assertEqual(result['confidence_score'], 0.1)
    
    @override_settings(GEMINI_API_KEY='test-api-key')
    @patch('matcher.services.genai.configure')
    @patch('matcher.services.genai.GenerativeModel')
    def test_parse_resume_success(self, mock_model, mock_configure):
        """Test successful resume parsing"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.sample_structured_data)
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        parser = GeminiResumeParser()
        
        # Mock file content extraction
        with patch.object(parser, '_extract_text_from_file', return_value=self.sample_resume_text):
            result = parser.parse_resume('/fake/path/resume.pdf')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['parsed_text'], self.sample_resume_text)
        self.assertIn('structured_data', result)
        self.assertGreater(result['processing_time'], 0)
    
    @override_settings(GEMINI_API_KEY='test-api-key')
    @patch('matcher.services.genai.configure')
    @patch('matcher.services.genai.GenerativeModel')
    def test_parse_resume_empty_content(self, mock_model, mock_configure):
        """Test resume parsing with empty content"""
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance
        
        parser = GeminiResumeParser()
        
        # Mock empty file content extraction
        with patch.object(parser, '_extract_text_from_file', return_value=''):
            result = parser.parse_resume('/fake/path/resume.pdf')
        
        self.assertFalse(result['success'])
        self.assertIn('No text content could be extracted', result['error'])


class FileValidatorTestCase(TestCase):
    """Test cases for FileValidator service"""
    
    def test_validate_file_success(self):
        """Test successful file validation"""
        # Create a mock file
        file_content = b"Sample resume content"
        uploaded_file = SimpleUploadedFile(
            "resume.pdf",
            file_content,
            content_type="application/pdf"
        )
        
        result = FileValidator.validate_file(uploaded_file)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(result['file_extension'], '.pdf')
        self.assertEqual(result['file_size'], len(file_content))
    
    def test_validate_file_invalid_extension(self):
        """Test file validation with invalid extension"""
        uploaded_file = SimpleUploadedFile(
            "resume.exe",
            b"content",
            content_type="application/octet-stream"
        )
        
        result = FileValidator.validate_file(uploaded_file)
        
        self.assertFalse(result['is_valid'])
        self.assertTrue(any('not supported' in error for error in result['errors']))
    
    def test_validate_file_too_large(self):
        """Test file validation with file too large"""
        # Create a file larger than the limit
        large_content = b"x" * (FileValidator.MAX_FILE_SIZE + 1)
        uploaded_file = SimpleUploadedFile(
            "resume.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        result = FileValidator.validate_file(uploaded_file)
        
        self.assertFalse(result['is_valid'])
        self.assertTrue(any('exceeds maximum' in error for error in result['errors']))
    
    def test_validate_file_empty(self):
        """Test file validation with empty file"""
        uploaded_file = SimpleUploadedFile(
            "resume.pdf",
            b"",
            content_type="application/pdf"
        )
        
        result = FileValidator.validate_file(uploaded_file)
        
        self.assertFalse(result['is_valid'])
        self.assertTrue(any('empty' in error.lower() for error in result['errors']))
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        original_filename = "My Resume (2023) - Final!.pdf"
        sanitized = FileValidator.sanitize_filename(original_filename)
        
        self.assertTrue(sanitized.endswith('.pdf'))
        self.assertNotIn('(', sanitized)
        self.assertNotIn(')', sanitized)
        self.assertNotIn('!', sanitized)


class ResumeParsingAPITestCase(APITestCase):
    """Test cases for resume parsing API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test user
        self.job_seeker = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        
        # Create profiles
        JobSeekerProfile.objects.create(user=self.job_seeker)
        
        # Create test resume
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker,
            file='test_resume.pdf',
            original_filename='test_resume.pdf',
            file_size=1024
        )
        
        # Get JWT tokens
        self.job_seeker_token = str(RefreshToken.for_user(self.job_seeker).access_token)
        self.recruiter_token = str(RefreshToken.for_user(self.recruiter).access_token)
    
    def test_parse_resume_view_success(self):
        """Test successful resume parsing via API"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Create test file
        file_content = b"Sample resume content for testing"
        uploaded_file = SimpleUploadedFile(
            "test_resume.pdf",
            file_content,
            content_type="application/pdf"
        )
        
        with patch('matcher.views.GeminiResumeParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_resume.return_value = {
                'success': True,
                'parsed_text': 'Sample parsed text',
                'structured_data': {'name': 'John Doe'},
                'confidence_score': 0.8,
                'processing_time': 1.5
            }
            mock_parser_class.return_value = mock_parser
            
            response = self.client.post(
                reverse('parse-resume'),
                {'file': uploaded_file},
                format='multipart'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('parsed_text', response.data)
        self.assertIn('structured_data', response.data)
    
    def test_parse_resume_view_no_file(self):
        """Test resume parsing API without file"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        response = self.client.post(reverse('parse-resume'), {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No file provided', response.data['error'])
    
    def test_parse_resume_view_recruiter_forbidden(self):
        """Test resume parsing API forbidden for recruiters"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.recruiter_token}')
        
        uploaded_file = SimpleUploadedFile(
            "test_resume.pdf",
            b"content",
            content_type="application/pdf"
        )
        
        response = self.client.post(
            reverse('parse-resume'),
            {'file': uploaded_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Only job seekers', response.data['error'])
    
    def test_parse_resume_view_invalid_file(self):
        """Test resume parsing API with invalid file"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Create invalid file
        uploaded_file = SimpleUploadedFile(
            "test_resume.exe",
            b"content",
            content_type="application/octet-stream"
        )
        
        response = self.client.post(
            reverse('parse-resume'),
            {'file': uploaded_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('File validation failed', response.data['error'])
    
    def test_parse_resume_view_gemini_api_error(self):
        """Test resume parsing API with Gemini API error"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        uploaded_file = SimpleUploadedFile(
            "test_resume.pdf",
            b"content",
            content_type="application/pdf"
        )
        
        with patch('matcher.views.GeminiResumeParser') as mock_parser_class:
            mock_parser_class.side_effect = GeminiAPIError("API not available")
            
            response = self.client.post(
                reverse('parse-resume'),
                {'file': uploaded_file},
                format='multipart'
            )
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('AI service temporarily unavailable', response.data['error'])
    
    def test_parse_resume_by_id_view_success(self):
        """Test successful resume re-parsing by ID"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        with patch('matcher.views.GeminiResumeParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_resume.return_value = {
                'success': True,
                'parsed_text': 'Re-parsed text',
                'structured_data': {'name': 'John Doe'},
                'confidence_score': 0.9,
                'processing_time': 2.0
            }
            mock_parser_class.return_value = mock_parser
            
            response = self.client.post(
                reverse('parse-resume-by-id', kwargs={'resume_id': self.resume.id})
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['resume_id'], str(self.resume.id))
    
    def test_parse_resume_by_id_view_not_found(self):
        """Test resume re-parsing with non-existent resume ID"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        fake_id = 99999  # Non-existent integer ID
        
        response = self.client.post(
            reverse('parse-resume-by-id', kwargs={'resume_id': fake_id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Resume not found', response.data['error'])
    
    def test_parse_resume_async_view_success(self):
        """Test successful async resume parsing"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        with patch('matcher.tasks.parse_resume_task') as mock_task:
            mock_result = MagicMock()
            mock_result.id = 'test-task-id'
            mock_task.apply_async.return_value = mock_result
            
            response = self.client.post(
                reverse('parse-resume-async'),
                {'resume_id': str(self.resume.id)}
            )
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['task_id'], 'test-task-id')
        self.assertEqual(response.data['status'], 'queued')
    
    def test_parse_resume_async_view_no_resume_id(self):
        """Test async resume parsing without resume ID"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        response = self.client.post(reverse('parse-resume-async'), {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('resume_id is required', response.data['error'])
    
    def test_parse_task_status_view_success(self):
        """Test successful task status check"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        with patch('celery.result.AsyncResult') as mock_async_result:
            mock_result = MagicMock()
            mock_result.state = 'SUCCESS'
            mock_result.result = {'status': 'completed'}
            mock_async_result.return_value = mock_result
            
            response = self.client.get(
                reverse('parse-task-status', kwargs={'task_id': 'test-task-id'})
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['task_id'], 'test-task-id')
    
    def test_batch_parse_resumes_view_success(self):
        """Test successful batch resume parsing"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Create another resume
        resume2 = Resume.objects.create(
            job_seeker=self.job_seeker,
            file='test_resume2.pdf',
            original_filename='test_resume2.pdf',
            file_size=1024
        )
        
        resume_ids = [str(self.resume.id), str(resume2.id)]
        
        with patch('matcher.tasks.batch_parse_resumes_task') as mock_task:
            mock_result = MagicMock()
            mock_result.id = 'batch-task-id'
            mock_task.apply_async.return_value = mock_result
            
            response = self.client.post(
                reverse('batch-parse-resumes'),
                {'resume_ids': resume_ids},
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['batch_task_id'], 'batch-task-id')
        self.assertEqual(response.data['resume_count'], 2)
    
    def test_batch_parse_resumes_view_empty_list(self):
        """Test batch resume parsing with empty list"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        response = self.client.post(
            reverse('batch-parse-resumes'),
            {'resume_ids': []}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('must be a non-empty list', response.data['error'])
    
    def test_batch_parse_resumes_view_invalid_resume_ids(self):
        """Test batch resume parsing with invalid resume IDs"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        fake_ids = [99998, 99999]  # Non-existent integer IDs
        
        response = self.client.post(
            reverse('batch-parse-resumes'),
            {'resume_ids': fake_ids},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Some resumes not found', response.data['error'])


class ResumeParsingIntegrationTestCase(APITestCase):
    """Integration tests for resume parsing functionality"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test user
        self.job_seeker = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        JobSeekerProfile.objects.create(user=self.job_seeker)
        
        # Get JWT token
        self.job_seeker_token = str(RefreshToken.for_user(self.job_seeker).access_token)
    
    def test_full_resume_parsing_workflow(self):
        """Test complete resume parsing workflow"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Step 1: Upload and parse resume
        file_content = b"John Doe\nSoftware Engineer\njohn@email.com\nPython, Django, React"
        uploaded_file = SimpleUploadedFile(
            "john_doe_resume.pdf",
            file_content,
            content_type="application/pdf"
        )
        
        with patch('matcher.views.GeminiResumeParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_resume.return_value = {
                'success': True,
                'parsed_text': 'John Doe Software Engineer...',
                'structured_data': {
                    'personal_info': {'name': 'John Doe', 'email': 'john@email.com'},
                    'skills': {'technical_skills': ['Python', 'Django', 'React']},
                    'total_experience_years': 3,
                    'confidence_score': 0.85
                },
                'confidence_score': 0.85,
                'processing_time': 2.1
            }
            mock_parser_class.return_value = mock_parser
            
            # Parse and save resume
            response = self.client.post(
                reverse('parse-resume'),
                {'file': uploaded_file, 'save_resume': 'true'},
                format='multipart'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('resume_id', response.data)
        
        # Verify resume was saved
        resume_id = response.data['resume_id']
        resume = Resume.objects.get(id=resume_id)
        self.assertEqual(resume.job_seeker, self.job_seeker)
        self.assertEqual(resume.original_filename, 'john_doe_resume.pdf')
        
        # Verify AI analysis was created
        analysis = AIAnalysisResult.objects.filter(resume=resume, analysis_type='resume_parse').first()
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.confidence_score, 0.85)
        
        # Step 2: Re-parse existing resume
        with patch('matcher.views.GeminiResumeParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_resume.return_value = {
                'success': True,
                'parsed_text': 'Updated parsed text...',
                'structured_data': {
                    'personal_info': {'name': 'John Doe', 'email': 'john@email.com'},
                    'skills': {'technical_skills': ['Python', 'Django', 'React', 'AWS']},
                    'total_experience_years': 4,
                    'confidence_score': 0.9
                },
                'confidence_score': 0.9,
                'processing_time': 1.8
            }
            mock_parser_class.return_value = mock_parser
            
            response = self.client.post(
                reverse('parse-resume-by-id', kwargs={'resume_id': resume_id})
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify resume was updated
        resume.refresh_from_db()
        self.assertEqual(resume.parsed_text, 'Updated parsed text...')
        
        # Verify new analysis was created
        analyses = AIAnalysisResult.objects.filter(resume=resume, analysis_type='resume_parse')
        self.assertEqual(analyses.count(), 2)  # Original + updated
        
        # Step 3: Queue async parsing
        with patch('matcher.tasks.parse_resume_task') as mock_task:
            mock_result = MagicMock()
            mock_result.id = 'async-task-123'
            mock_task.apply_async.return_value = mock_result
            
            response = self.client.post(
                reverse('parse-resume-async'),
                {'resume_id': resume_id}
            )
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['task_id'], 'async-task-123')
        
        # Step 4: Check task status
        with patch('celery.result.AsyncResult') as mock_async_result:
            mock_result = MagicMock()
            mock_result.state = 'SUCCESS'
            mock_result.result = {
                'resume_id': resume_id,
                'status': 'completed',
                'confidence_score': 0.92
            }
            mock_async_result.return_value = mock_result
            
            response = self.client.get(
                reverse('parse-task-status', kwargs={'task_id': 'async-task-123'})
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('result', response.data)