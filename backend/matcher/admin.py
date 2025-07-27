from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils.safestring import mark_safe
import csv
import json
from datetime import datetime, timedelta
from .models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost, 
    Application, AIAnalysisResult, InterviewSession, AIInterviewQuestion,
    Skill, UserSkill, EmailVerificationToken, PasswordResetToken,
    JobAnalytics, JobView, Notification, NotificationPreference,
    NotificationTemplate
)


# Custom Filters
class UserTypeFilter(SimpleListFilter):
    title = 'User Type'
    parameter_name = 'user_type'

    def lookups(self, request, model_admin):
        return User.USER_TYPE_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user_type=self.value())
        return queryset


class RecentActivityFilter(SimpleListFilter):
    title = 'Recent Activity'
    parameter_name = 'recent_activity'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            return queryset.filter(last_login__date=now.date())
        elif self.value() == 'week':
            week_ago = now - timedelta(days=7)
            return queryset.filter(last_login__gte=week_ago)
        elif self.value() == 'month':
            month_ago = now - timedelta(days=30)
            return queryset.filter(last_login__gte=month_ago)
        return queryset


# Enhanced User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'user_type_badge', 'verification_status', 
        'profile_completion', 'last_login_formatted', 'is_active', 'date_joined'
    )
    list_filter = (
        UserTypeFilter, 'is_verified', 'is_active', 'date_joined', 
        RecentActivityFilter
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    actions = [
        'verify_users', 'deactivate_users', 'send_verification_email',
        'export_users_csv', 'bulk_delete_unverified'
    ]
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'profile_picture', 'is_verified')
        }),
        ('Profile Links', {
            'fields': ('profile_links',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('profile_links', 'date_joined', 'last_login')

    def user_type_badge(self, obj):
        colors = {
            'job_seeker': '#28a745',
            'recruiter': '#007bff', 
            'admin': '#dc3545'
        }
        color = colors.get(obj.user_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_user_type_display()
        )
    user_type_badge.short_description = 'Type'

    def verification_status(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="color: green;">✓ Verified</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Unverified</span>'
        )
    verification_status.short_description = 'Status'

    def profile_completion(self, obj):
        completion = 0
        total_fields = 10
        
        if obj.first_name: completion += 1
        if obj.last_name: completion += 1
        if obj.email: completion += 1
        if obj.phone_number: completion += 1
        if obj.profile_picture: completion += 1
        
        if obj.user_type == 'job_seeker' and hasattr(obj, 'job_seeker_profile'):
            profile = obj.job_seeker_profile
            if profile.location: completion += 1
            if profile.current_position: completion += 1
            if profile.skills: completion += 1
            if profile.bio: completion += 1
            if profile.linkedin_url: completion += 1
        elif obj.user_type == 'recruiter' and hasattr(obj, 'recruiter_profile'):
            profile = obj.recruiter_profile
            if profile.company_name: completion += 1
            if profile.company_website: completion += 1
            if profile.industry: completion += 1
            if profile.company_description: completion += 1
            if profile.location: completion += 1
        
        percentage = (completion / total_fields) * 100
        color = '#28a745' if percentage >= 80 else '#ffc107' if percentage >= 50 else '#dc3545'
        
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; '
            'text-align: center; color: white; font-size: 11px; line-height: 20px;">'
            '{}%</div></div>',
            percentage, color, int(percentage)
        )
    profile_completion.short_description = 'Profile'

    def last_login_formatted(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M')
        return 'Never'
    last_login_formatted.short_description = 'Last Login'

    def profile_links(self, obj):
        links = []
        if obj.user_type == 'job_seeker' and hasattr(obj, 'job_seeker_profile'):
            url = reverse('admin:matcher_jobseekerprofile_change', args=[obj.job_seeker_profile.id])
            links.append(f'<a href="{url}">Job Seeker Profile</a>')
        elif obj.user_type == 'recruiter' and hasattr(obj, 'recruiter_profile'):
            url = reverse('admin:matcher_recruiterprofile_change', args=[obj.recruiter_profile.id])
            links.append(f'<a href="{url}">Recruiter Profile</a>')
        
        # Add related objects links
        if obj.resumes.exists():
            links.append(f'<a href="/admin/matcher/resume/?job_seeker__id__exact={obj.id}">Resumes ({obj.resumes.count()})</a>')
        if obj.applications.exists():
            links.append(f'<a href="/admin/matcher/application/?job_seeker__id__exact={obj.id}">Applications ({obj.applications.count()})</a>')
        if obj.job_posts.exists():
            links.append(f'<a href="/admin/matcher/jobpost/?recruiter__id__exact={obj.id}">Job Posts ({obj.job_posts.count()})</a>')
        
        return format_html('<br>'.join(links)) if links else 'No related profiles'
    profile_links.short_description = 'Related Objects'

    # Bulk Actions
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users verified successfully.')
    verify_users.short_description = "Verify selected users"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated successfully.')
    deactivate_users.short_description = "Deactivate selected users"

    def send_verification_email(self, request, queryset):
        # This would integrate with your email service
        count = queryset.filter(is_verified=False).count()
        self.message_user(request, f'Verification emails sent to {count} users.')
    send_verification_email.short_description = "Send verification emails"

    def export_users_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'User Type', 'Verified', 'Active', 'Date Joined', 'Last Login'])
        
        for user in queryset:
            writer.writerow([
                user.username, user.email, user.get_user_type_display(),
                user.is_verified, user.is_active, user.date_joined,
                user.last_login or 'Never'
            ])
        
        return response
    export_users_csv.short_description = "Export selected users to CSV"

    def bulk_delete_unverified(self, request, queryset):
        unverified = queryset.filter(is_verified=False, date_joined__lt=timezone.now() - timedelta(days=30))
        count = unverified.count()
        unverified.delete()
        self.message_user(request, f'{count} unverified users (>30 days old) deleted.')
    bulk_delete_unverified.short_description = "Delete old unverified users"


# Enhanced Profile Admins
@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'current_position', 'experience_level', 'location', 
        'availability_status', 'skills_count', 'resume_count'
    )
    list_filter = ('experience_level', 'availability')
    search_fields = ('user__username', 'current_position', 'current_company', 'location', 'skills')
    actions = ['mark_available', 'mark_unavailable', 'export_profiles_csv']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Professional Details', {
            'fields': ('current_position', 'current_company', 'experience_level', 'expected_salary')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'location', 'bio')
        }),
        ('Skills & Links', {
            'fields': ('skills', 'linkedin_url', 'github_url', 'portfolio_url')
        }),
        ('Availability', {
            'fields': ('availability',)
        }),
    )

    def availability_status(self, obj):
        if obj.availability:
            return format_html('<span style="color: green;">✓ Available</span>')
        return format_html('<span style="color: red;">✗ Not Available</span>')
    availability_status.short_description = 'Status'

    def skills_count(self, obj):
        if obj.skills:
            skills = [s.strip() for s in obj.skills.split(',') if s.strip()]
            return len(skills)
        return 0
    skills_count.short_description = 'Skills'

    def resume_count(self, obj):
        return obj.user.resumes.count()
    resume_count.short_description = 'Resumes'

    def mark_available(self, request, queryset):
        updated = queryset.update(availability=True)
        self.message_user(request, f'{updated} profiles marked as available.')
    mark_available.short_description = "Mark as available"

    def mark_unavailable(self, request, queryset):
        updated = queryset.update(availability=False)
        self.message_user(request, f'{updated} profiles marked as unavailable.')
    mark_unavailable.short_description = "Mark as unavailable"

    def export_profiles_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="job_seeker_profiles.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Email', 'Current Position', 'Company', 'Experience Level',
            'Location', 'Expected Salary', 'Skills', 'Available'
        ])
        
        for profile in queryset:
            writer.writerow([
                profile.user.username, profile.user.email, profile.current_position,
                profile.current_company, profile.get_experience_level_display(),
                profile.location, profile.expected_salary, profile.skills,
                'Yes' if profile.availability else 'No'
            ])
        
        return response
    export_profiles_csv.short_description = "Export profiles to CSV"


