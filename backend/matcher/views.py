from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q, Count, Avg
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from rest_framework import status, generics, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from .models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost,
    Application, AIAnalysisResult, InterviewSession, Skill, UserSkill,
    EmailVerificationToken, PasswordResetToken, JobAnalytics, JobView
)
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    JobSeekerProfileSerializer, RecruiterProfileSerializer, ResumeSerializer,
    JobPostSerializer, JobPostCreateSerializer, JobPostListSerializer, ApplicationSerializer, 
    AIAnalysisResultSerializer, InterviewSessionSerializer, SkillSerializer, UserSkillSerializer,
    JobMatchSerializer, EmailVerificationSerializer, EmailVerificationConfirmSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer, ChangePasswordSerializer,
    UserProfileUpdateSerializer, JobAnalyticsSerializer, JobViewSerializer
)
from .jwt_serializers import (
    CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer,
    JWTRegistrationSerializer, JWTLoginSerializer
)
from .permissions import (
    IsJobSeeker, IsRecruiter, IsOwnerOrReadOnly, IsJobSeekerOwner,
    IsRecruiterOwner, IsApplicationOwner, CustomJWTAuthentication
)
from .utils import (
    parse_resume, analyze_job_match, extract_skills_from_text,
    generate_interview_questions, calculate_match_score,
    generate_secure_token, send_verification_email, send_password_reset_email,
    send_welcome_email
)
from .services import GeminiResumeParser, FileValidator, GeminiAPIError


# JWT Authentication Views
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view with user role information
    """
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom JWT token refresh view
    """
    serializer_class = CustomTokenRefreshSerializer


