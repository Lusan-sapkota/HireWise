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
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny

import json
import os
from datetime import datetime, timedelta

from .models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost,
    Application, AIAnalysisResult, InterviewSession, Skill, UserSkill
)
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    JobSeekerProfileSerializer, RecruiterProfileSerializer, ResumeSerializer,
    JobPostSerializer, ApplicationSerializer, AIAnalysisResultSerializer,
    InterviewSessionSerializer, SkillSerializer, UserSkillSerializer,
    JobMatchSerializer
)
from .utils import (
    parse_resume, analyze_job_match, extract_skills_from_text,
    generate_interview_questions, calculate_match_score
)


# Authentication Views
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            # Create corresponding profile based on user type
            if user.user_type == 'job_seeker':
                JobSeekerProfile.objects.create(user=user)
            elif user.user_type == 'recruiter':
                RecruiterProfile.objects.create(
                    user=user,
                    company_name=request.data.get('company_name', '')
                )
            
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except:
        return Response({'message': 'Error during logout'}, status=status.HTTP_400_BAD_REQUEST)


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