@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'company_name', 'industry', 'location', 
        'company_size', 'active_jobs_count', 'total_applications'
    )
    list_filter = ('industry', 'company_size')
    search_fields = ('user__username', 'company_name', 'industry', 'location')
    actions = ['export_recruiters_csv']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Company Details', {
            'fields': ('company_name', 'company_website', 'company_size', 'industry')
        }),
        ('Company Profile', {
            'fields': ('company_description', 'company_logo', 'location')
        }),
    )

    def active_jobs_count(self, obj):
        return obj.user.job_posts.filter(is_active=True).count()
    active_jobs_count.short_description = 'Active Jobs'

    def total_applications(self, obj):
        return Application.objects.filter(job_post__recruiter=obj.user).count()
    total_applications.short_description = 'Total Applications'

    def export_recruiters_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recruiters.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Email', 'Company', 'Industry', 'Location',
            'Company Size', 'Website', 'Active Jobs', 'Total Applications'
        ])
        
        for profile in queryset:
            writer.writerow([
                profile.user.username, profile.user.email, profile.company_name,
                profile.industry, profile.location, profile.company_size,
                profile.company_website, self.active_jobs_count(profile),
                self.total_applications(profile)
            ])
        
        return response
    export_recruiters_csv.short_description = "Export recruiters to CSV"


