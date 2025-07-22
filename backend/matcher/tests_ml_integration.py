"""
Tests for ML model integration and job matching functionality
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
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Resume, JobPost, AIAnalysisResult, JobSeekerProfile, RecruiterProfile
from .ml_services import (
    JobMatchMLModel, FeatureExtractor, MatchScoreCache, 
    MLModelError, get_ml_model
)

User = get_user_model()


class JobMatchMLModelTestCase(TestCase):
    """Test cases for JobMatchMLModel"""
    
    def setUp(self):
        self.sample_resume_data = {
            'parsed_text': 'John Doe Software Engineer Python Django React 5 years experience',
            'skills': ['Python', 'Django', 'React', 'JavaScript', 'SQL'],
            'experience_level': 'senior',
            'total_experience_years': 5,
            'education': 'Bachelor of Science in Computer Science',
            'location': 'San Francisco'
        }
        
        self.sample_job_data = {
            'title': 'Senior Python Developer',
            'description': 'We are looking for a senior Python developer with Django experience',
            'requirements': 'Python, Django, React, 3+ years experience',
            'skills_required': ['Python', 'Django', 'React'],
            'experience_level': 'senior',
            'location': 'San Francisco',
            'remote_work_allowed': False,
            'salary_min': 100000,
            'salary_max': 150000
        }
    
    @patch('matcher.ml_services.joblib.load')
    @patch('matcher.ml_services.os.path.exists')
    def test_model_initialization_with_existing_model(self, mock_exists, mock_joblib_load):
        """Test model initialization when existing model files are present"""
        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_vectorizer = MagicMock()
        mock_scaler = MagicMock()
        mock_joblib_load.side_effect = [mock_model, mock_vectorizer, mock_scaler]
        
        ml_model = JobMatchMLModel()
        
        self.assertTrue(ml_model.is_initialized)
        self.assertEqual(ml_model.model, mock_model)
        self.assertEqual(ml_model.vectorizer, mock_vectorizer)
        self.assertEqual(ml_model.scaler, mock_scaler)
    
    @patch('matcher.ml_services.joblib.load')
    @patch('matcher.ml_services.os.path.exists')
    @patch('matcher.ml_services.os.makedirs')
    @patch('matcher.ml_services.joblib.dump')
    def test_model_initialization_create_new_model(self, mock_joblib_dump, mock_makedirs, mock_exists, mock_joblib_load):
        """Test model initialization when no existing model is found"""
        mock_exists.return_value = False
        
        ml_model = JobMatchMLModel()
        
        self.assertTrue(ml_model.is_initialized)
        self.assertIsNotNone(ml_model.model)
        self.assertIsNotNone(ml_model.vectorizer)
        self.assertIsNotNone(ml_model.scaler)
        
        # Verify model was saved
        self.assertEqual(mock_joblib_dump.call_count, 3)  # model, vectorizer, scaler
    
    def test_generate_synthetic_training_data(self):
        """Test synthetic training data generation"""
        ml_model = JobMatchMLModel()
        training_data = ml_model._generate_synthetic_training_data()
        
        self.assertEqual(len(training_data), 1000)
        
        # Check structure of first item
        first_item = training_data[0]
        required_keys = [
            'job_skills', 'job_experience', 'job_location', 'job_education',
            'resume_skills', 'resume_experience', 'resume_location', 'resume_education',
            'score'
        ]
        
        for key in required_keys:
            self.assertIn(key, first_item)
        
        # Check score is between 0 and 1
        self.assertGreaterEqual(first_item['score'], 0)
        self.assertLessEqual(first_item['score'], 1)
    
    @patch('matcher.ml_services.joblib.load')
    @patch('matcher.ml_services.os.path.exists')
    def test_calculate_match_score_ml_based(self, mock_exists, mock_joblib_load):
        """Test match score calculation using ML model"""
        mock_exists.return_value = True
        
        # Mock ML model components
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.85]
        mock_vectorizer = MagicMock()
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        
        mock_joblib_load.side_effect = [mock_model, mock_vectorizer, mock_scaler]
        
        ml_model = JobMatchMLModel()
        result = ml_model.calculate_match_score(self.sample_resume_data, self.sample_job_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['match_score'], 85.0)  # 0.85 * 100
        self.assertEqual(result['method'], 'ml_model')
        self.assertIn('analysis', result)
    
    def test_calculate_match_score_rule_based_fallback(self):
        """Test match score calculation using rule-based fallback"""
        # Initialize model without existing files to trigger fallback
        with patch('matcher.ml_services.os.path.exists', return_value=False), \
             patch('matcher.ml_services.os.makedirs'), \
             patch('matcher.ml_services.joblib.dump'):
            
            ml_model = JobMatchMLModel()
            ml_model.is_initialized = False  # Force rule-based scoring
            
            result = ml_model.calculate_match_score(self.sample_resume_data, self.sample_job_data)
            
            self.assertTrue(result['success'])
            self.assertGreater(result['match_score'], 0)
            self.assertEqual(result['method'], 'rule_based')
            self.assertIn('analysis', result)
            self.assertIn('component_scores', result['analysis'])
    
    def test_skill_match_calculation(self):
        """Test skill matching calculation"""
        ml_model = JobMatchMLModel()
        
        resume_data = {'skills': ['Python', 'Django', 'React', 'JavaScript']}
        job_data = {'skills_required': ['Python', 'Django', 'Vue.js']}
        
        skill_score = ml_model._calculate_skill_match(resume_data, job_data)
        
        # Jaccard similarity: intersection=2, union=5, score=2/5=0.4
        self.assertAlmostEqual(skill_score, 0.4, places=2)
    
    def test_experience_match_calculation(self):
        """Test experience level matching calculation"""
        ml_model = JobMatchMLModel()
        
        # Perfect match
        resume_data = {'experience_level': 'senior', 'total_experience_years': 7}
        job_data = {'experience_level': 'senior'}
        
        exp_score = ml_model._calculate_experience_match(resume_data, job_data)
        self.assertEqual(exp_score, 1.0)
        
        # Underqualified
        resume_data = {'experience_level': 'mid'}
        job_data = {'experience_level': 'senior'}
        
        exp_score = ml_model._calculate_experience_match(resume_data, job_data)
        self.assertLess(exp_score, 1.0)
    
    def test_location_match_calculation(self):
        """Test location matching calculation"""
        ml_model = JobMatchMLModel()
        
        # Remote work
        resume_data = {'location': 'New York'}
        job_data = {'location': 'Remote', 'remote_work_allowed': True}
        
        location_score = ml_model._calculate_location_match(resume_data, job_data)
        self.assertEqual(location_score, 1.0)
        
        # Exact match
        resume_data = {'location': 'San Francisco'}
        job_data = {'location': 'San Francisco'}
        
        location_score = ml_model._calculate_location_match(resume_data, job_data)
        self.assertEqual(location_score, 1.0)
        
        # Different locations
        resume_data = {'location': 'New York'}
        job_data = {'location': 'Los Angeles'}
        
        location_score = ml_model._calculate_location_match(resume_data, job_data)
        self.assertEqual(location_score, 0.3)
    
    def test_text_similarity_calculation(self):
        """Test text similarity calculation"""
        ml_model = JobMatchMLModel()
        
        # Similar texts
        resume_data = {'parsed_text': 'Python Django web development'}
        job_data = {'description': 'Python Django developer position'}
        
        similarity = ml_model._simple_text_similarity(
            resume_data['parsed_text'], 
            job_data['description']
        )
        
        self.assertGreater(similarity, 0)
        self.assertLessEqual(similarity, 1)


class FeatureExtractorTestCase(TestCase):
    """Test cases for FeatureExtractor"""
    
    def test_extract_resume_features(self):
        """Test resume feature extraction"""
        resume_data = {
            'parsed_text': 'John Doe Software Engineer',
            'skills': 'Python, Django, React',
            'structured_data': {
                'skills': {
                    'technical_skills': ['Python', 'Django'],
                    'programming_languages': ['Python', 'JavaScript']
                },
                'total_experience_years': 5,
                'education': [{'degree': 'Bachelor of Science'}],
                'personal_info': {'location': 'San Francisco'}
            }
        }
        
        features = FeatureExtractor.extract_resume_features(resume_data)
        
        self.assertIn('skills', features)
        self.assertIn('experience_level', features)
        self.assertIn('total_experience_years', features)
        self.assertIn('education', features)
        self.assertIn('location', features)
        self.assertIn('parsed_text', features)
        
        self.assertEqual(features['total_experience_years'], 5)
        self.assertEqual(features['location'], 'San Francisco')
        self.assertIn('Python', features['skills'])
    
    def test_extract_job_features(self):
        """Test job feature extraction"""
        job_data = {
            'title': 'Senior Python Developer',
            'description': 'Python development position',
            'skills_required': 'Python, Django, React',
            'experience_level': 'senior',
            'location': 'San Francisco',
            'remote_work_allowed': True,
            'salary_min': 100000,
            'salary_max': 150000
        }
        
        features = FeatureExtractor.extract_job_features(job_data)
        
        self.assertEqual(features['title'], 'Senior Python Developer')
        self.assertEqual(features['experience_level'], 'senior')
        self.assertEqual(features['location'], 'San Francisco')
        self.assertTrue(features['remote_work_allowed'])
        self.assertEqual(features['salary_min'], 100000)
        self.assertIn('Python', features['skills_required'])


class MatchScoreCacheTestCase(TestCase):
    """Test cases for MatchScoreCache"""
    
    def setUp(self):
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_cache_operations(self):
        """Test cache get, set, and invalidate operations"""
        resume_id = 'test-resume-123'
        job_id = 'test-job-456'
        score_data = {
            'match_score': 85.5,
            'confidence': 0.9,
            'method': 'ml_model'
        }
        
        # Test cache miss
        cached_score = MatchScoreCache.get_cached_score(resume_id, job_id)
        self.assertIsNone(cached_score)
        
        # Test cache set
        MatchScoreCache.cache_score(resume_id, job_id, score_data)
        
        # Test cache hit
        cached_score = MatchScoreCache.get_cached_score(resume_id, job_id)
        self.assertIsNotNone(cached_score)
        self.assertEqual(cached_score['match_score'], 85.5)
        
        # Test cache invalidation
        MatchScoreCache.invalidate_cache(resume_id, job_id)
        cached_score = MatchScoreCache.get_cached_score(resume_id, job_id)
        self.assertIsNone(cached_score)
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        resume_id = 'resume-123'
        job_id = 'job-456'
        
        cache_key = MatchScoreCache.get_cache_key(resume_id, job_id)
        expected_key = f"match_score:{resume_id}:{job_id}"
        
        self.assertEqual(cache_key, expected_key)


class MatchScoreAPITestCase(APITestCase):
    """Test cases for match score API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        
        # Create test users
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
        JobSeekerProfile.objects.create(
            user=self.job_seeker,
            skills='Python, Django, React'
        )
        
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Corp'
        )
        
        # Create test resume
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker,
            file='test_resume.pdf',
            original_filename='test_resume.pdf',
            file_size=1024,
            parsed_text='John Doe Software Engineer Python Django React 5 years experience'
        )
        
        # Create test job post
        self.job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Senior Python Developer',
            description='We are looking for a senior Python developer',
            requirements='Python, Django, React, 3+ years experience',
            skills_required='Python, Django, React',
            experience_level='senior',
            location='San Francisco',
            salary_min=100000,
            salary_max=150000
        )
        
        # Get JWT tokens
        self.job_seeker_token = str(RefreshToken.for_user(self.job_seeker).access_token)
        self.recruiter_token = str(RefreshToken.for_user(self.recruiter).access_token)
    
    def tearDown(self):
        cache.clear()
    
    @patch('matcher.ml_services.get_ml_model')
    def test_calculate_match_score_success(self, mock_get_ml_model):
        """Test successful match score calculation"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Mock ML model
        mock_model = MagicMock()
        mock_model.calculate_match_score.return_value = {
            'success': True,
            'match_score': 87.5,
            'confidence': 0.85,
            'method': 'ml_model',
            'analysis': {
                'matching_skills': ['Python', 'Django'],
                'missing_skills': ['React'],
                'recommendations': ['Strong match in Python, Django']
            },
            'processing_time': 1.2
        }
        mock_get_ml_model.return_value = mock_model
        
        response = self.client.post(
            reverse('calculate-match-score'),
            {
                'resume_id': str(self.resume.id),
                'job_id': str(self.job_post.id)
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['match_score'], 87.5)
        self.assertEqual(response.data['confidence'], 0.85)
        self.assertIn('analysis', response.data)
        
        # Verify AI analysis result was created
        analysis = AIAnalysisResult.objects.filter(
            resume=self.resume,
            job_post=self.job_post,
            analysis_type='job_match'
        ).first()
        self.assertIsNotNone(analysis)
    
    def test_calculate_match_score_missing_parameters(self):
        """Test match score calculation with missing parameters"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        response = self.client.post(
            reverse('calculate-match-score'),
            {'resume_id': str(self.resume.id)},  # Missing job_id
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Both resume_id and job_id are required', response.data['error'])
    
    def test_calculate_match_score_resume_not_found(self):
        """Test match score calculation with non-existent resume"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        import uuid
        fake_resume_id = str(uuid.uuid4())
        
        response = self.client.post(
            reverse('calculate-match-score'),
            {
                'resume_id': fake_resume_id,
                'job_id': str(self.job_post.id)
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Resume not found', response.data['error'])
    
    def test_calculate_match_score_job_not_found(self):
        """Test match score calculation with non-existent job"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        fake_job_id = '12345678-1234-5678-9012-123456789012'
        
        response = self.client.post(
            reverse('calculate-match-score'),
            {
                'resume_id': str(self.resume.id),
                'job_id': fake_job_id
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Job post not found', response.data['error'])
    
    @patch('matcher.views.MatchScoreCache.get_cached_score')
    def test_calculate_match_score_cached_result(self, mock_get_cached_score):
        """Test match score calculation with cached result"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Mock cached result
        cached_data = {
            'success': True,
            'match_score': 90.0,
            'confidence': 0.9,
            'method': 'ml_model',
            'cached': True
        }
        mock_get_cached_score.return_value = cached_data
        
        response = self.client.post(
            reverse('calculate-match-score'),
            {
                'resume_id': str(self.resume.id),
                'job_id': str(self.job_post.id)
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, cached_data)
    
    def test_calculate_match_score_async_success(self):
        """Test successful async match score calculation"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        with patch('matcher.tasks.calculate_match_score_task') as mock_task:
            mock_result = MagicMock()
            mock_result.id = 'test-task-id'
            mock_task.apply_async.return_value = mock_result
            
            response = self.client.post(
                reverse('calculate-match-score-async'),
                {
                    'resume_id': str(self.resume.id),
                    'job_id': str(self.job_post.id)
                },
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['task_id'], 'test-task-id')
        self.assertEqual(response.data['status'], 'queued')
    
    def test_batch_calculate_match_scores_success(self):
        """Test successful batch match score calculation"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Create another resume and job
        resume2 = Resume.objects.create(
            job_seeker=self.job_seeker,
            file='test_resume2.pdf',
            original_filename='test_resume2.pdf',
            file_size=1024
        )
        
        job_post2 = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Junior Python Developer',
            description='Entry level Python position',
            skills_required='Python, Django',
            experience_level='entry',
            location='Remote'
        )
        
        resume_ids = [str(self.resume.id), str(resume2.id)]
        job_ids = [str(self.job_post.id), str(job_post2.id)]
        
        with patch('matcher.tasks.batch_calculate_match_scores_task') as mock_task:
            mock_result = MagicMock()
            mock_result.id = 'batch-task-id'
            mock_task.apply_async.return_value = mock_result
            
            response = self.client.post(
                reverse('batch-calculate-match-scores'),
                {
                    'resume_ids': resume_ids,
                    'job_ids': job_ids
                },
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['batch_task_id'], 'batch-task-id')
        self.assertEqual(response.data['total_combinations'], 4)  # 2 resumes * 2 jobs
    
    def test_get_match_scores_for_resume_success(self):
        """Test getting match scores for a specific resume"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Create AI analysis result
        AIAnalysisResult.objects.create(
            resume=self.resume,
            job_post=self.job_post,
            analysis_type='job_match',
            input_data='Test match calculation',
            analysis_result={
                'match_score': 85.0,
                'analysis': {'matching_skills': ['Python', 'Django']},
                'method': 'ml_model'
            },
            confidence_score=0.85,
            processing_time=1.5
        )
        
        response = self.client.get(
            reverse('match-scores-for-resume', kwargs={'resume_id': self.resume.id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['resume_id'], str(self.resume.id))
        self.assertEqual(response.data['total_matches'], 1)
        self.assertEqual(len(response.data['match_scores']), 1)
        
        match_score = response.data['match_scores'][0]
        self.assertEqual(match_score['match_score'], 85.0)
        self.assertEqual(match_score['job_title'], self.job_post.title)
    
    def test_get_match_scores_for_job_success(self):
        """Test getting match scores for a specific job (recruiter only)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.recruiter_token}')
        
        # Create AI analysis result
        AIAnalysisResult.objects.create(
            resume=self.resume,
            job_post=self.job_post,
            analysis_type='job_match',
            input_data='Test match calculation',
            analysis_result={
                'match_score': 87.5,
                'analysis': {'matching_skills': ['Python', 'Django']},
                'method': 'ml_model'
            },
            confidence_score=0.875,
            processing_time=1.2
        )
        
        response = self.client.get(
            reverse('match-scores-for-job', kwargs={'job_id': self.job_post.id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['job_id'], str(self.job_post.id))
        self.assertEqual(response.data['total_candidates'], 1)
        self.assertEqual(len(response.data['match_scores']), 1)
        
        match_score = response.data['match_scores'][0]
        self.assertEqual(match_score['match_score'], 87.5)
        self.assertEqual(match_score['resume_id'], str(self.resume.id))
    
    def test_get_match_scores_for_job_forbidden_for_job_seeker(self):
        """Test that job seekers cannot access job match scores"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        response = self.client.get(
            reverse('match-scores-for-job', kwargs={'job_id': self.job_post.id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Only recruiters can view', response.data['error'])


class MLModelIntegrationTestCase(APITestCase):
    """Integration tests for ML model functionality"""
    
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        
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
        
        JobSeekerProfile.objects.create(
            user=self.job_seeker,
            skills='Python, Django, React, JavaScript, SQL'
        )
        
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Innovations Inc'
        )
        
        # Get JWT token
        self.job_seeker_token = str(RefreshToken.for_user(self.job_seeker).access_token)
    
    def tearDown(self):
        cache.clear()
    
    def test_full_ml_workflow(self):
        """Test complete ML workflow from resume parsing to match scoring"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Step 1: Create resume with parsed data
        resume = Resume.objects.create(
            job_seeker=self.job_seeker,
            file='john_doe_resume.pdf',
            original_filename='john_doe_resume.pdf',
            file_size=2048,
            parsed_text='John Doe Senior Software Engineer Python Django React JavaScript 5 years experience Bachelor Computer Science'
        )
        
        # Step 2: Create AI analysis for resume parsing
        AIAnalysisResult.objects.create(
            resume=resume,
            analysis_type='resume_parse',
            input_data=resume.parsed_text[:1000],
            analysis_result={
                'personal_info': {
                    'name': 'John Doe',
                    'email': 'john@example.com'
                },
                'skills': {
                    'technical_skills': ['Python', 'Django', 'React', 'JavaScript'],
                    'programming_languages': ['Python', 'JavaScript']
                },
                'total_experience_years': 5,
                'education': [{'degree': 'Bachelor of Science in Computer Science'}]
            },
            confidence_score=0.9,
            processing_time=2.1
        )
        
        # Step 3: Create job post
        job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Senior Full Stack Developer',
            description='We are seeking a senior full stack developer with strong Python and React skills',
            requirements='Python, Django, React, JavaScript, 3+ years experience, Bachelor degree preferred',
            skills_required='Python, Django, React, JavaScript, SQL',
            experience_level='senior',
            location='San Francisco',
            remote_work_allowed=True,
            salary_min=120000,
            salary_max=180000
        )
        
        # Step 4: Calculate match score
        with patch('matcher.views.get_ml_model') as mock_get_ml_model:
            mock_model = MagicMock()
            mock_model.calculate_match_score.return_value = {
                'success': True,
                'match_score': 92.5,
                'confidence': 0.88,
                'method': 'ml_model',
                'analysis': {
                    'matching_skills': ['Python', 'Django', 'React', 'JavaScript'],
                    'missing_skills': ['SQL'],
                    'experience_analysis': 'Perfect match for senior level position',
                    'location_analysis': 'Remote work available - location flexible',
                    'recommendations': [
                        'Strong match in: Python, Django, React',
                        'Consider developing skills in: SQL'
                    ]
                },
                'processing_time': 1.8
            }
            mock_get_ml_model.return_value = mock_model
            
            response = self.client.post(
                reverse('calculate-match-score'),
                {
                    'resume_id': str(resume.id),
                    'job_id': str(job_post.id)
                },
                format='json'
            )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['match_score'], 92.5)
        self.assertEqual(response.data['confidence'], 0.88)
        self.assertEqual(response.data['method'], 'ml_model')
        
        # Verify analysis details
        analysis = response.data['analysis']
        self.assertIn('matching_skills', analysis)
        self.assertIn('missing_skills', analysis)
        self.assertIn('recommendations', analysis)
        self.assertEqual(len(analysis['matching_skills']), 4)
        self.assertEqual(len(analysis['missing_skills']), 1)
        
        # Step 5: Verify AI analysis result was created
        match_analysis = AIAnalysisResult.objects.filter(
            resume=resume,
            job_post=job_post,
            analysis_type='job_match'
        ).first()
        
        self.assertIsNotNone(match_analysis)
        self.assertEqual(match_analysis.analysis_result['match_score'], 92.5)
        self.assertEqual(match_analysis.confidence_score, 0.88)
        
        # Step 6: Test caching by making the same request again
        response2 = self.client.post(
            reverse('calculate-match-score'),
            {
                'resume_id': str(resume.id),
                'job_id': str(job_post.id)
            },
            format='json'
        )
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        # Note: In a real scenario, this would return cached data
        
        # Step 7: Get all match scores for the resume
        response3 = self.client.get(
            reverse('match-scores-for-resume', kwargs={'resume_id': resume.id})
        )
        
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertEqual(response3.data['total_matches'], 1)
        self.assertEqual(response3.data['match_scores'][0]['match_score'], 92.5)
    
    def test_ml_model_error_handling(self):
        """Test ML model error handling and fallback"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        resume = Resume.objects.create(
            job_seeker=self.job_seeker,
            file='test_resume.pdf',
            original_filename='test_resume.pdf',
            file_size=1024,
            parsed_text='Test resume content'
        )
        
        job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Test Job',
            description='Test job description',
            skills_required='Python, Django',
            experience_level='mid'
        )
        
        # Mock ML model to raise an error, then fall back to rule-based
        with patch('matcher.views.get_ml_model') as mock_get_ml_model:
            mock_model = MagicMock()
            mock_model.calculate_match_score.return_value = {
                'success': True,
                'match_score': 65.0,
                'confidence': 0.75,
                'method': 'rule_based',  # Fallback method
                'analysis': {
                    'matching_skills': ['Python'],
                    'missing_skills': ['Django'],
                    'recommendations': ['Consider developing skills in: Django']
                },
                'processing_time': 0.5
            }
            mock_get_ml_model.return_value = mock_model
            
            response = self.client.post(
                reverse('calculate-match-score'),
                {
                    'resume_id': str(resume.id),
                    'job_id': str(job_post.id)
                },
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['method'], 'rule_based')
        self.assertGreater(response.data['match_score'], 0)