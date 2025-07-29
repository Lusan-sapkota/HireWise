"""
Tests for AI-powered resume assistance functionality
"""

import json
import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost,
    AIAnalysisResult
)
from .ml_services import (
    ResumeAnalysisEngine, generate_resume_suggestions, analyze_resume_content
)

User = get_user_model()


class ResumeAnalysisEngineTestCase(TestCase):
    """Test cases for ResumeAnalysisEngine"""
    
    def setUp(self):
        self.engine = ResumeAnalysisEngine()
        self.sample_resume = """
        John Doe
        Software Engineer
        
        Experience:
        - Developed web applications using Python and Django
        - Managed team of 5 developers
        - Increased system performance by 30%
        - Led migration to cloud infrastructure
        
        Skills:
        Python, Django, JavaScript, React, AWS, Docker
        
        Education:
        Bachelor of Science in Computer Science
        """
        
        self.sample_job_requirements = [
            "Python programming experience",
            "Django framework knowledge",
            "Team leadership skills",
            "Cloud computing experience",
            "Bachelor's degree in Computer Science"
        ]
    
    def test_analyze_content_structure(self):
        """Test content structure analysis"""
        analysis = self.engine._analyze_content_structure(self.sample_resume)
        
        self.assertIn('scores', analysis)
        self.assertIn('strengths', analysis)
        self.assertIn('weaknesses', analysis)
        
        # Check that scores are within valid range
        for score in analysis['scores'].values():
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)
    
    def test_analyze_keywords(self):
        """Test keyword analysis"""
        target_job = "Senior Python Developer with Django experience"
        analysis = self.engine._analyze_keywords(
            self.sample_resume, 
            target_job, 
            self.sample_job_requirements
        )
        
        self.assertIn('score', analysis)
        self.assertIn('found_keywords', analysis)
        self.assertIn('missing_keywords', analysis)
        self.assertIn('industry', analysis)
        
        # Should find Python and Django keywords
        found_keywords_lower = [kw.lower() for kw in analysis['found_keywords']]
        self.assertIn('python', found_keywords_lower)
        self.assertIn('django', found_keywords_lower)
    
    def test_analyze_skill_gaps(self):
        """Test skill gap analysis"""
        analysis = self.engine._analyze_skill_gaps(
            self.sample_resume, 
            self.sample_job_requirements
        )
        
        self.assertIn('alignment_score', analysis)
        self.assertIn('technical_skills', analysis)
        self.assertIn('soft_skills', analysis)
        self.assertIn('priority_gaps', analysis)
        
        # Should have high alignment score for this matching resume
        self.assertGreater(analysis['alignment_score'], 70)
    
    def test_detect_industry(self):
        """Test industry detection"""
        tech_job = "Software Engineer Python Developer"
        marketing_job = "Digital Marketing Manager SEO Specialist"
        
        self.assertEqual(self.engine._detect_industry(tech_job), 'technology')
        self.assertEqual(self.engine._detect_industry(marketing_job), 'marketing')
        self.assertEqual(self.engine._detect_industry(""), 'general')
    
    def test_calculate_overall_score(self):
        """Test overall score calculation"""
        category_scores = {
            'length': 85,
            'sections': 90,
            'action_verbs': 80,
            'quantification': 75,
            'keyword_optimization': 85,
            'skill_alignment': 90
        }
        
        overall_score = self.engine._calculate_overall_score(category_scores)
        
        self.assertGreater(overall_score, 0)
        self.assertLessEqual(overall_score, 100)
        self.assertIsInstance(overall_score, float)
    
    @patch('matcher.ml_services.genai')
    def test_get_ai_suggestions_with_api(self, mock_genai):
        """Test AI suggestions with mocked Gemini API"""
        # Mock the Gemini API response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """
        1. Add more quantified achievements with specific numbers
        2. Use stronger action verbs to begin bullet points
        3. Include relevant technical certifications
        4. Tailor skills section to match job requirements
        5. Add a professional summary at the top
        """
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Set API key for test
        self.engine.gemini_api_key = "test_key"
        
        suggestions = self.engine._get_ai_suggestions(
            self.sample_resume, 
            "Software Engineer"
        )
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        self.assertLessEqual(len(suggestions), 7)
    
    def test_get_ai_suggestions_fallback(self):
        """Test AI suggestions fallback when API is not available"""
        # No API key set
        self.engine.gemini_api_key = None
        
        suggestions = self.engine._get_ai_suggestions(
            self.sample_resume, 
            "Software Engineer"
        )
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        # Should return default suggestions
        self.assertIn("quantified achievements", suggestions[0].lower())
    
    def test_generate_improvement_recommendations(self):
        """Test improvement recommendations generation"""
        analysis_result = {
            'category_scores': {
                'quantification': 60,  # Low score
                'action_verbs': 80,    # Good score
                'keyword_optimization': 65,  # Low score
                'sections': 90         # Good score
            },
            'skill_gap_analysis': {
                'alignment_score': 65,
                'priority_gaps': ['Docker', 'Kubernetes', 'AWS']
            }
        }
        
        recommendations = self.engine._generate_improvement_recommendations(analysis_result)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should include high priority recommendations for low scores
        priorities = [rec['priority'] for rec in recommendations]
        self.assertIn('high', priorities)
        
        # Should include quantification recommendation
        categories = [rec['category'] for rec in recommendations]
        self.assertIn('Achievement Quantification', categories)


class ResumeAssistanceFunctionsTestCase(TestCase):
    """Test cases for resume assistance utility functions"""
    
    def test_generate_resume_suggestions(self):
        """Test resume content suggestions generation"""
        result = generate_resume_suggestions(
            job_title="Software Engineer",
            experience_level="mid",
            skills=["Python", "Django", "React"],
            industry="technology"
        )
        
        self.assertTrue(result['success'])
        self.assertIn('suggestions', result)
        
        suggestions = result['suggestions']
        self.assertIn('professional_summary', suggestions)
        self.assertIn('skills_optimization', suggestions)
        self.assertIn('experience_bullets', suggestions)
        self.assertIn('keywords_to_include', suggestions)
        self.assertIn('achievement_examples', suggestions)
        self.assertIn('industry_specific_tips', suggestions)
    
    def test_analyze_resume_content(self):
        """Test resume content analysis"""
        sample_resume = """
        Jane Smith
        Marketing Manager
        
        Experience:
        - Managed digital marketing campaigns
        - Increased conversion rates by 25%
        - Led team of 3 marketing specialists
        
        Skills:
        Google Analytics, SEO, Social Media Marketing
        """
        
        result = analyze_resume_content(
            resume_content=sample_resume,
            target_job="Digital Marketing Manager",
            job_requirements=["Google Analytics", "SEO", "Team leadership"]
        )
        
        self.assertTrue(result['success'])
        self.assertIn('analysis', result)
        
        analysis = result['analysis']
        self.assertIn('overall_score', analysis)
        self.assertIn('category_scores', analysis)
        self.assertIn('strengths', analysis)
        self.assertIn('weaknesses', analysis)


class AIResumeAssistanceAPITestCase(APITestCase):
    """Test cases for AI resume assistance API endpoints"""
    
    def setUp(self):
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
        JobSeekerProfile.objects.create(user=self.job_seeker)
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Test Company'
        )
        
        # Create test resume
        self.resume = Resume.objects.create(
            job_seeker=self.job_seeker,
            original_filename='test_resume.pdf',
            parsed_text="""
            John Doe
            Software Engineer
            
            Experience:
            - Developed web applications using Python and Django
            - Managed team of 5 developers
            - Increased system performance by 30%
            
            Skills:
            Python, Django, JavaScript, React, AWS
            
            Education:
            Bachelor of Science in Computer Science
            """
        )
        
        # Create test job post
        self.job_post = JobPost.objects.create(
            recruiter=self.recruiter,
            title='Senior Python Developer',
            description='Looking for experienced Python developer',
            requirements='Python, Django, team leadership, cloud experience',
            location='Remote',
            job_type='full_time',
            experience_level='senior',
            skills_required='Python, Django, AWS, Docker'
        )
        
        # Get JWT tokens
        self.job_seeker_token = str(RefreshToken.for_user(self.job_seeker).access_token)
        self.recruiter_token = str(RefreshToken.for_user(self.recruiter).access_token)
    
    def test_get_resume_suggestions(self):
        """Test resume suggestions endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        data = {
            'resume_content': self.resume.parsed_text,
            'target_job': 'Senior Python Developer',
            'job_requirements': ['Python', 'Django', 'Team leadership']
        }
        
        response = self.client.post(
            '/api/v1/resume-builder/suggestions/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('analysis', response.data)
        
        analysis = response.data['analysis']['analysis']
        self.assertIn('overall_score', analysis)
        self.assertIn('category_scores', analysis)
        self.assertIn('improvement_recommendations', analysis)
    
    def test_analyze_resume_for_job(self):
        """Test resume-job analysis endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        data = {
            'resume_id': str(self.resume.id),
            'job_id': str(self.job_post.id)
        }
        
        response = self.client.post(
            '/api/v1/resume-analysis/analyze-for-job/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('analysis', response.data)
        self.assertEqual(response.data['job_title'], self.job_post.title)
        
        # Check that AI analysis result was created
        self.assertTrue(
            AIAnalysisResult.objects.filter(
                resume=self.resume,
                job_post=self.job_post,
                analysis_type='resume_analysis'
            ).exists()
        )
    
    def test_get_skill_gap_analysis(self):
        """Test skill gap analysis endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        data = {
            'resume_content': self.resume.parsed_text,
            'job_requirements': [
                'Python programming',
                'Django framework',
                'Docker containerization',
                'Kubernetes orchestration',
                'Team leadership'
            ]
        }
        
        response = self.client.post(
            '/api/v1/resume-analysis/skill-gap/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('skill_gap_analysis', response.data)
        
        analysis = response.data['skill_gap_analysis']
        self.assertIn('alignment_score', analysis)
        self.assertIn('technical_skills', analysis)
        self.assertIn('priority_gaps', analysis)
    
    def test_score_resume_content(self):
        """Test resume scoring endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        data = {
            'resume_content': self.resume.parsed_text
        }
        
        response = self.client.post(
            '/api/v1/resume-analysis/score/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('overall_score', response.data)
        self.assertIn('category_scores', response.data)
        self.assertIn('strengths', response.data)
        self.assertIn('weaknesses', response.data)
        
        # Score should be between 0 and 100
        self.assertGreaterEqual(response.data['overall_score'], 0)
        self.assertLessEqual(response.data['overall_score'], 100)
    
    def test_get_keyword_optimization(self):
        """Test keyword optimization endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        data = {
            'resume_content': self.resume.parsed_text,
            'target_job': 'Senior Python Developer with Django experience',
            'job_requirements': ['Python', 'Django', 'AWS', 'Docker']
        }
        
        response = self.client.post(
            '/api/v1/resume-analysis/keywords/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('keyword_analysis', response.data)
        
        analysis = response.data['keyword_analysis']
        self.assertIn('score', analysis)
        self.assertIn('found_keywords', analysis)
        self.assertIn('missing_keywords', analysis)
        self.assertIn('industry', analysis)
    
    def test_get_resume_analysis_history(self):
        """Test resume analysis history endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Create some analysis history
        AIAnalysisResult.objects.create(
            resume=self.resume,
            job_post=self.job_post,
            analysis_type='resume_analysis',
            input_data='Test analysis',
            analysis_result={'overall_score': 85, 'test': True},
            confidence_score=0.85
        )
        
        response = self.client.get(
            f'/api/v1/resume-analysis/{self.resume.id}/history/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('analysis_history', response.data)
        self.assertEqual(response.data['total_analyses'], 1)
        
        history = response.data['analysis_history'][0]
        self.assertIn('analysis_type', history)
        self.assertIn('processed_at', history)
        self.assertIn('job_post', history)
    
    def test_generate_resume_content_suggestions(self):
        """Test resume content generation endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        data = {
            'job_title': 'Software Engineer',
            'experience_level': 'mid',
            'skills': ['Python', 'Django', 'React'],
            'industry': 'technology'
        }
        
        response = self.client.post(
            '/api/v1/resume-builder/generate/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('suggestions', response.data)
        
        suggestions = response.data['suggestions']
        self.assertIn('professional_summary', suggestions)
        self.assertIn('skills_optimization', suggestions)
        self.assertIn('experience_bullets', suggestions)
    
    def test_unauthorized_access(self):
        """Test that endpoints require authentication"""
        data = {'resume_content': 'test content'}
        
        endpoints = [
            'resume-suggestions',
            'analyze-resume-for-job',
            'skill-gap-analysis',
            'score-resume-content',
            'keyword-optimization'
        ]
        
        endpoint_urls = [
            '/api/v1/resume-builder/suggestions/',
            '/api/v1/resume-analysis/analyze-for-job/',
            '/api/v1/resume-analysis/skill-gap/',
            '/api/v1/resume-analysis/score/',
            '/api/v1/resume-analysis/keywords/'
        ]
        
        for endpoint_url in endpoint_urls:
            response = self.client.post(
                endpoint_url,
                data=data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_resume_id(self):
        """Test handling of invalid resume ID"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        data = {
            'resume_id': str(uuid.uuid4()),
            'job_id': str(self.job_post.id)
        }
        
        response = self.client.post(
            '/api/v1/resume-analysis/analyze-for-job/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_invalid_job_id(self):
        """Test handling of invalid job ID"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        data = {
            'resume_id': str(self.resume.id),
            'job_id': str(uuid.uuid4())
        }
        
        response = self.client.post(
            '/api/v1/resume-analysis/analyze-for-job/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_missing_required_fields(self):
        """Test validation of required fields"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
        
        # Test missing resume_content
        response = self.client.post(
            '/api/v1/resume-builder/suggestions/',
            data={},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Test missing job_requirements for skill gap analysis
        response = self.client.post(
            '/api/v1/resume-analysis/skill-gap/',
            data={'resume_content': 'test content'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_recruiter_access_to_resume_analysis(self):
        """Test that recruiters can access resume analysis for any resume"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.recruiter_token}')
        
        data = {
            'resume_id': str(self.resume.id),
            'job_id': str(self.job_post.id)
        }
        
        response = self.client.post(
            '/api/v1/resume-analysis/analyze-for-job/',
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])


class ResumeAssistanceIntegrationTestCase(APITestCase):
    """Integration tests for complete resume assistance workflow"""
    
    def setUp(self):
        self.job_seeker = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        JobSeekerProfile.objects.create(user=self.job_seeker)
        
        self.job_seeker_token = str(RefreshToken.for_user(self.job_seeker).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.job_seeker_token}')
    
    def test_complete_resume_improvement_workflow(self):
        """Test complete workflow from analysis to improvement"""
        resume_content = """
        John Smith
        Developer
        
        Experience:
        - Worked on web applications
        - Used Python and JavaScript
        - Helped with team projects
        
        Skills:
        Python, JavaScript, HTML, CSS
        """
        
        # Step 1: Get initial resume score
        score_response = self.client.post(
            '/api/v1/resume-analysis/score/',
            data={'resume_content': resume_content},
            format='json'
        )
        
        self.assertEqual(score_response.status_code, status.HTTP_200_OK)
        initial_score = score_response.data['overall_score']
        
        # Step 2: Get improvement suggestions
        suggestions_response = self.client.post(
            '/api/v1/resume-builder/suggestions/',
            data={
                'resume_content': resume_content,
                'target_job': 'Senior Python Developer'
            },
            format='json'
        )
        
        self.assertEqual(suggestions_response.status_code, status.HTTP_200_OK)
        suggestions = suggestions_response.data['analysis']['analysis']
        
        # Should have improvement recommendations
        self.assertIn('improvement_recommendations', suggestions)
        self.assertGreater(len(suggestions['improvement_recommendations']), 0)
        
        # Step 3: Get keyword optimization suggestions
        keyword_response = self.client.post(
            '/api/v1/resume-analysis/keywords/',
            data={
                'resume_content': resume_content,
                'target_job': 'Senior Python Developer with Django experience'
            },
            format='json'
        )
        
        self.assertEqual(keyword_response.status_code, status.HTTP_200_OK)
        keyword_analysis = keyword_response.data['keyword_analysis']
        
        # Should identify missing keywords
        self.assertIn('missing_keywords', keyword_analysis)
        self.assertGreater(len(keyword_analysis['missing_keywords']), 0)
        
        # Step 4: Get skill gap analysis
        skill_gap_response = self.client.post(
            '/api/v1/resume-analysis/skill-gap/',
            data={
                'resume_content': resume_content,
                'job_requirements': [
                    'Python programming',
                    'Django framework',
                    'Team leadership',
                    'AWS cloud services',
                    'Docker containerization'
                ]
            },
            format='json'
        )
        
        self.assertEqual(skill_gap_response.status_code, status.HTTP_200_OK)
        skill_gap = skill_gap_response.data['skill_gap_analysis']
        
        # Should identify skill gaps
        self.assertIn('priority_gaps', skill_gap)
        self.assertGreater(len(skill_gap['priority_gaps']), 0)
        
        # Verify that all responses provide actionable insights
        self.assertGreater(initial_score, 0)
        self.assertIn('weaknesses', score_response.data)
        self.assertGreater(len(suggestions['improvement_recommendations']), 0)
        self.assertGreater(len(keyword_analysis['missing_keywords']), 0)
        self.assertLess(skill_gap['alignment_score'], 100)  # Should have room for improvement