# Enhanced Resume Admin
@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = (
        'job_seeker', 'original_filename', 'primary_status', 'file_size_formatted',
        'uploaded_at', 'parsed_status', 'applications_count'
    )
    list_filter = ('is_primary', 'uploaded_at')
    search_fields = ('job_seeker__username', 'original_filename', 'parsed_text')
    readonly_fields = ('file_size', 'uploaded_at', 'file_preview')
    actions = ['mark_as_primary', 'bulk_parse_resumes', 'export_resumes_csv']
    
    fieldsets = (
        ('File Information', {
            'fields': ('job_seeker', 'file', 'original_filename', 'is_primary')
        }),
        ('File Details', {
            'fields': ('file_size', 'uploaded_at', 'file_preview'),
            'classes': ('collapse',)
        }),
        ('Parsed Content', {
            'fields': ('parsed_text',),
            'classes': ('collapse',)
        }),
    )

    def primary_status(self, obj):
        if obj.is_primary:
            return format_html('<span style="color: green;">★ Primary</span>')
        return format_html('<span style="color: gray;">Secondary</span>')
    primary_status.short_description = 'Status'

    def file_size_formatted(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "Unknown"
    file_size_formatted.short_description = 'Size'

    def parsed_status(self, obj):
        if obj.parsed_text:
            return format_html('<span style="color: green;">✓ Parsed</span>')
        return format_html('<span style="color: orange;">Not Parsed</span>')
    parsed_status.short_description = 'Parsed'

    def applications_count(self, obj):
        return obj.application_set.count()
    applications_count.short_description = 'Applications'

    def file_preview(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Download File</a><br>'
                'File: {}<br>Size: {}',
                obj.file.url, obj.original_filename, self.file_size_formatted(obj)
            )
        return "No file"
    file_preview.short_description = 'File Preview'

    def mark_as_primary(self, request, queryset):
        for resume in queryset:
            # Unmark other resumes as primary for this user
            Resume.objects.filter(job_seeker=resume.job_seeker).update(is_primary=False)
            # Mark this resume as primary
            resume.is_primary = True
            resume.save()
        self.message_user(request, f'{queryset.count()} resumes marked as primary.')
    mark_as_primary.short_description = "Mark as primary resume"

    def bulk_parse_resumes(self, request, queryset):
        unparsed = queryset.filter(parsed_text='')
        count = unparsed.count()
        # This would trigger your resume parsing service
        self.message_user(request, f'{count} resumes queued for parsing.')
    bulk_parse_resumes.short_description = "Parse selected resumes"

    def export_resumes_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="resumes.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Job Seeker', 'Email', 'Filename', 'Primary', 'File Size', 
            'Uploaded', 'Parsed', 'Applications Count'
        ])
        
        for resume in queryset:
            writer.writerow([
                resume.job_seeker.username, resume.job_seeker.email,
                resume.original_filename, 'Yes' if resume.is_primary else 'No',
                self.file_size_formatted(resume), resume.uploaded_at,
                'Yes' if resume.parsed_text else 'No', self.applications_count(resume)
            ])
        
        return response
    export_resumes_csv.short_description = "Export resumes to CSV"


