from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q, Count, Avg
from django.conf import settings

from rest_framework import status, generics, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
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
    EmailVerificationToken, PasswordResetToken
)
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    JobSeekerProfileSerializer, RecruiterProfileSerializer, ResumeSerializer,
    JobPostSerializer, ApplicationSerializer, AIAnalysisResultSerializer,
    InterviewSessionSerializer, SkillSerializer, UserSkillSerializer,
    JobMatchSerializer, EmailVerificationSerializer, EmailVerificationConfirmSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer, ChangePasswordSerializer,
    UserProfileUpdateSerializer
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


# Job Post Views
class JobPostViewSet(viewsets.ModelViewSet):
    serializer_class = JobPostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = JobPost.objects.filter(is_active=True)
        
        # Filter by user type
        if self.request.user.user_type == 'recruiter':
            if self.action in ['update', 'partial_update', 'destroy']:
                queryset = queryset.filter(recruiter=self.request.user)
        
        # Search and filter functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(skills_required__icontains=search) |
                Q(location__icontains=search)
            )
        
        job_type = self.request.query_params.get('job_type', None)
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
        experience_level = self.request.query_params.get('experience_level', None)
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)
        
        location = self.request.query_params.get('location', None)
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        if self.request.user.user_type != 'recruiter':
            raise permissions.PermissionDenied("Only recruiters can create job posts")
        serializer.save(recruiter=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.views_count += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        job_post = self.get_object()
        if job_post.recruiter != request.user:
            raise permissions.PermissionDenied("Access denied")
        
        applications = Application.objects.filter(job_post=job_post).order_by('-match_score')
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data)


# Application Views
class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'job_seeker':
            return Application.objects.filter(job_seeker=self.request.user)
        elif self.request.user.user_type == 'recruiter':
            return Application.objects.filter(job_post__recruiter=self.request.user)
        return Application.objects.none()
    
    def perform_create(self, serializer):
        if self.request.user.user_type != 'job_seeker':
            raise permissions.PermissionDenied("Only job seekers can apply for jobs")
        
        # Get primary resume or first resume
        resume = Resume.objects.filter(
            job_seeker=self.request.user, is_primary=True
        ).first()
        if not resume:
            resume = Resume.objects.filter(job_seeker=self.request.user).first()
        
        if not resume:
            raise serializers.ValidationError("Please upload a resume first")
        
        # Calculate match score
        job_post = serializer.validated_data['job_post']
        match_score = calculate_match_score(resume, job_post)
        
        application = serializer.save(
            job_seeker=self.request.user,
            resume=resume,
            match_score=match_score
        )
        
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
            print(f"Error analyzing job match: {e}")
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        application = self.get_object()
        if application.job_post.recruiter != request.user:
            raise permissions.PermissionDenied("Access denied")
        
        new_status = request.data.get('status')
        recruiter_notes = request.data.get('recruiter_notes', '')
        
        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            if recruiter_notes:
                application.recruiter_notes = recruiter_notes
            application.save()
            
            return Response(ApplicationSerializer(application).data)
        
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)


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
            raise permissions.PermissionDenied("Access denied")
        
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
