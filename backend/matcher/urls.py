from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import file_views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'job-seeker-profiles', views.JobSeekerProfileViewSet, basename='job-seeker-profile')
router.register(r'recruiter-profiles', views.RecruiterProfileViewSet, basename='recruiter-profile')
router.register(r'resumes', views.ResumeViewSet, basename='resume')
router.register(r'job-posts', views.JobPostViewSet, basename='job-post')
router.register(r'applications', views.ApplicationViewSet, basename='application')
router.register(r'interview-sessions', views.InterviewSessionViewSet, basename='interview-session')
router.register(r'skills', views.SkillViewSet, basename='skill')
router.register(r'user-skills', views.UserSkillViewSet, basename='user-skill')

urlpatterns = [
    # JWT Authentication endpoints
    path('auth/jwt/register/', views.JWTRegisterView.as_view(), name='jwt-register'),
    path('auth/jwt/login/', views.JWTLoginView.as_view(), name='jwt-login'),
    path('auth/jwt/logout/', views.jwt_logout_view, name='jwt-logout'),
    path('auth/jwt/token/', views.CustomTokenObtainPairView.as_view(), name='jwt-token-obtain-pair'),
    path('auth/jwt/token/refresh/', views.CustomTokenRefreshView.as_view(), name='jwt-token-refresh'),
    
    # Legacy authentication endpoints (for backward compatibility)
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Email verification endpoints
    path('auth/request-email-verification/', views.request_email_verification, name='request-email-verification'),
    path('auth/verify-email/', views.verify_email, name='verify-email'),
    
    # Password reset endpoints
    path('auth/request-password-reset/', views.request_password_reset, name='request-password-reset'),
    path('auth/reset-password/', views.reset_password, name='reset-password'),
    
    # User profile management endpoints
    path('auth/change-password/', views.change_password, name='change-password'),
    path('auth/profile/', views.user_profile, name='user-profile'),
    path('auth/delete-account/', views.delete_account, name='delete-account'),
    
    # Dashboard and recommendations
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('recommendations/', views.job_recommendations, name='job-recommendations'),
    
    # Resume parsing endpoints
    path('parse-resume/', views.parse_resume_view, name='parse-resume'),
    path('parse-resume/<int:resume_id>/', views.parse_resume_by_id_view, name='parse-resume-by-id'),
    path('parse-resume-async/', views.parse_resume_async_view, name='parse-resume-async'),
    path('parse-task-status/<str:task_id>/', views.parse_task_status_view, name='parse-task-status'),
    path('batch-parse-resumes/', views.batch_parse_resumes_view, name='batch-parse-resumes'),
    
    # Match score calculation endpoints
    path('calculate-match-score/', views.calculate_match_score_view, name='calculate-match-score'),
    path('calculate-match-score-async/', views.calculate_match_score_async_view, name='calculate-match-score-async'),
    path('batch-calculate-match-scores/', views.batch_calculate_match_scores_view, name='batch-calculate-match-scores'),
    path('match-scores/resume/<uuid:resume_id>/', views.get_match_scores_for_resume_view, name='match-scores-for-resume'),
    path('match-scores/job/<uuid:job_id>/', views.get_match_scores_for_job_view, name='match-scores-for-job'),
    
    # Secure file upload and management endpoints
    path('files/upload/', file_views.secure_file_upload, name='secure-file-upload'),
    path('files/upload-resume/', file_views.upload_resume, name='upload-resume'),
    path('files/secure/<path:file_path>/', file_views.serve_secure_file, name='serve-secure-file'),
    path('files/delete/<int:file_id>/', file_views.delete_file, name='delete-file'),
    path('files/list/', file_views.list_user_files, name='list-user-files'),
    path('files/cleanup/', file_views.cleanup_old_files, name='cleanup-old-files'),
    path('files/validation-info/', file_views.file_validation_info, name='file-validation-info'),
    
    # Include router URLs
    path('', include(router.urls)),
]