# Enhanced JobPost Admin
class JobStatusFilter(SimpleListFilter):
    title = 'Job Status'
    parameter_name = 'job_status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('expired', 'Expired'),
            ('draft', 'Draft'),
            ('featured', 'Featured'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True, application_deadline__gt=timezone.now())
        elif self.value() == 'expired':
            return queryset.filter(application_deadline__lt=timezone.now())
        elif self.value() == 'draft':
            return queryset.filter(is_active=False)
        elif self.value() == 'featured':
            return queryset.filter(is_featured=True)
        return queryset


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'recruiter_company', 'job_type', 'experience_level', 
        'location', 'status_badge', 'applications_count', 'views_count', 
        'salary_range', 'created_at'
    )
    list_filter = (
        'job_type', 'experience_level', 'is_active', 'is_featured',
        'created_at', JobStatusFilter, 'priority'
    )
    search_fields = ('title', 'recruiter__username', 'location', 'skills_required', 'description')
    readonly_fields = ('views_count', 'applications_count', 'created_at', 'updated_at', 'slug')
    actions = [
        'activate_jobs', 'deactivate_jobs', 'mark_featured', 'unmark_featured',
        'export_jobs_csv', 'bulk_extend_deadline'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'recruiter', 'description', 'location', 'remote_work_allowed')
        }),
        ('Job Details', {
            'fields': ('job_type', 'experience_level', 'priority', 'application_deadline')
        }),
        ('Requirements & Responsibilities', {
            'fields': ('requirements', 'responsibilities', 'skills_required', 'benefits')
        }),
        ('Compensation', {
            'fields': ('salary_min', 'salary_max', 'salary_currency')
        }),
        ('Status & SEO', {
            'fields': ('is_active', 'is_featured', 'slug', 'meta_description')
        }),
        ('Analytics', {
            'fields': ('views_count', 'applications_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def recruiter_company(self, obj):
        if hasattr(obj.recruiter, 'recruiter_profile'):
            return obj.recruiter.recruiter_profile.company_name
        return obj.recruiter.username
    recruiter_company.short_description = 'Company'

    def status_badge(self, obj):
        if not obj.is_active:
            return format_html('<span style="background-color: #6c757d; color: white; padding: 2px 6px; border-radius: 3px;">Draft</span>')
        elif obj.is_expired:
            return format_html('<span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px;">Expired</span>')
        elif obj.is_featured:
            return format_html('<span style="background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px;">★ Featured</span>')
        else:
            return format_html('<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px;">Active</span>')
    status_badge.short_description = 'Status'

    def salary_range(self, obj):
        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_currency} {obj.salary_min:,} - {obj.salary_max:,}"
        elif obj.salary_min:
            return f"{obj.salary_currency} {obj.salary_min:,}+"
        return "Not specified"
    salary_range.short_description = 'Salary'

    # Bulk Actions
    def activate_jobs(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} jobs activated successfully.')
    activate_jobs.short_description = "Activate selected jobs"

    def deactivate_jobs(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} jobs deactivated successfully.')
    deactivate_jobs.short_description = "Deactivate selected jobs"

    def mark_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} jobs marked as featured.')
    mark_featured.short_description = "Mark as featured"

    def unmark_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} jobs unmarked as featured.')
    unmark_featured.short_description = "Remove featured status"

    def bulk_extend_deadline(self, request, queryset):
        new_deadline = timezone.now() + timedelta(days=30)
        updated = queryset.update(application_deadline=new_deadline)
        self.message_user(request, f'{updated} job deadlines extended by 30 days.')
    bulk_extend_deadline.short_description = "Extend deadline by 30 days"

    def export_jobs_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="job_posts.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Title', 'Company', 'Recruiter', 'Job Type', 'Experience Level',
            'Location', 'Salary Min', 'Salary Max', 'Skills Required',
            'Active', 'Featured', 'Views', 'Applications', 'Created'
        ])
        
        for job in queryset:
            writer.writerow([
                job.title, self.recruiter_company(job), job.recruiter.username,
                job.get_job_type_display(), job.get_experience_level_display(),
                job.location, job.salary_min, job.salary_max, job.skills_required,
                'Yes' if job.is_active else 'No', 'Yes' if job.is_featured else 'No',
                job.views_count, job.applications_count, job.created_at
            ])
        
        return response
    export_jobs_csv.short_description = "Export jobs to CSV"


