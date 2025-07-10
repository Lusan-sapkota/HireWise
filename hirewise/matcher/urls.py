from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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
    # Authentication endpoints
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Dashboard and recommendations
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('recommendations/', views.job_recommendations, name='job-recommendations'),
    
    # Include router URLs
    path('', include(router.urls)),
]
