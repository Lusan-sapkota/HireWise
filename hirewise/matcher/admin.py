from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost, 
    Application, AIAnalysisResult, InterviewSession, AIInterviewQuestion,
    Skill, UserSkill
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_verified', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'profile_picture', 'is_verified')
        }),
    )


@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_position', 'experience_level', 'location', 'availability')
    list_filter = ('experience_level', 'availability')
    search_fields = ('user__username', 'current_position', 'current_company', 'location')


@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'industry', 'location')
    list_filter = ('industry',)
    search_fields = ('user__username', 'company_name', 'industry', 'location')


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('job_seeker', 'original_filename', 'is_primary', 'uploaded_at', 'file_size')
    list_filter = ('is_primary', 'uploaded_at')
    search_fields = ('job_seeker__username', 'original_filename')
    readonly_fields = ('file_size', 'uploaded_at')


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'recruiter', 'job_type', 'experience_level', 'location', 'is_active', 'created_at')
    list_filter = ('job_type', 'experience_level', 'is_active', 'created_at')
    search_fields = ('title', 'recruiter__username', 'location', 'skills_required')
    readonly_fields = ('views_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'recruiter', 'description', 'location', 'job_type', 'experience_level')
        }),
        ('Requirements & Responsibilities', {
            'fields': ('requirements', 'responsibilities', 'skills_required')
        }),
        ('Compensation & Benefits', {
            'fields': ('salary_min', 'salary_max', 'benefits')
        }),
        ('Status & Deadlines', {
            'fields': ('is_active', 'application_deadline')
        }),
        ('Metadata', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job_seeker', 'job_post', 'status', 'match_score', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('job_seeker__username', 'job_post__title')
    readonly_fields = ('applied_at', 'updated_at')


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