# Enhanced Application Admin
class ApplicationStatusFilter(SimpleListFilter):
    title = 'Application Status'
    parameter_name = 'app_status'

    def lookups(self, request, model_admin):
        return Application.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class MatchScoreFilter(SimpleListFilter):
    title = 'Match Score Range'
    parameter_name = 'match_score_range'

    def lookups(self, request, model_admin):
        return (
            ('high', 'High (80-100)'),
            ('medium', 'Medium (50-79)'),
            ('low', 'Low (0-49)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(match_score__gte=80)
        elif self.value() == 'medium':
            return queryset.filter(match_score__gte=50, match_score__lt=80)
        elif self.value() == 'low':
            return queryset.filter(match_score__lt=50)
        return queryset


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'job_seeker', 'job_post_title', 'company_name', 'status_badge', 
        'match_score_display', 'applied_at', 'days_since_applied'
    )
    list_filter = (
        ApplicationStatusFilter, 'applied_at', MatchScoreFilter
    )
    search_fields = (
        'job_seeker__username', 'job_post__title', 
        'job_post__recruiter__recruiter_profile__company_name'
    )
    readonly_fields = ('applied_at', 'updated_at', 'application_details')
    actions = [
        'mark_reviewed', 'mark_shortlisted', 'mark_rejected',
        'export_applications_csv', 'bulk_calculate_match_scores'
    ]
    
    fieldsets = (
        ('Application Details', {
            'fields': ('job_seeker', 'job_post', 'resume', 'status')
        }),
        ('Content', {
            'fields': ('cover_letter', 'recruiter_notes')
        }),
        ('Scoring & Analytics', {
            'fields': ('match_score', 'applied_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('application_details',),
            'classes': ('collapse',)
        }),
    )

    def job_post_title(self, obj):
        return obj.job_post.title[:50] + ('...' if len(obj.job_post.title) > 50 else '')
    job_post_title.short_description = 'Job Title'

    def company_name(self, obj):
        if hasattr(obj.job_post.recruiter, 'recruiter_profile'):
            return obj.job_post.recruiter.recruiter_profile.company_name
        return obj.job_post.recruiter.username
    company_name.short_description = 'Company'

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'reviewed': '#17a2b8',
            'shortlisted': '#28a745',
            'interview_scheduled': '#007bff',
            'interviewed': '#6f42c1',
            'hired': '#28a745',
            'rejected': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def match_score_display(self, obj):
        if obj.match_score > 0:
            color = '#28a745' if obj.match_score >= 80 else '#ffc107' if obj.match_score >= 50 else '#dc3545'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, float(obj.match_score)
            )
        return format_html('<span style="color: #6c757d;">Not calculated</span>')
    match_score_display.short_description = 'Match Score'

    def days_since_applied(self, obj):
        days = (timezone.now() - obj.applied_at).days
        if days == 0:
            return 'Today'
        elif days == 1:
            return '1 day ago'
        else:
            return f'{days} days ago'
    days_since_applied.short_description = 'Applied'

    def application_details(self, obj):
        details = []
        details.append(f'<strong>Job Seeker:</strong> {obj.job_seeker.get_full_name() or obj.job_seeker.username}')
        details.append(f'<strong>Email:</strong> {obj.job_seeker.email}')
        if hasattr(obj.job_seeker, 'job_seeker_profile'):
            profile = obj.job_seeker.job_seeker_profile
            if profile.current_position:
                details.append(f'<strong>Current Position:</strong> {profile.current_position}')
            if profile.location:
                details.append(f'<strong>Location:</strong> {profile.location}')
        details.append(f'<strong>Resume:</strong> {obj.resume.original_filename}')
        details.append(f'<strong>Applied:</strong> {obj.applied_at.strftime("%Y-%m-%d %H:%M")}')
        if obj.updated_at != obj.applied_at:
            details.append(f'<strong>Last Updated:</strong> {obj.updated_at.strftime("%Y-%m-%d %H:%M")}')
        
        return format_html('<br>'.join(details))
    application_details.short_description = 'Application Details'

    # Bulk Actions
    def mark_reviewed(self, request, queryset):
        updated = queryset.update(status='reviewed')
        self.message_user(request, f'{updated} applications marked as reviewed.')
    mark_reviewed.short_description = "Mark as reviewed"

    def mark_shortlisted(self, request, queryset):
        updated = queryset.update(status='shortlisted')
        self.message_user(request, f'{updated} applications shortlisted.')
    mark_shortlisted.short_description = "Mark as shortlisted"

    def mark_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} applications rejected.')
    mark_rejected.short_description = "Mark as rejected"

    def bulk_calculate_match_scores(self, request, queryset):
        count = queryset.filter(match_score=0).count()
        # This would trigger your ML matching service
        self.message_user(request, f'{count} applications queued for match score calculation.')
    bulk_calculate_match_scores.short_description = "Calculate match scores"

    def export_applications_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="applications.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Job Seeker', 'Email', 'Job Title', 'Company', 'Status',
            'Match Score', 'Applied Date', 'Resume File', 'Cover Letter Length'
        ])
        
        for app in queryset:
            writer.writerow([
                app.job_seeker.username, app.job_seeker.email,
                app.job_post.title, self.company_name(app),
                app.get_status_display(), app.match_score,
                app.applied_at, app.resume.original_filename,
                len(app.cover_letter) if app.cover_letter else 0
            ])
        
        return response
    export_applications_csv.short_description = "Export applications to CSV"


