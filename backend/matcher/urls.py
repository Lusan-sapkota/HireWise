from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import file_views
from . import recommendation_views

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
router.register(r'resume-templates', views.ResumeTemplateViewSet, basename='resume-template')
router.register(r'resume-template-versions', views.ResumeTemplateVersionViewSet, basename='resume-template-version')
router.register(r'user-resume-templates', views.UserResumeTemplateViewSet, basename='user-resume-template')

urlpatterns = [
    # JWT Authentication endpoints
    path('auth/jwt/register/', views.JWTRegisterView.as_view(), name='jwt-register'),
    path('auth/jwt/login/', views.JWTLoginView.as_view(), name='jwt-login'),
    path('auth/jwt/logout/', views.jwt_logout_view, name='jwt-logout'),
    path('auth/jwt/token/', views.CustomTokenObtainPairView.as_view(), name='jwt-token-obtain-pair'),
    path('auth/jwt/token/refresh/', views.CustomTokenRefreshView.as_view(), name='jwt-token-refresh'),
    # Google OAuth endpoint
    path('auth/google/', views.google_login_view, name='google-login'),
    
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
    
    # Task monitoring and management endpoints
    path('tasks/status/<str:task_id>/', views.get_task_status_view, name='get-task-status'),
    path('tasks/batch-status/', views.get_batch_task_status_view, name='get-batch-task-status'),
    path('tasks/progress/<str:task_id>/', views.get_task_progress_view, name='get-task-progress'),
    path('tasks/cancel/<str:task_id>/', views.cancel_task_view, name='cancel-task'),
    path('tasks/active/', views.get_active_tasks_view, name='get-active-tasks'),
    path('tasks/worker-stats/', views.get_worker_stats_view, name='get-worker-stats'),
    path('tasks/result/<str:task_id>/', views.get_task_result_view, name='get-task-result'),
    path('tasks/result/<str:task_id>/clear/', views.clear_task_result_view, name='clear-task-result'),
    path('tasks/user-results/', views.get_user_task_results_view, name='get-user-task-results'),
    path('tasks/test/', views.test_celery_task_view, name='test-celery-task'),
    
    # Background task queue endpoints
    path('tasks/queue/parse-resume/', views.queue_resume_parsing_task_view, name='queue-resume-parsing-task'),
    path('tasks/queue/batch-parse-resumes/', views.queue_batch_resume_parsing_task_view, name='queue-batch-resume-parsing-task'),
    path('tasks/queue/resume-insights/', views.queue_resume_insights_task_view, name='queue-resume-insights-task'),
    path('tasks/queue/send-notification/', views.send_notification_task_view, name='send-notification-task'),
    path('tasks/queue/health-check/', views.health_check_task_view, name='health-check-task'),
    
    # Secure file upload and management endpoints
    path('files/upload/', file_views.secure_file_upload, name='secure-file-upload'),
    path('files/upload-resume/', file_views.upload_resume, name='upload-resume'),
    path('files/secure/<path:file_path>/', file_views.serve_secure_file, name='serve-secure-file'),
    path('files/delete/<int:file_id>/', file_views.delete_file, name='delete-file'),
    path('files/list/', file_views.list_user_files, name='list-user-files'),
    path('files/cleanup/', file_views.cleanup_old_files, name='cleanup-old-files'),
    path('files/validation-info/', file_views.file_validation_info, name='file-validation-info'),
    
    # Advanced search and recommendation endpoints
    path('recommendations/jobs/', recommendation_views.JobRecommendationView.as_view(), name='job-recommendations'),
    path('recommendations/candidates/<uuid:job_id>/', recommendation_views.CandidateRecommendationView.as_view(), name='candidate-recommendations'),
    path('search/jobs/', recommendation_views.AdvancedJobSearchView.as_view(), name='advanced-job-search'),
    path('search/candidates/', recommendation_views.AdvancedCandidateSearchView.as_view(), name='advanced-candidate-search'),
    path('dashboard/personalized/', recommendation_views.personalized_dashboard_view, name='personalized-dashboard'),
    
    # Notification endpoints
    path('notifications/', views.NotificationListView.as_view(), name='notifications-list'),
    path('notifications/<uuid:notification_id>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/<uuid:notification_id>/mark-read/', views.mark_notification_read, name='mark-notification-read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark-all-notifications-read'),
    path('notifications/unread-count/', views.get_unread_notifications_count, name='unread-notifications-count'),
    path('notifications/preferences/', views.notification_preferences, name='notification-preferences'),
    path('notifications/cleanup-expired/', views.cleanup_expired_notifications, name='cleanup-expired-notifications'),
    path('notifications/deliver-queued/', views.deliver_queued_notifications, name='deliver-queued-notifications'),
    
    # Resume builder endpoints
    path('resume-builder/templates/', views.ResumeTemplateListView.as_view(), name='resume-templates'),
    path('resume-builder/templates/<uuid:template_id>/preview/', views.get_template_preview, name='template-preview'),
    path('resume-builder/generate/', views.generate_resume_content, name='generate-resume-content'),
    path('resume-builder/export/', views.export_resume, name='export-resume'),
    path('resume-builder/suggestions/', views.get_resume_suggestions, name='resume-suggestions'),
    
    # AI Resume Assistance endpoints
    path('resume-analysis/analyze-for-job/', views.analyze_resume_for_job, name='analyze-resume-for-job'),
    path('resume-analysis/skill-gap/', views.get_skill_gap_analysis, name='skill-gap-analysis'),
    path('resume-analysis/score/', views.score_resume_content, name='score-resume-content'),
    path('resume-analysis/keywords/', views.get_keyword_optimization, name='keyword-optimization'),
    path('resume-analysis/<uuid:resume_id>/history/', views.get_resume_analysis_history, name='resume-analysis-history'),
    
    # AI Interview endpoints
    path('ai-interview/start/', views.start_ai_interview, name='start-ai-interview'),
    path('ai-interview/<uuid:session_id>/response/', views.submit_ai_interview_response, name='submit-ai-interview-response'),
    path('ai-interview/<uuid:session_id>/end/', views.end_ai_interview, name='end-ai-interview'),
    path('ai-interview/<uuid:session_id>/feedback/', views.get_ai_interview_feedback, name='ai-interview-feedback'),
    
    # AI Interview Session Management endpoints
    path('ai-interview/<uuid:session_id>/status/', views.get_interview_session_status, name='interview-session-status'),
    path('ai-interview/<uuid:session_id>/questions/', views.get_interview_questions, name='interview-questions'),
    path('ai-interview/<uuid:session_id>/pause/', views.pause_interview_session, name='pause-interview-session'),
    path('ai-interview/<uuid:session_id>/resume/', views.resume_interview_session, name='resume-interview-session'),
    path('ai-interview/<uuid:session_id>/cancel/', views.cancel_interview_session, name='cancel-interview-session'),
    path('ai-interview/sessions/', views.get_user_interview_sessions, name='user-interview-sessions'),
    path('ai-interview/cleanup-expired/', views.cleanup_expired_sessions, name='cleanup-expired-sessions'),
    
    # Message endpoints
    path('messages/conversations/', views.ConversationListView.as_view(), name='conversations-list'),
    path('messages/conversations/<uuid:conversation_id>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
    path('messages/conversations/<uuid:conversation_id>/messages/', views.MessageListView.as_view(), name='messages-list'),
    path('messages/send/', views.send_message, name='send-message'),
    path('messages/mark-read/', views.mark_messages_read, name='mark-messages-read'),
    
    # Search analytics and suggestions endpoints
    path('search/suggestions/', recommendation_views.search_suggestions_view, name='search-suggestions'),
    path('search/popular/', recommendation_views.popular_searches_view, name='popular-searches'),
    path('search/save/', recommendation_views.save_search_view, name='save-search'),
    path('search/saved/', recommendation_views.saved_searches_view, name='saved-searches'),
    path('search/saved/<uuid:search_id>/', recommendation_views.delete_saved_search_view, name='delete-saved-search'),
    path('search/analytics/', recommendation_views.search_analytics_view, name='search-analytics'),
    path('search/track-interaction/', recommendation_views.track_search_interaction_view, name='track-search-interaction'),
    
    # Include router URLs
    path('', include(router.urls)),
]