class JWTRegisterView(generics.CreateAPIView):
    """
    JWT-based user registration view
    """
    queryset = User.objects.all()
    serializer_class = JWTRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create corresponding profile based on user type
            if user.user_type == 'job_seeker':
                JobSeekerProfile.objects.create(user=user)
            elif user.user_type == 'recruiter':
                RecruiterProfile.objects.create(
                    user=user,
                    company_name=request.data.get('company_name', '')
                )
            
            # Generate and send email verification token
            try:
                token = generate_secure_token()
                EmailVerificationToken.objects.create(user=user, token=token)
                send_verification_email(user, token)
            except Exception as e:
                logger.error(f"Error sending verification email during registration: {str(e)}")
            
            # Return JWT tokens and user data
            response_data = serializer.to_representation(user)
            response_data['verification_email_sent'] = True
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JWTLoginView(generics.GenericAPIView):
    """
    JWT-based user login view
    """
    serializer_class = JWTLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def jwt_logout_view(request):
    """
    JWT logout view - blacklists the refresh token
    """
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
            except TokenError as e:
                return Response({'error': f'Invalid token: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'Error during logout: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


# Legacy Token Authentication Views (for backward compatibility)
class RegisterView(generics.CreateAPIView):
    """
    Legacy token-based registration (deprecated - use JWTRegisterView)
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        # Redirect to JWT registration
        jwt_view = JWTRegisterView()
        jwt_view.request = request
        return jwt_view.create(request, *args, **kwargs)


class LoginView(generics.GenericAPIView):
    """
    Legacy token-based login (deprecated - use JWTLoginView)
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Redirect to JWT login
        jwt_view = JWTLoginView()
        jwt_view.request = request
        return jwt_view.post(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Legacy logout view (deprecated - use jwt_logout_view)
    """
    return jwt_logout_view(request)


# Profile Views
class JobSeekerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = JobSeekerProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'job_seeker':
            return JobSeekerProfile.objects.filter(user=self.request.user)
        return JobSeekerProfile.objects.none()
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class RecruiterProfileViewSet(viewsets.ModelViewSet):
    serializer_class = RecruiterProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'recruiter':
            return RecruiterProfile.objects.filter(user=self.request.user)
        return RecruiterProfile.objects.none()
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


# Resume Views
class ResumeViewSet(viewsets.ModelViewSet):
    serializer_class = ResumeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'job_seeker':
            return Resume.objects.filter(job_seeker=self.request.user)
        return Resume.objects.none()
    
    def perform_create(self, serializer):
        # Save the resume
        resume = serializer.save(
            job_seeker=self.request.user,
            original_filename=self.request.FILES['file'].name,
            file_size=self.request.FILES['file'].size
        )
        
        # Parse the resume using AI
        try:
            parsed_data = parse_resume(resume.file.path)
            resume.parsed_text = parsed_data.get('text', '')
            resume.save()
            
            # Extract skills and create AI analysis
            skills_data = extract_skills_from_text(resume.parsed_text)
            AIAnalysisResult.objects.create(
                resume=resume,
                analysis_type='resume_parse',
                input_data=resume.parsed_text,
                analysis_result=parsed_data,
                confidence_score=parsed_data.get('confidence', 0.0)
            )
            
        except Exception as e:
            print(f"Error parsing resume: {e}")
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        resume = self.get_object()
        # Set all other resumes as non-primary
        Resume.objects.filter(job_seeker=request.user).update(is_primary=False)
        # Set this resume as primary
        resume.is_primary = True
        resume.save()
        return Response({'message': 'Resume set as primary'})


# Job Match Score API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_match_score_view(request):
    """
    Calculate match score between a resume and job posting
    """
    resume_id = request.data.get('resume_id')
    job_id = request.data.get('job_id')
    
    if not resume_id or not job_id:
        return Response(
            {'error': 'Both resume_id and job_id are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get resume
        if request.user.user_type == 'job_seeker':
            resume = Resume.objects.get(id=resume_id, job_seeker=request.user)
        else:
            # Recruiters can calculate scores for any resume
            resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        return Response(
            {'error': 'Resume not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Get job post
        job_post = JobPost.objects.get(id=job_id, is_active=True)
    except JobPost.DoesNotExist:
        return Response(
            {'error': 'Job post not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        from .ml_services import get_ml_model, FeatureExtractor, MatchScoreCache
        
        # Check cache first
        cached_score = MatchScoreCache.get_cached_score(str(resume_id), str(job_id))
        if cached_score:
            logger.info(f"Returning cached match score for resume {resume_id} and job {job_id}")
            return Response(cached_score, status=status.HTTP_200_OK)
        
        # Extract features
        resume_features = FeatureExtractor.extract_resume_features({
            'parsed_text': resume.parsed_text,
            'skills': resume.job_seeker.job_seeker_profile.skills if hasattr(resume.job_seeker, 'job_seeker_profile') else '',
            'structured_data': None  # Will be populated from AI analysis if available
        })
        
        # Get structured data from latest AI analysis if available
        latest_analysis = AIAnalysisResult.objects.filter(
            resume=resume, 
            analysis_type='resume_parse'
        ).order_by('-processed_at').first()
        
        if latest_analysis and latest_analysis.analysis_result:
            resume_features['structured_data'] = latest_analysis.analysis_result
            resume_features = FeatureExtractor.extract_resume_features(resume_features)
        
        job_features = FeatureExtractor.extract_job_features({
            'title': job_post.title,
            'description': job_post.description,
            'requirements': job_post.requirements,
            'skills_required': job_post.skills_required,
            'experience_level': job_post.experience_level,
            'location': job_post.location,
            'remote_work_allowed': job_post.remote_work_allowed,
            'salary_min': job_post.salary_min,
            'salary_max': job_post.salary_max
        })
        
        # Calculate match score
        ml_model = get_ml_model()
        score_result = ml_model.calculate_match_score(resume_features, job_features)
        
        if not score_result['success']:
            return Response(
                {'error': 'Match score calculation failed', 'details': score_result.get('error', 'Unknown error')}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Prepare response
        response_data = {
            'success': True,
            'resume_id': str(resume_id),
            'job_id': str(job_id),
            'match_score': score_result['match_score'],
            'confidence': score_result['confidence'],
            'method': score_result['method'],
            'analysis': score_result['analysis'],
            'processing_time': score_result['processing_time'],
            'cached': False
        }
        
        # Cache the result
        MatchScoreCache.cache_score(str(resume_id), str(job_id), response_data)
        
        # Create AI analysis result for match score
        AIAnalysisResult.objects.create(
            resume=resume,
            job_post=job_post,
            analysis_type='job_match',
            input_data=f"Resume: {resume.original_filename}, Job: {job_post.title}",
            analysis_result={
                'match_score': score_result['match_score'],
                'analysis': score_result['analysis'],
                'method': score_result['method']
            },
            confidence_score=score_result['confidence'] / 100,  # Convert to 0-1 scale
            processing_time=score_result['processing_time']
        )
        
        logger.info(f"Match score calculated: {score_result['match_score']} for resume {resume_id} and job {job_id}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Unexpected error calculating match score: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_match_score_async_view(request):
    """
    Queue match score calculation as a background task
    """
    resume_id = request.data.get('resume_id')
    job_id = request.data.get('job_id')
    
    if not resume_id or not job_id:
        return Response(
            {'error': 'Both resume_id and job_id are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Verify resume exists and user has access
        if request.user.user_type == 'job_seeker':
            resume = Resume.objects.get(id=resume_id, job_seeker=request.user)
        else:
            resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        return Response(
            {'error': 'Resume not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Verify job post exists
        job_post = JobPost.objects.get(id=job_id, is_active=True)
    except JobPost.DoesNotExist:
        return Response(
            {'error': 'Job post not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        from .tasks import calculate_match_score_task
        
        # Queue the match score calculation task
        task = calculate_match_score_task.apply_async(args=[str(resume_id), str(job_id)])
        
        logger.info(f"Match score calculation task queued for resume {resume_id} and job {job_id}, task ID: {task.id}")
        
        return Response({
            'success': True,
            'task_id': task.id,
            'resume_id': str(resume_id),
            'job_id': str(job_id),
            'status': 'queued',
            'message': 'Match score calculation task has been queued'
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error queuing match score calculation task: {str(e)}")
        return Response(
            {'error': 'Failed to queue calculation task', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_calculate_match_scores_view(request):
    """
    Calculate match scores for multiple resume-job combinations
    """
    resume_ids = request.data.get('resume_ids', [])
    job_ids = request.data.get('job_ids', [])
    
    if not resume_ids or not job_ids:
        return Response(
            {'error': 'Both resume_ids and job_ids must be provided as non-empty lists'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not isinstance(resume_ids, list) or not isinstance(job_ids, list):
        return Response(
            {'error': 'resume_ids and job_ids must be lists'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify resumes exist and user has access
    try:
        if request.user.user_type == 'job_seeker':
            resumes = Resume.objects.filter(id__in=resume_ids, job_seeker=request.user)
        else:
            resumes = Resume.objects.filter(id__in=resume_ids)
        
        if len(resumes) != len(resume_ids):
            return Response(
                {'error': 'Some resumes not found or access denied'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {'error': 'Error validating resumes', 'details': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify job posts exist
    try:
        job_posts = JobPost.objects.filter(id__in=job_ids, is_active=True)
        if len(job_posts) != len(job_ids):
            return Response(
                {'error': 'Some job posts not found or inactive'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {'error': 'Error validating job posts', 'details': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from .tasks import batch_calculate_match_scores_task
        
        # Queue the batch calculation task
        task = batch_calculate_match_scores_task.apply_async(args=[resume_ids, job_ids])
        
        total_combinations = len(resume_ids) * len(job_ids)
        
        logger.info(f"Batch match score calculation task queued for {total_combinations} combinations, task ID: {task.id}")
        
        return Response({
            'success': True,
            'batch_task_id': task.id,
            'resume_count': len(resume_ids),
            'job_count': len(job_ids),
            'total_combinations': total_combinations,
            'status': 'queued',
            'message': f'Batch calculation task queued for {total_combinations} resume-job combinations'
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error queuing batch match score calculation task: {str(e)}")
        return Response(
            {'error': 'Failed to queue batch calculation task', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_match_scores_for_resume_view(request, resume_id):
    """
    Get all match scores for a specific resume
    """
    try:
        # Verify resume exists and user has access
        if request.user.user_type == 'job_seeker':
            resume = Resume.objects.get(id=resume_id, job_seeker=request.user)
        else:
            resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        return Response(
            {'error': 'Resume not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Get all match score analyses for this resume
        match_analyses = AIAnalysisResult.objects.filter(
            resume=resume,
            analysis_type='job_match'
        ).select_related('job_post').order_by('-processed_at')
        
        # Prepare response data
        match_scores = []
        for analysis in match_analyses:
            if analysis.job_post:
                match_data = {
                    'job_id': str(analysis.job_post.id),
                    'job_title': analysis.job_post.title,
                    'company': analysis.job_post.recruiter.recruiter_profile.company_name if hasattr(analysis.job_post.recruiter, 'recruiter_profile') else 'Unknown',
                    'match_score': analysis.analysis_result.get('match_score', 0),
                    'confidence': analysis.confidence_score * 100,  # Convert to percentage
                    'analysis': analysis.analysis_result.get('analysis', {}),
                    'method': analysis.analysis_result.get('method', 'unknown'),
                    'calculated_at': analysis.processed_at.isoformat(),
                    'processing_time': analysis.processing_time
                }
                match_scores.append(match_data)
        
        # Sort by match score descending
        match_scores.sort(key=lambda x: x['match_score'], reverse=True)
        
        return Response({
            'success': True,
            'resume_id': str(resume_id),
            'resume_filename': resume.original_filename,
            'total_matches': len(match_scores),
            'match_scores': match_scores
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting match scores for resume {resume_id}: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_match_scores_for_job_view(request, job_id):
    """
    Get all match scores for a specific job posting (recruiter only)
    """
    if request.user.user_type != 'recruiter':
        return Response(
            {'error': 'Only recruiters can view job match scores'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Verify job post exists and belongs to recruiter
        job_post = JobPost.objects.get(id=job_id, recruiter=request.user)
    except JobPost.DoesNotExist:
        return Response(
            {'error': 'Job post not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Get all match score analyses for this job
        match_analyses = AIAnalysisResult.objects.filter(
            job_post=job_post,
            analysis_type='job_match'
        ).select_related('resume', 'resume__job_seeker').order_by('-processed_at')
        
        # Prepare response data
        match_scores = []
        for analysis in match_analyses:
            if analysis.resume:
                match_data = {
                    'resume_id': str(analysis.resume.id),
                    'candidate_name': analysis.resume.job_seeker.get_full_name() or analysis.resume.job_seeker.username,
                    'resume_filename': analysis.resume.original_filename,
                    'match_score': analysis.analysis_result.get('match_score', 0),
                    'confidence': analysis.confidence_score * 100,  # Convert to percentage
                    'analysis': analysis.analysis_result.get('analysis', {}),
                    'method': analysis.analysis_result.get('method', 'unknown'),
                    'calculated_at': analysis.processed_at.isoformat(),
                    'processing_time': analysis.processing_time
                }
                match_scores.append(match_data)
        
        # Sort by match score descending
        match_scores.sort(key=lambda x: x['match_score'], reverse=True)
        
        return Response({
            'success': True,
            'job_id': str(job_id),
            'job_title': job_post.title,
            'total_candidates': len(match_scores),
            'match_scores': match_scores
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting match scores for job {job_id}: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Resume Parsing API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def parse_resume_view(request):
    """
    Parse resume using Google Gemini API
    Supports PDF, DOCX, and TXT file formats
    """
    if request.user.user_type != 'job_seeker':
        return Response(
            {'error': 'Only job seekers can parse resumes'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = request.FILES['file']
    
    try:
        # Validate file
        validation_result = FileValidator.validate_file(uploaded_file)
        if not validation_result['is_valid']:
            return Response(
                {'error': 'File validation failed', 'details': validation_result['errors']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize Gemini parser
        try:
            parser = GeminiResumeParser()
        except GeminiAPIError as e:
            logger.error(f"Gemini API initialization error: {str(e)}")
            return Response(
                {'error': 'AI service temporarily unavailable', 'details': str(e)}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Read file content
        uploaded_file.seek(0)
        file_content = uploaded_file.read()
        
        # Create temporary file path for processing
        sanitized_filename = FileValidator.sanitize_filename(uploaded_file.name)
        temp_file_path = f"/tmp/{sanitized_filename}"
        
        # Parse resume
        try:
            parsing_result = parser.parse_resume(temp_file_path, file_content)
        except GeminiAPIError as e:
            logger.error(f"Resume parsing error: {str(e)}")
            return Response(
                {'error': 'Resume parsing failed', 'details': str(e)}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        if not parsing_result['success']:
            return Response(
                {'error': 'Resume parsing failed', 'details': parsing_result.get('error', 'Unknown error')}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update resume record if requested
        save_resume = request.data.get('save_resume', 'false').lower() == 'true'
        resume_id = None
        
        if save_resume:
            try:
                # Save the file
                resume = Resume.objects.create(
                    job_seeker=request.user,
                    file=uploaded_file,
                    original_filename=uploaded_file.name,
                    file_size=uploaded_file.size,
                    parsed_text=parsing_result['parsed_text']
                )
                resume_id = str(resume.id)
                
                # Create AI analysis result
                AIAnalysisResult.objects.create(
                    resume=resume,
                    analysis_type='resume_parse',
                    input_data=parsing_result['parsed_text'][:1000],  # Truncate for storage
                    analysis_result=parsing_result['structured_data'],
                    confidence_score=parsing_result['confidence_score'],
                    processing_time=parsing_result['processing_time']
                )
                
                logger.info(f"Resume parsed and saved for user {request.user.username}")
                
            except Exception as e:
                logger.error(f"Error saving resume: {str(e)}")
                # Continue without saving if there's an error
        
        # Prepare response
        response_data = {
            'success': True,
            'parsed_text': parsing_result['parsed_text'],
            'structured_data': parsing_result['structured_data'],
            'confidence_score': parsing_result['confidence_score'],
            'processing_time': parsing_result['processing_time'],
            'file_info': {
                'original_filename': uploaded_file.name,
                'file_size': uploaded_file.size,
                'file_type': validation_result['file_extension']
            }
        }
        
        if resume_id:
            response_data['resume_id'] = resume_id
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Unexpected error in resume parsing: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def parse_resume_by_id_view(request, resume_id):
    """
    Re-parse an existing resume by ID using Google Gemini API
    """
    if request.user.user_type != 'job_seeker':
        return Response(
            {'error': 'Only job seekers can parse resumes'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        resume = Resume.objects.get(id=resume_id, job_seeker=request.user)
    except Resume.DoesNotExist:
        return Response(
            {'error': 'Resume not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Initialize Gemini parser
        try:
            parser = GeminiResumeParser()
        except GeminiAPIError as e:
            logger.error(f"Gemini API initialization error: {str(e)}")
            return Response(
                {'error': 'AI service temporarily unavailable', 'details': str(e)}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Parse resume
        try:
            parsing_result = parser.parse_resume(resume.file.path)
        except GeminiAPIError as e:
            logger.error(f"Resume parsing error: {str(e)}")
            return Response(
                {'error': 'Resume parsing failed', 'details': str(e)}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        if not parsing_result['success']:
            return Response(
                {'error': 'Resume parsing failed', 'details': parsing_result.get('error', 'Unknown error')}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update resume with new parsed data
        resume.parsed_text = parsing_result['parsed_text']
        resume.save()
        
        # Create new AI analysis result
        AIAnalysisResult.objects.create(
            resume=resume,
            analysis_type='resume_parse',
            input_data=parsing_result['parsed_text'][:1000],  # Truncate for storage
            analysis_result=parsing_result['structured_data'],
            confidence_score=parsing_result['confidence_score'],
            processing_time=parsing_result['processing_time']
        )
        
        logger.info(f"Resume {resume_id} re-parsed for user {request.user.username}")
        
        # Prepare response
        response_data = {
            'success': True,
            'resume_id': str(resume.id),
            'parsed_text': parsing_result['parsed_text'],
            'structured_data': parsing_result['structured_data'],
            'confidence_score': parsing_result['confidence_score'],
            'processing_time': parsing_result['processing_time'],
            'file_info': {
                'original_filename': resume.original_filename,
                'file_size': resume.file_size,
                'uploaded_at': resume.uploaded_at.isoformat()
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Unexpected error in resume re-parsing: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def parse_resume_async_view(request):
    """
    Queue resume parsing as a background task
    """
    if request.user.user_type != 'job_seeker':
        return Response(
            {'error': 'Only job seekers can parse resumes'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    resume_id = request.data.get('resume_id')
    if not resume_id:
        return Response(
            {'error': 'resume_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Verify resume exists and belongs to user
        resume = Resume.objects.get(id=resume_id, job_seeker=request.user)
    except Resume.DoesNotExist:
        return Response(
            {'error': 'Resume not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        from .tasks import parse_resume_task
        
        # Queue the parsing task
        task = parse_resume_task.apply_async(args=[str(resume_id)])
        
        logger.info(f"Resume parsing task queued for resume {resume_id}, task ID: {task.id}")
        
        return Response({
            'success': True,
            'task_id': task.id,
            'resume_id': str(resume_id),
            'status': 'queued',
            'message': 'Resume parsing task has been queued'
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error queuing resume parsing task: {str(e)}")
        return Response(
            {'error': 'Failed to queue parsing task', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parse_task_status_view(request, task_id):
    """
    Check the status of a resume parsing task
    """
    try:
        from celery.result import AsyncResult
        
        # Get task result
        task_result = AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response_data = {
                'task_id': task_id,
                'status': 'pending',
                'message': 'Task is waiting to be processed'
            }
        elif task_result.state == 'PROGRESS':
            response_data = {
                'task_id': task_id,
                'status': 'in_progress',
                'message': 'Task is being processed',
                'progress': task_result.info
            }
        elif task_result.state == 'SUCCESS':
            response_data = {
                'task_id': task_id,
                'status': 'completed',
                'result': task_result.result
            }
        elif task_result.state == 'FAILURE':
            response_data = {
                'task_id': task_id,
                'status': 'failed',
                'error': str(task_result.info)
            }
        else:
            response_data = {
                'task_id': task_id,
                'status': task_result.state.lower(),
                'info': str(task_result.info) if task_result.info else None
            }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking task status for {task_id}: {str(e)}")
        return Response(
            {'error': 'Failed to check task status', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_parse_resumes_view(request):
    """
    Queue multiple resumes for parsing as background tasks
    """
    if request.user.user_type != 'job_seeker':
        return Response(
            {'error': 'Only job seekers can parse resumes'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    resume_ids = request.data.get('resume_ids', [])
    if not resume_ids or not isinstance(resume_ids, list):
        return Response(
            {'error': 'resume_ids must be a non-empty list'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify all resumes exist and belong to user
    try:
        resumes = Resume.objects.filter(id__in=resume_ids, job_seeker=request.user)
        if len(resumes) != len(resume_ids):
            return Response(
                {'error': 'Some resumes not found or do not belong to you'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {'error': 'Error validating resumes', 'details': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from .tasks import batch_parse_resumes_task
        
        # Queue the batch parsing task
        task = batch_parse_resumes_task.apply_async(args=[resume_ids])
        
        logger.info(f"Batch resume parsing task queued for {len(resume_ids)} resumes, task ID: {task.id}")
        
        return Response({
            'success': True,
            'batch_task_id': task.id,
            'resume_count': len(resume_ids),
            'status': 'queued',
            'message': f'Batch parsing task queued for {len(resume_ids)} resumes'
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error queuing batch resume parsing task: {str(e)}")
        return Response(
            {'error': 'Failed to queue batch parsing task', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Job Post Views
class JobPostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return JobPostListSerializer
        elif self.action == 'create':
            return JobPostCreateSerializer
        return JobPostSerializer
    
    def get_queryset(self):
        """Enhanced queryset with advanced filtering and search"""
        queryset = JobPost.objects.select_related(
            'recruiter', 'recruiter__recruiter_profile'
        ).prefetch_related('applications')
        
        # Base filtering - only active jobs for non-owners
        if self.request.user.user_type != 'recruiter' or self.action == 'list':
            queryset = queryset.filter(is_active=True)
        
        # Recruiter can only modify their own jobs
        if self.request.user.user_type == 'recruiter':
            if self.action in ['update', 'partial_update', 'destroy']:
                queryset = queryset.filter(recruiter=self.request.user)
            elif self.action == 'list' and self.request.query_params.get('my_jobs') == 'true':
                # For my_jobs, show all jobs (active and inactive) for the recruiter
                queryset = JobPost.objects.select_related(
                    'recruiter', 'recruiter__recruiter_profile'
                ).prefetch_related('applications').filter(recruiter=self.request.user)
        
        # Advanced search functionality
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(skills_required__icontains=search) |
                Q(location__icontains=search) |
                Q(recruiter__recruiter_profile__company_name__icontains=search)
            )
        
        # Filter by job type
        job_type = self.request.query_params.get('job_type')
        if job_type:
            job_types = job_type.split(',')
            queryset = queryset.filter(job_type__in=job_types)
        
        # Filter by experience level
        experience_level = self.request.query_params.get('experience_level')
        if experience_level:
            experience_levels = experience_level.split(',')
            queryset = queryset.filter(experience_level__in=experience_levels)
        
        # Location filtering with fuzzy matching
        location = self.request.query_params.get('location', '').strip()
        if location:
            # Only include remote jobs if specifically searching for "remote"
            if location.lower() in ['remote', 'anywhere']:
                queryset = queryset.filter(
                    Q(location__icontains=location) |
                    Q(remote_work_allowed=True)
                )
            else:
                queryset = queryset.filter(location__icontains=location)
        
        # Salary range filtering
        salary_min = self.request.query_params.get('salary_min')
        salary_max = self.request.query_params.get('salary_max')
        if salary_min:
            try:
                salary_min = int(salary_min)
                # Jobs where the max salary is at least the requested minimum
                queryset = queryset.filter(
                    Q(salary_max__gte=salary_min) | Q(salary_max__isnull=True)
                )
            except ValueError:
                pass
        
        if salary_max:
            try:
                salary_max = int(salary_max)
                # Jobs where the min salary is at most the requested maximum
                queryset = queryset.filter(
                    Q(salary_min__lte=salary_max) | Q(salary_min__isnull=True)
                )
            except ValueError:
                pass
        
        # Skills filtering
        skills = self.request.query_params.get('skills', '').strip()
        if skills:
            skill_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
            for skill in skill_list:
                queryset = queryset.filter(skills_required__icontains=skill)
        
        # Remote work filter
        remote_only = self.request.query_params.get('remote_only')
        if remote_only and remote_only.lower() == 'true':
            queryset = queryset.filter(remote_work_allowed=True)
        
        # Featured jobs filter
        featured_only = self.request.query_params.get('featured_only')
        if featured_only and featured_only.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            try:
                from datetime import datetime
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                from datetime import datetime
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        # Sorting
        ordering = self.request.query_params.get('ordering', '-created_at')
        valid_orderings = [
            'created_at', '-created_at', 'title', '-title', 'salary_min', '-salary_min',
            'salary_max', '-salary_max', 'views_count', '-views_count', 'applications_count', '-applications_count'
        ]
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, IsRecruiter]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsRecruiterOwner]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Create job post with analytics initialization"""
        job_post = serializer.save(recruiter=self.request.user)
        
        # Create analytics record
        JobAnalytics.objects.create(job_post=job_post)
    
    def retrieve(self, request, *args, **kwargs):
        """Enhanced retrieve with view tracking and analytics"""
        instance = self.get_object()
        
        # Track job view
        self._track_job_view(instance, request)
        
        # Increment view count atomically
        instance.increment_view_count()
        
        # Update analytics
        self._update_job_analytics(instance, request)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def _track_job_view(self, job_post, request):
        """Track individual job view"""
        try:
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
            
            # Create job view record
            JobView.objects.create(
                job_post=job_post,
                viewer=request.user if request.user.is_authenticated else None,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referrer=request.META.get('HTTP_REFERER', ''),
                session_id=request.session.session_key or ''
            )
        except Exception as e:
            logger.error(f"Error tracking job view: {str(e)}")
    
    def _update_job_analytics(self, job_post, request):
        """Update job analytics"""
        try:
            analytics, created = JobAnalytics.objects.get_or_create(job_post=job_post)
            
            # Update view counts
            analytics.total_views = job_post.views_count
            analytics.unique_views = JobView.objects.filter(job_post=job_post).values('ip_address').distinct().count()
            analytics.total_applications = job_post.applications.count()
            
            # Update conversion rate
            analytics.update_conversion_rate()
            
            # Update geographic distribution
            location_data = JobView.objects.filter(job_post=job_post).values_list('ip_address', flat=True)
            # In a real implementation, you'd use a GeoIP service to get locations
            
            analytics.save()
        except Exception as e:
            logger.error(f"Error updating job analytics: {str(e)}")
    
    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """Get applications for a job post (recruiter only)"""
        job_post = self.get_object()
        if job_post.recruiter != request.user:
            raise PermissionDenied("Access denied")
        
        applications = Application.objects.filter(job_post=job_post).select_related(
            'job_seeker', 'resume'
        ).order_by('-match_score', '-applied_at')
        
        # Pagination
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(applications, request)
        
        if page is not None:
            serializer = ApplicationSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for a job post (recruiter only)"""
        job_post = self.get_object()
        if job_post.recruiter != request.user:
            raise PermissionDenied("Access denied")
        
        try:
            analytics = job_post.analytics
            serializer = JobAnalyticsSerializer(analytics)
            
            # Add additional analytics data
            data = serializer.data
            data['recent_views'] = JobView.objects.filter(
                job_post=job_post,
                viewed_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            data['top_skills_searched'] = self._get_top_skills_for_job(job_post)
            
            return Response(data)
        except JobAnalytics.DoesNotExist:
            return Response({'error': 'Analytics not available'}, status=404)
    
    def _get_top_skills_for_job(self, job_post):
        """Get top skills that led to this job being viewed"""
        # This is a simplified implementation
        # In practice, you'd track search queries that led to job views
        skills = job_post.skills_required.split(',') if job_post.skills_required else []
        return [skill.strip() for skill in skills[:5]]
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle job post active status (recruiter only)"""
        job_post = self.get_object()
        if job_post.recruiter != request.user:
            raise PermissionDenied("Access denied")
        
        job_post.is_active = not job_post.is_active
        job_post.save(update_fields=['is_active'])
        
        return Response({
            'message': f'Job post {"activated" if job_post.is_active else "deactivated"}',
            'is_active': job_post.is_active
        })
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a job post (recruiter only)"""
        job_post = self.get_object()
        if job_post.recruiter != request.user:
            raise PermissionDenied("Access denied")
        
        # Create a copy
        job_post.pk = None
        job_post.title = f"{job_post.title} (Copy)"
        job_post.is_active = False  # Start as inactive
        job_post.views_count = 0
        job_post.applications_count = 0
        job_post.slug = ''  # Will be regenerated on save
        job_post.save()
        
        # Create analytics for the new job
        JobAnalytics.objects.create(job_post=job_post)
        
        serializer = self.get_serializer(job_post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def search_suggestions(self, request):
        """Get search suggestions based on existing job data"""
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        # Get title suggestions
        title_suggestions = JobPost.objects.filter(
            title__icontains=query, is_active=True
        ).values_list('title', flat=True).distinct()[:5]
        
        # Get location suggestions
        location_suggestions = JobPost.objects.filter(
            location__icontains=query, is_active=True
        ).values_list('location', flat=True).distinct()[:5]
        
        # Get company suggestions
        company_suggestions = JobPost.objects.filter(
            recruiter__recruiter_profile__company_name__icontains=query, is_active=True
        ).values_list('recruiter__recruiter_profile__company_name', flat=True).distinct()[:5]
        
        suggestions = {
            'titles': list(title_suggestions),
            'locations': list(location_suggestions),
            'companies': list(company_suggestions)
        }
        
        return Response({'suggestions': suggestions})


# Application Views
class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Enhanced queryset with filtering and search capabilities"""
        if self.request.user.user_type == 'job_seeker':
            queryset = Application.objects.filter(job_seeker=self.request.user)
        elif self.request.user.user_type == 'recruiter':
            queryset = Application.objects.filter(job_post__recruiter=self.request.user)
        else:
            return Application.objects.none()
        
        # Add select_related and prefetch_related for performance
        queryset = queryset.select_related(
            'job_seeker', 'job_post', 'resume', 'job_post__recruiter'
        ).prefetch_related('ai_analyses')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            status_list = status_filter.split(',')
            queryset = queryset.filter(status__in=status_list)
        
        # Filter by job post
        job_post_id = self.request.query_params.get('job_post')
        if job_post_id:
            queryset = queryset.filter(job_post_id=job_post_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            try:
                from datetime import datetime
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(applied_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                from datetime import datetime
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(applied_at__date__lte=date_to)
            except ValueError:
                pass
        
        # Search functionality
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(job_post__title__icontains=search) |
                Q(job_post__recruiter__recruiter_profile__company_name__icontains=search) |
                Q(cover_letter__icontains=search)
            )
        
        # Sorting
        ordering = self.request.query_params.get('ordering', '-applied_at')
        valid_orderings = [
            'applied_at', '-applied_at', 'status', '-status', 
            'match_score', '-match_score', 'updated_at', '-updated_at'
        ]
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-applied_at')
        
        return queryset
    
    def perform_create(self, serializer):
        """Enhanced application creation with validation and analytics"""
        if self.request.user.user_type != 'job_seeker':
            raise PermissionDenied("Only job seekers can apply for jobs")
        
        job_post = serializer.validated_data['job_post']
        
        # Check if user already applied to this job
        existing_application = Application.objects.filter(
            job_seeker=self.request.user,
            job_post=job_post
        ).first()
        
        if existing_application:
            raise ValidationError("You have already applied to this job")
        
        # Check if job is still active and not expired
        if not job_post.is_active:
            raise ValidationError("This job posting is no longer active")
        
        if job_post.is_expired:
            raise ValidationError("The application deadline for this job has passed")
        
        # Get primary resume or first resume
        resume = Resume.objects.filter(
            job_seeker=self.request.user, is_primary=True
        ).first()
        if not resume:
            resume = Resume.objects.filter(job_seeker=self.request.user).first()
        
        if not resume:
            raise ValidationError("Please upload a resume first")
        
        # Calculate match score
        match_score = calculate_match_score(resume, job_post)
        
        application = serializer.save(
            job_seeker=self.request.user,
            resume=resume,
            match_score=match_score
        )
        
        # Update job post applications count
        job_post.update_applications_count()
        
        # Create AI analysis for job matching
        try:
            match_analysis = analyze_job_match(resume, job_post)
            AIAnalysisResult.objects.create(
                resume=resume,
                job_post=job_post,
                application=application,
                analysis_type='job_match',
                input_data=f"Resume vs Job: {job_post.title}",
                analysis_result=match_analysis,
                confidence_score=match_score
            )
        except Exception as e:
            logger.error(f"Error analyzing job match: {e}")
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update application status (recruiter only)"""
        application = self.get_object()
        if application.job_post.recruiter != request.user:
            raise PermissionDenied("Access denied")
        
        new_status = request.data.get('status')
        recruiter_notes = request.data.get('recruiter_notes', '')
        
        if new_status not in dict(Application.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = application.status
        application.status = new_status
        if recruiter_notes:
            application.recruiter_notes = recruiter_notes
        application.save()
        
        # Log status change for analytics
        logger.info(f"Application {application.id} status changed from {old_status} to {new_status} by {request.user.username}")
        
        return Response(ApplicationSerializer(application).data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get application history for job seekers"""
        if request.user.user_type != 'job_seeker':
            raise PermissionDenied("Only job seekers can view application history")
        
        # Get applications with status timeline
        applications = self.get_queryset()
        
        # Group by status for summary
        from django.db.models import Count
        status_summary = applications.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Get recent applications (last 30 days)
        recent_applications = applications.filter(
            applied_at__gte=timezone.now() - timedelta(days=30)
        )
        
        # Pagination for all applications
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(applications, request)
        
        if page is not None:
            serializer = ApplicationSerializer(page, many=True)
            return paginator.get_paginated_response({
                'applications': serializer.data,
                'status_summary': list(status_summary),
                'recent_count': recent_applications.count(),
                'total_count': applications.count()
            })
        
        serializer = ApplicationSerializer(applications, many=True)
        return Response({
            'applications': serializer.data,
            'status_summary': list(status_summary),
            'recent_count': recent_applications.count(),
            'total_count': applications.count()
        })
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get application analytics for recruiters"""
        if request.user.user_type != 'recruiter':
            raise PermissionDenied("Only recruiters can view application analytics")
        
        applications = self.get_queryset()
        
        # Overall statistics
        total_applications = applications.count()
        
        # Status distribution
        from django.db.models import Count
        status_distribution = applications.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Applications over time (last 30 days)
        from django.db.models import TruncDate
        applications_over_time = applications.filter(
            applied_at__gte=timezone.now() - timedelta(days=30)
        ).extra(
            select={'day': 'date(applied_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Top performing jobs (by application count)
        top_jobs = applications.values(
            'job_post__title', 'job_post__id'
        ).annotate(
            application_count=Count('id')
        ).order_by('-application_count')[:10]
        
        # Average match scores
        from django.db.models import Avg
        avg_match_score = applications.aggregate(
            avg_score=Avg('match_score')
        )['avg_score'] or 0
        
        # Match score distribution
        match_score_ranges = [
            ('0-20', applications.filter(match_score__lt=0.2).count()),
            ('20-40', applications.filter(match_score__gte=0.2, match_score__lt=0.4).count()),
            ('40-60', applications.filter(match_score__gte=0.4, match_score__lt=0.6).count()),
            ('60-80', applications.filter(match_score__gte=0.6, match_score__lt=0.8).count()),
            ('80-100', applications.filter(match_score__gte=0.8).count()),
        ]
        
        # Response time analytics (time from application to first status change)
        response_times = []
        for app in applications.exclude(status='pending'):
            if app.updated_at and app.applied_at:
                response_time = (app.updated_at - app.applied_at).total_seconds() / 3600  # in hours
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return Response({
            'total_applications': total_applications,
            'status_distribution': list(status_distribution),
            'applications_over_time': list(applications_over_time),
            'top_jobs': list(top_jobs),
            'average_match_score': round(avg_match_score, 2),
            'match_score_distribution': match_score_ranges,
            'average_response_time_hours': round(avg_response_time, 2),
            'total_response_times': len(response_times)
        })
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get application timeline/history"""
        application = self.get_object()
        
        # Build timeline from application data
        timeline = [
            {
                'event': 'Application Submitted',
                'timestamp': application.applied_at,
                'status': 'pending',
                'description': f'Applied to {application.job_post.title}',
                'actor': application.job_seeker.username
            }
        ]
        
        # Add status changes (this would be enhanced with a proper audit log)
        if application.status != 'pending':
            timeline.append({
                'event': 'Status Updated',
                'timestamp': application.updated_at,
                'status': application.status,
                'description': f'Status changed to {application.get_status_display()}',
                'actor': application.job_post.recruiter.username,
                'notes': application.recruiter_notes
            })
        
        # Add AI analysis results
        for analysis in application.ai_analyses.all():
            timeline.append({
                'event': 'AI Analysis Completed',
                'timestamp': analysis.processed_at,
                'status': 'analysis',
                'description': f'{analysis.get_analysis_type_display()} completed',
                'confidence_score': analysis.confidence_score
            })
        
        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        return Response({
            'application_id': application.id,
            'timeline': timeline
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export applications data (CSV format)"""
        import csv
        from django.http import HttpResponse
        
        applications = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="applications.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Application ID', 'Job Title', 'Company', 'Applicant', 'Status',
            'Applied Date', 'Match Score', 'Cover Letter Preview'
        ])
        
        for app in applications:
            writer.writerow([
                str(app.id),
                app.job_post.title,
                app.job_post.recruiter.recruiter_profile.company_name,
                app.job_seeker.username,
                app.get_status_display(),
                app.applied_at.strftime('%Y-%m-%d %H:%M'),
                f"{app.match_score:.2f}",
                app.cover_letter[:100] + '...' if len(app.cover_letter) > 100 else app.cover_letter
            ])
        
        return response


# AI-powered Job Matching
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_recommendations(request):
    """Get AI-powered job recommendations for job seekers"""
    if request.user.user_type != 'job_seeker':
        return Response({'error': 'Only job seekers can get recommendations'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    # Get user's primary resume
    resume = Resume.objects.filter(
        job_seeker=request.user, is_primary=True
    ).first()
    
    if not resume:
        return Response({'error': 'Please upload a resume first'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Get active job posts
    job_posts = JobPost.objects.filter(is_active=True)
    recommendations = []
    
    for job_post in job_posts:
        match_score = calculate_match_score(resume, job_post)
        if match_score > 0.3:  # Only include jobs with >30% match
            try:
                match_analysis = analyze_job_match(resume, job_post)
                recommendations.append({
                    'job_post': JobPostSerializer(job_post).data,
                    'match_score': match_score,
                    'matching_skills': match_analysis.get('matching_skills', []),
                    'missing_skills': match_analysis.get('missing_skills', []),
                    'recommendations': match_analysis.get('recommendations', '')
                })
            except:
                recommendations.append({
                    'job_post': JobPostSerializer(job_post).data,
                    'match_score': match_score,
                    'matching_skills': [],
                    'missing_skills': [],
                    'recommendations': 'AI analysis temporarily unavailable'
                })
    
    # Sort by match score
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    
    return Response(recommendations[:20])  # Return top 20 matches


# Interview Management
class InterviewSessionViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'job_seeker':
            return InterviewSession.objects.filter(
                application__job_seeker=self.request.user
            )
        elif self.request.user.user_type == 'recruiter':
            return InterviewSession.objects.filter(
                application__job_post__recruiter=self.request.user
            )
        return InterviewSession.objects.none()
    
    @action(detail=True, methods=['post'])
    def generate_questions(self, request, pk=None):
        interview = self.get_object()
        if (interview.application.job_post.recruiter != request.user and 
            interview.application.job_seeker != request.user):
            raise PermissionDenied("Access denied")
        
        try:
            questions = generate_interview_questions(
                interview.application.job_post,
                interview.interview_type
            )
            return Response({'questions': questions})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Dashboard Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics based on user type"""
    if request.user.user_type == 'job_seeker':
        stats = {
            'total_applications': Application.objects.filter(job_seeker=request.user).count(),
            'pending_applications': Application.objects.filter(
                job_seeker=request.user, status='pending'
            ).count(),
            'shortlisted_applications': Application.objects.filter(
                job_seeker=request.user, status='shortlisted'
            ).count(),
            'interviews_scheduled': InterviewSession.objects.filter(
                application__job_seeker=request.user, status='scheduled'
            ).count(),
            'profile_completion': calculate_profile_completion(request.user),
        }
    elif request.user.user_type == 'recruiter':
        stats = {
            'total_job_posts': JobPost.objects.filter(recruiter=request.user).count(),
            'active_job_posts': JobPost.objects.filter(
                recruiter=request.user, is_active=True
            ).count(),
            'total_applications': Application.objects.filter(
                job_post__recruiter=request.user
            ).count(),
            'pending_applications': Application.objects.filter(
                job_post__recruiter=request.user, status='pending'
            ).count(),
            'interviews_scheduled': InterviewSession.objects.filter(
                application__job_post__recruiter=request.user, status='scheduled'
            ).count(),
        }
    else:
        stats = {}
    
    return Response(stats)


# Utility Functions
def calculate_profile_completion(user):
    """Calculate profile completion percentage"""
    if user.user_type == 'job_seeker':
        try:
            profile = user.job_seeker_profile
            fields = [
                profile.date_of_birth, profile.location, profile.experience_level,
                profile.current_position, profile.skills, profile.bio
            ]
            completed = sum(1 for field in fields if field)
            return int((completed / len(fields)) * 100)
        except:
            return 0
    elif user.user_type == 'recruiter':
        try:
            profile = user.recruiter_profile
            fields = [
                profile.company_name, profile.company_website,
                profile.industry, profile.company_description, profile.location
            ]
            completed = sum(1 for field in fields if field)
            return int((completed / len(fields)) * 100)
        except:
            return 0
    return 0


# Skills Management
class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Skill.objects.all()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class UserSkillViewSet(viewsets.ModelViewSet):
    serializer_class = UserSkillSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Email Verification Views
@api_view(['POST'])
@permission_classes([AllowAny])
def request_email_verification(request):
    """
    Request email verification for a user
    """
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate verification token
        token = generate_secure_token()
        
        # Create or update verification token
        EmailVerificationToken.objects.filter(user=user, is_used=False).delete()
        EmailVerificationToken.objects.create(user=user, token=token)
        
        # Send verification email
        if send_verification_email(user, token):
            return Response({
                'message': 'Verification email sent successfully',
                'email': email
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to send verification email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify email using verification token
    """
    serializer = EmailVerificationConfirmSerializer(data=request.data)
    if serializer.is_valid():
        token = serializer.validated_data['token']
        
        try:
            verification_token = EmailVerificationToken.objects.get(token=token, is_used=False)
            
            if verification_token.is_expired():
                return Response({
                    'error': 'Verification token has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark user as verified
            user = verification_token.user
            user.is_verified = True
            user.save()
            
            # Mark token as used
            verification_token.is_used = True
            verification_token.save()
            
            # Send welcome email
            send_welcome_email(user)
            
            return Response({
                'message': 'Email verified successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        except EmailVerificationToken.DoesNotExist:
            return Response({
                'error': 'Invalid verification token'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Password Reset Views
@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    Request password reset for a user
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email, is_active=True)
        
        # Generate reset token
        token = generate_secure_token()
        
        # Create or update reset token
        PasswordResetToken.objects.filter(user=user, is_used=False).delete()
        PasswordResetToken.objects.create(user=user, token=token)
        
        # Send reset email
        if send_password_reset_email(user, token):
            return Response({
                'message': 'Password reset email sent successfully',
                'email': email
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to send password reset email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Reset password using reset token
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
            
            if reset_token.is_expired():
                return Response({
                    'error': 'Reset token has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Reset user password
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            return Response({
                'message': 'Password reset successfully'
            }, status=status.HTTP_200_OK)
            
        except PasswordResetToken.DoesNotExist:
            return Response({
                'error': 'Invalid reset token'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# User Profile Management Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change password for authenticated user
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        new_password = serializer.validated_data['new_password']
        
        # Change user password
        user = request.user
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get or update user profile information
    """
    user = request.user
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = UserProfileUpdateSerializer(
            user, 
            data=request.data, 
            partial=(request.method == 'PATCH')
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """
    Delete user account (soft delete by deactivating)
    """
    user = request.user
    
    # Soft delete by deactivating the account
    user.is_active = False
    user.save()
    
    return Response({
        'message': 'Account deactivated successfully'
    }, status=status.HTTP_200_OK)