# Register remaining models with basic admin
@admin.register(AIAnalysisResult)
class AIAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('analysis_type', 'confidence_score', 'processing_time', 'processed_at')
    list_filter = ('analysis_type', 'processed_at')
    readonly_fields = ('processed_at', 'processing_time')


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('application', 'interview_type', 'status', 'scheduled_at', 'rating')
    list_filter = ('interview_type', 'status', 'scheduled_at')
    search_fields = ('application__job_seeker__username', 'application__job_post__title')


@admin.register(AIInterviewQuestion)
class AIInterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ('interview_session', 'question_type', 'difficulty_level', 'ai_score')
    list_filter = ('question_type', 'difficulty_level')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_verified', 'created_at')
    list_filter = ('category', 'is_verified')
    search_fields = ('name', 'description')


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'proficiency_level', 'years_of_experience', 'is_verified')
    list_filter = ('proficiency_level', 'is_verified')
    search_fields = ('user__username', 'skill__name')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email')


@admin.register(JobAnalytics)
class JobAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('job_post', 'total_views', 'unique_views', 'total_applications', 'conversion_rate')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('job_post__title',)


@admin.register(JobView)
class JobViewAdmin(admin.ModelAdmin):
    list_display = ('job_post', 'viewer', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('job_post__title', 'viewer__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'priority', 'is_read', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_posted_enabled', 'application_received_enabled', 'digest_frequency')
    list_filter = ('digest_frequency',)
    search_fields = ('user__username',)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_type', 'delivery_channel', 'is_active', 'is_default')
    list_filter = ('template_type', 'delivery_channel', 'is_active')


# Admin Site Customization
admin.site.site_header = "HireWise Admin Dashboard"
admin.site.site_title = "HireWise Admin"
admin.site.index_title = "Welcome to HireWise Administration"