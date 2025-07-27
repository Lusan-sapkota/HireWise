from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import (
    User, JobPost, Application, Resume, JobAnalytics, 
    Notification, AIAnalysisResult
)


@staff_member_required
def admin_dashboard(request):
    """
    Custom admin dashboard with system analytics and monitoring
    """
    # Calculate date ranges
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # User statistics
    total_users = User.objects.count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
    active_users_week = User.objects.filter(last_login__gte=week_ago).count()
    
    user_type_breakdown = User.objects.values('user_type').annotate(
        count=Count('id')
    ).order_by('user_type')
    
    # Job statistics
    total_jobs = JobPost.objects.count()
    active_jobs = JobPost.objects.filter(is_active=True).count()
    featured_jobs = JobPost.objects.filter(is_featured=True).count()
    new_jobs_week = JobPost.objects.filter(created_at__gte=week_ago).count()
    
    # Application statistics
    total_applications = Application.objects.count()
    new_applications_today = Application.objects.filter(applied_at__date=today).count()
    new_applications_week = Application.objects.filter(applied_at__gte=week_ago).count()
    
    application_status_breakdown = Application.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Resume statistics
    total_resumes = Resume.objects.count()
    parsed_resumes = Resume.objects.exclude(parsed_text='').count()
    parsing_rate = (parsed_resumes / total_resumes * 100) if total_resumes > 0 else 0
    
    # AI Analysis statistics
    total_analyses = AIAnalysisResult.objects.count()
    avg_confidence = AIAnalysisResult.objects.aggregate(
        avg_confidence=Avg('confidence_score')
    )['avg_confidence'] or 0
    
    # Top performing jobs (by applications)
    top_jobs = JobPost.objects.annotate(
        app_count=Count('applications')
    ).order_by('-app_count')[:5]
    
    # Recent activity
    recent_applications = Application.objects.select_related(
        'job_seeker', 'job_post'
    ).order_by('-applied_at')[:10]
    
    recent_jobs = JobPost.objects.select_related(
        'recruiter'
    ).order_by('-created_at')[:10]
    
    # System health indicators
    unverified_users = User.objects.filter(is_verified=False).count()
    pending_applications = Application.objects.filter(status='pending').count()
    unread_notifications = Notification.objects.filter(is_read=False).count()
    
    context = {
        'title': 'System Dashboard',
        'user_stats': {
            'total': total_users,
            'new_today': new_users_today,
            'new_week': new_users_week,
            'active_week': active_users_week,
            'breakdown': user_type_breakdown,
            'unverified': unverified_users,
        },
        'job_stats': {
            'total': total_jobs,
            'active': active_jobs,
            'featured': featured_jobs,
            'new_week': new_jobs_week,
        },
        'application_stats': {
            'total': total_applications,
            'new_today': new_applications_today,
            'new_week': new_applications_week,
            'breakdown': application_status_breakdown,
            'pending': pending_applications,
        },
        'resume_stats': {
            'total': total_resumes,
            'parsed': parsed_resumes,
            'parsing_rate': round(parsing_rate, 1),
        },
        'ai_stats': {
            'total_analyses': total_analyses,
            'avg_confidence': round(avg_confidence * 100, 1) if avg_confidence else 0,
        },
        'top_jobs': top_jobs,
        'recent_applications': recent_applications,
        'recent_jobs': recent_jobs,
        'system_health': {
            'unverified_users': unverified_users,
            'pending_applications': pending_applications,
            'unread_notifications': unread_notifications,
        }
    }
    
    return render(request, 'admin/dashboard.html', context)


@staff_member_required
def analytics_api(request):
    """
    API endpoint for dashboard analytics data
    """
    # Calculate date ranges
    now = timezone.now()
    days_back = int(request.GET.get('days', 30))
    start_date = now - timedelta(days=days_back)
    
    # Daily user registrations
    daily_users = []
    for i in range(days_back):
        date = (start_date + timedelta(days=i)).date()
        count = User.objects.filter(date_joined__date=date).count()
        daily_users.append({
            'date': date.isoformat(),
            'count': count
        })
    
    # Daily job postings
    daily_jobs = []
    for i in range(days_back):
        date = (start_date + timedelta(days=i)).date()
        count = JobPost.objects.filter(created_at__date=date).count()
        daily_jobs.append({
            'date': date.isoformat(),
            'count': count
        })
    
    # Daily applications
    daily_applications = []
    for i in range(days_back):
        date = (start_date + timedelta(days=i)).date()
        count = Application.objects.filter(applied_at__date=date).count()
        daily_applications.append({
            'date': date.isoformat(),
            'count': count
        })
    
    # Match score distribution
    match_score_ranges = [
        ('90-100', Application.objects.filter(match_score__gte=90).count()),
        ('80-89', Application.objects.filter(match_score__gte=80, match_score__lt=90).count()),
        ('70-79', Application.objects.filter(match_score__gte=70, match_score__lt=80).count()),
        ('60-69', Application.objects.filter(match_score__gte=60, match_score__lt=70).count()),
        ('50-59', Application.objects.filter(match_score__gte=50, match_score__lt=60).count()),
        ('0-49', Application.objects.filter(match_score__lt=50, match_score__gt=0).count()),
    ]
    
    return JsonResponse({
        'daily_users': daily_users,
        'daily_jobs': daily_jobs,
        'daily_applications': daily_applications,
        'match_score_distribution': [
            {'range': range_name, 'count': count}
            for range_name, count in match_score_ranges
        ]
    })


@staff_member_required
def system_health_api(request):
    """
    API endpoint for system health monitoring
    """
    # System health checks
    health_data = {
        'database': {
            'status': 'healthy',
            'total_records': (
                User.objects.count() + 
                JobPost.objects.count() + 
                Application.objects.count()
            )
        },
        'users': {
            'total': User.objects.count(),
            'active_today': User.objects.filter(
                last_login__date=timezone.now().date()
            ).count(),
            'unverified': User.objects.filter(is_verified=False).count(),
        },
        'jobs': {
            'total': JobPost.objects.count(),
            'active': JobPost.objects.filter(is_active=True).count(),
            'expired': JobPost.objects.filter(
                application_deadline__lt=timezone.now()
            ).count(),
        },
        'applications': {
            'total': Application.objects.count(),
            'pending': Application.objects.filter(status='pending').count(),
            'processed_today': Application.objects.filter(
                updated_at__date=timezone.now().date()
            ).count(),
        },
        'ai_processing': {
            'total_analyses': AIAnalysisResult.objects.count(),
            'avg_processing_time': AIAnalysisResult.objects.aggregate(
                avg_time=Avg('processing_time')
            )['avg_time'] or 0,
            'recent_failures': AIAnalysisResult.objects.filter(
                confidence_score__lt=0.5,
                processed_at__gte=timezone.now() - timedelta(hours=24)
            ).count(),
        }
    }
    
    return JsonResponse(health_data)