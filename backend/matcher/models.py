from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from datetime import timedelta
import uuid

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('job_seeker', 'Job Seeker'),
        ('recruiter', 'Recruiter'),
        ('admin', 'Admin'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    
    @classmethod
    def get_pagination_optimizations(cls, queryset):
        """
        Apply pagination optimizations for User queryset.
        """
        return queryset.select_related(
            'job_seeker_profile',
            'recruiter_profile'
        ).prefetch_related(
            'user_skills__skill'
        )
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class JobSeekerProfile(models.Model):
    EXPERIENCE_LEVELS = (
        ('entry', 'Entry Level (0-2 years)'),
        ('mid', 'Mid Level (3-5 years)'),
        ('senior', 'Senior Level (6-10 years)'),
        ('lead', 'Lead Level (10+ years)'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='job_seeker_profile')
    date_of_birth = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, blank=True)
    current_position = models.CharField(max_length=255, blank=True)
    current_company = models.CharField(max_length=255, blank=True)
    expected_salary = models.IntegerField(blank=True, null=True)
    bio = models.TextField(blank=True)
    professional_summary = models.TextField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    personal_website = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    availability = models.CharField(max_length=50, blank=True)
    notice_period = models.CharField(max_length=50, blank=True)
    references = models.TextField(blank=True)
    # Relationships to new profile sections
    # (see below for models)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


# --- New Profile Section Models ---
class Education(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='education')
    degree = models.CharField(max_length=255)
    institution = models.CharField(max_length=255)
    year = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return f"{self.degree} at {self.institution}"

class WorkExperience(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='work_experience')
    job_title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    start_date = models.CharField(max_length=20, blank=True)
    end_date = models.CharField(max_length=20, blank=True)
    current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    def __str__(self):
        return f"{self.job_title} at {self.company}"

class Project(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    technologies = models.CharField(max_length=255, blank=True)
    link = models.URLField(blank=True)
    start_date = models.CharField(max_length=20, blank=True)
    end_date = models.CharField(max_length=20, blank=True)
    def __str__(self):
        return self.title

class Certification(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    issue_date = models.CharField(max_length=20, blank=True)
    expiry_date = models.CharField(max_length=20, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return self.name

class Award(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='awards')
    title = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    date = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.title

class VolunteerExperience(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='volunteer_experience')
    role = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    start_date = models.CharField(max_length=20, blank=True)
    end_date = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.role


class RecruiterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiter_profile')
    company_name = models.CharField(max_length=255)
    company_website = models.URLField(blank=True)
    company_size = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=255, blank=True)
    company_description = models.TextField(blank=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"{self.company_name} - {self.user.username}"


class Resume(models.Model):
    job_seeker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(
        upload_to='resumes/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)
    parsed_text = models.TextField(blank=True)
    file_size = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.job_seeker.username} - {self.original_filename}"


class JobPost(models.Model):
    JOB_TYPES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
    )
    
    EXPERIENCE_LEVELS = (
        ('entry', 'Entry Level (0-2 years)'),
        ('mid', 'Mid Level (3-5 years)'),
        ('senior', 'Senior Level (6-10 years)'),
        ('lead', 'Lead Level (10+ years)'),
        ('executive', 'Executive Level'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_posts')
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField(blank=True)
    location = models.CharField(max_length=255, db_index=True)
    remote_work_allowed = models.BooleanField(default=False)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, db_index=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, db_index=True)
    salary_min = models.IntegerField(blank=True, null=True, db_index=True)
    salary_max = models.IntegerField(blank=True, null=True, db_index=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    skills_required = models.TextField(help_text="Comma-separated skills", db_index=True)
    benefits = models.TextField(blank=True)
    application_deadline = models.DateTimeField(blank=True, null=True, db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.IntegerField(default=0)
    applications_count = models.IntegerField(default=0)
    
    # SEO and metadata fields
    slug = models.SlugField(max_length=300, blank=True, db_index=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['location', 'is_active']),
            models.Index(fields=['job_type', 'experience_level']),
            models.Index(fields=['salary_min', 'salary_max']),
        ]
    
    @classmethod
    def get_pagination_optimizations(cls, queryset):
        """
        Apply pagination optimizations for JobPost queryset.
        """
        return queryset.select_related(
            'recruiter',
            'recruiter__recruiter_profile'
        ).prefetch_related(
            models.Prefetch(
                'applications',
                queryset=cls.applications.related.related_model.objects.select_related('job_seeker')
            )
        )
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(f"{self.title}-{self.recruiter.recruiter_profile.company_name}")
            self.slug = base_slug[:300]
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} at {self.recruiter.recruiter_profile.company_name}"
    
    @property
    def is_expired(self):
        """Check if job posting has expired"""
        if self.application_deadline:
            return timezone.now() > self.application_deadline
        return False
    
    @property
    def days_since_posted(self):
        """Get number of days since job was posted"""
        return (timezone.now() - self.created_at).days
    
    def increment_view_count(self):
        """Increment view count atomically"""
        from django.db.models import F
        JobPost.objects.filter(id=self.id).update(views_count=F('views_count') + 1)
    
    def update_applications_count(self):
        """Update applications count"""
        self.applications_count = self.applications.count()
        self.save(update_fields=['applications_count'])


class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interviewed', 'Interviewed'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_seeker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    recruiter_notes = models.TextField(blank=True)
    match_score = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ('job_seeker', 'job_post')
        ordering = ['-applied_at']
    
    @classmethod
    def get_pagination_optimizations(cls, queryset):
        """
        Apply pagination optimizations for Application queryset.
        """
        return queryset.select_related(
            'job_seeker',
            'job_seeker__job_seeker_profile',
            'job_post',
            'job_post__recruiter__recruiter_profile',
            'resume'
        )
    
    def __str__(self):
        return f"{self.job_seeker.username} -> {self.job_post.title}"


class AIAnalysisResult(models.Model):
    ANALYSIS_TYPES = (
        ('resume_parse', 'Resume Parsing'),
        ('job_match', 'Job Matching'),
        ('skill_extraction', 'Skill Extraction'),
        ('interview_prep', 'Interview Preparation'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='ai_analyses', blank=True, null=True)
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='ai_analyses', blank=True, null=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='ai_analyses', blank=True, null=True)
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES)
    input_data = models.TextField()
    analysis_result = models.JSONField()
    confidence_score = models.FloatField(default=0.0)
    processed_at = models.DateTimeField(auto_now_add=True)
    processing_time = models.FloatField(default=0.0)  # in seconds
    
    class Meta:
        ordering = ['-processed_at']
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.processed_at}"


class InterviewSession(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    INTERVIEW_TYPES = (
        ('ai_screening', 'AI Screening'),
        ('technical', 'Technical Interview'),
        ('hr', 'HR Interview'),
        ('final', 'Final Interview'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interview_sessions')
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES)
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    interviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducted_interviews')
    meeting_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    rating = models.IntegerField(blank=True, null=True)  # 1-10 scale
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_interview_type_display()} - {self.application.job_seeker.username}"


class AIInterviewQuestion(models.Model):
    DIFFICULTY_LEVELS = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    
    QUESTION_TYPES = (
        ('technical', 'Technical'),
        ('behavioral', 'Behavioral'),
        ('situational', 'Situational'),
        ('coding', 'Coding'),
    )
    
    interview_session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='ai_questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    difficulty_level = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS)
    expected_answer = models.TextField(blank=True)
    candidate_answer = models.TextField(blank=True)
    ai_score = models.FloatField(default=0.0)
    time_taken_seconds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Q: {self.question_text[:50]}..."


class Skill(models.Model):
    SKILL_CATEGORIES = (
        ('technical', 'Technical'),
        ('soft', 'Soft Skills'),
        ('language', 'Programming Language'),
        ('framework', 'Framework/Library'),
        ('tool', 'Tool/Software'),
        ('certification', 'Certification'),
    )
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=SKILL_CATEGORIES)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class UserSkill(models.Model):
    PROFICIENCY_LEVELS = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency_level = models.CharField(max_length=20, choices=PROFICIENCY_LEVELS)
    years_of_experience = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    last_used = models.DateField(blank=True, null=True)
    
    class Meta:
        unique_together = ('user', 'skill')
    
    def __str__(self):
        return f"{self.user.username} - {self.skill.name} ({self.proficiency_level})"


class EmailVerificationToken(models.Model):
    """
    Model for email verification tokens
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)  # Token expires in 24 hours
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Email verification token for {self.user.username}"


class PasswordResetToken(models.Model):
    """
    Model for password reset tokens
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)  # Token expires in 1 hour
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Password reset token for {self.user.username}"


class JobAnalytics(models.Model):
    """
    Model for tracking job posting analytics and metrics
    """
    job_post = models.OneToOneField(JobPost, on_delete=models.CASCADE, related_name='analytics')
    total_views = models.IntegerField(default=0)
    unique_views = models.IntegerField(default=0)
    total_applications = models.IntegerField(default=0)
    conversion_rate = models.FloatField(default=0.0)  # applications/views ratio
    avg_time_on_page = models.FloatField(default=0.0)  # in seconds
    bounce_rate = models.FloatField(default=0.0)  # percentage
    top_referral_sources = models.JSONField(default=dict)  # source -> count mapping
    geographic_distribution = models.JSONField(default=dict)  # location -> count mapping
    skill_match_distribution = models.JSONField(default=dict)  # match_score_range -> count
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Job Analytics"
    
    def __str__(self):
        return f"Analytics for {self.job_post.title}"
    
    def update_conversion_rate(self):
        """Update conversion rate based on current views and applications"""
        if self.total_views > 0:
            self.conversion_rate = (self.total_applications / self.total_views) * 100
        else:
            self.conversion_rate = 0.0
        self.save(update_fields=['conversion_rate'])


class JobView(models.Model):
    """
    Model for tracking individual job post views
    """
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='job_views')
    viewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    session_id = models.CharField(max_length=40, blank=True)
    view_duration = models.IntegerField(default=0)  # in seconds
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['job_post', 'viewed_at']),
            models.Index(fields=['viewer', 'viewed_at']),
            models.Index(fields=['ip_address', 'viewed_at']),
        ]
    
    def __str__(self):
        viewer_info = self.viewer.username if self.viewer else self.ip_address
        return f"{self.job_post.title} viewed by {viewer_info}"


class Notification(models.Model):
    """
    Model for storing notification history and persistence.
    """
    NOTIFICATION_TYPES = (
        ('job_posted', 'Job Posted'),
        ('application_received', 'Application Received'),
        ('application_status_changed', 'Application Status Changed'),
        ('match_score_calculated', 'Match Score Calculated'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('system_message', 'System Message'),
        ('reminder', 'Reminder'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    
    # Related objects for context
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, null=True, blank=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True, blank=True)
    
    # Additional data as JSON
    data = models.JSONField(default=dict, blank=True)
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Expiration for temporary notifications
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['priority', 'is_read']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save(update_fields=['is_sent', 'sent_at'])
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def age_in_hours(self):
        """Get notification age in hours"""
        return (timezone.now() - self.created_at).total_seconds() / 3600


class NotificationPreference(models.Model):
    """
    Model for user notification preferences and settings.
    """
    DELIVERY_METHODS = (
        ('websocket', 'Real-time WebSocket'),
        ('email', 'Email'),
        ('both', 'Both WebSocket and Email'),
        ('none', 'Disabled'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Notification type preferences
    job_posted_enabled = models.BooleanField(default=True)
    job_posted_delivery = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='websocket')
    
    application_received_enabled = models.BooleanField(default=True)
    application_received_delivery = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='websocket')
    
    application_status_changed_enabled = models.BooleanField(default=True)
    application_status_changed_delivery = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='both')
    
    match_score_calculated_enabled = models.BooleanField(default=True)
    match_score_calculated_delivery = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='websocket')
    
    interview_scheduled_enabled = models.BooleanField(default=True)
    interview_scheduled_delivery = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='both')
    
    system_message_enabled = models.BooleanField(default=True)
    system_message_delivery = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='websocket')
    
    # General preferences
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(default='22:00')
    quiet_hours_end = models.TimeField(default='08:00')
    
    # Frequency settings
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='immediate'
    )
    
    # Timezone for scheduling
    timezone = models.CharField(max_length=50, default='UTC')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
    
    def is_notification_enabled(self, notification_type: str) -> bool:
        """Check if a specific notification type is enabled"""
        field_name = f"{notification_type}_enabled"
        return getattr(self, field_name, True)
    
    def get_delivery_method(self, notification_type: str) -> str:
        """Get delivery method for a specific notification type"""
        field_name = f"{notification_type}_delivery"
        return getattr(self, field_name, 'websocket')
    
    def is_in_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        from django.utils import timezone as tz
        import pytz
        
        try:
            user_tz = pytz.timezone(self.timezone)
            current_time = tz.now().astimezone(user_tz).time()
            
            if self.quiet_hours_start <= self.quiet_hours_end:
                # Same day quiet hours (e.g., 22:00 to 23:59)
                return self.quiet_hours_start <= current_time <= self.quiet_hours_end
            else:
                # Overnight quiet hours (e.g., 22:00 to 08:00)
                return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
        except Exception:
            # Fallback to UTC if timezone is invalid
            return False


class NotificationTemplate(models.Model):
    """
    Model for notification message templates and formatting.
    """
    TEMPLATE_TYPES = (
        ('job_posted', 'Job Posted'),
        ('application_received', 'Application Received'),
        ('application_status_changed', 'Application Status Changed'),
        ('match_score_calculated', 'Match Score Calculated'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('system_message', 'System Message'),
        ('reminder', 'Reminder'),
    )
    
    DELIVERY_CHANNELS = (
        ('websocket', 'WebSocket'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
    )
    
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES)
    delivery_channel = models.CharField(max_length=20, choices=DELIVERY_CHANNELS)
    
    # Template content
    title_template = models.CharField(max_length=255)
    message_template = models.TextField()
    
    # Email-specific templates
    email_subject_template = models.CharField(max_length=255, blank=True)
    email_html_template = models.TextField(blank=True)
    
    # Template variables documentation
    available_variables = models.JSONField(
        default=dict,
        help_text="JSON object documenting available template variables"
    )
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('template_type', 'delivery_channel', 'is_default')
        indexes = [
            models.Index(fields=['template_type', 'delivery_channel']),
            models.Index(fields=['is_active', 'is_default']),
        ]
    
    def __str__(self):
        return f"{self.get_template_type_display()} - {self.get_delivery_channel_display()}"
    
    def render_title(self, context: dict) -> str:
        """Render title template with context variables"""
        try:
            return self.title_template.format(**context)
        except (KeyError, ValueError) as e:
            return f"Notification (template error: {e})"
    
    def render_message(self, context: dict) -> str:
        """Render message template with context variables"""
        try:
            return self.message_template.format(**context)
        except (KeyError, ValueError) as e:
            return f"Notification message (template error: {e})"
    
    def render_email_subject(self, context: dict) -> str:
        """Render email subject template with context variables"""
        if not self.email_subject_template:
            return self.render_title(context)
        try:
            return self.email_subject_template.format(**context)
        except (KeyError, ValueError) as e:
            return f"Email notification (template error: {e})"
    
    def render_email_html(self, context: dict) -> str:
        """Render email HTML template with context variables"""
        if not self.email_html_template:
            return self.render_message(context)
        try:
            return self.email_html_template.format(**context)
        except (KeyError, ValueError) as e:
            return f"<p>Email notification (template error: {e})</p>"


class ResumeTemplate(models.Model):
    """
    Model for resume templates used in the resume builder.
    """
    TEMPLATE_CATEGORIES = [
        ('professional', 'Professional'),
        ('creative', 'Creative'),
        ('modern', 'Modern'),
        ('classic', 'Classic'),
        ('academic', 'Academic'),
        ('technical', 'Technical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=TEMPLATE_CATEGORIES, default='professional')
    template_data = models.JSONField(default=dict, help_text="Template structure and styling data")
    preview_image = models.ImageField(upload_to='resume_templates/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'matcher_resumetemplate'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Conversation(models.Model):
    """
    Model for conversations between users (messaging system).
    """
    CONVERSATION_TYPES = [
        ('direct', 'Direct Message'),
        ('job_inquiry', 'Job Inquiry'),
        ('interview', 'Interview Discussion'),
        ('support', 'Support Ticket'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    conversation_type = models.CharField(max_length=20, choices=CONVERSATION_TYPES, default='direct')
    subject = models.CharField(max_length=255, blank=True)
    related_job = models.ForeignKey(JobPost, on_delete=models.SET_NULL, null=True, blank=True)
    related_application = models.ForeignKey(Application, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'matcher_conversation'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['conversation_type', 'is_active']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        participant_names = ", ".join([p.username for p in self.participants.all()[:2]])
        return f"{self.get_conversation_type_display()}: {participant_names}"
    
    @property
    def last_message(self):
        """Get the last message in this conversation"""
        return self.messages.order_by('-sent_at').first()
    
    @property
    def unread_count_for_user(self, user):
        """Get unread message count for a specific user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """
    Model for individual messages within conversations.
    """
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('file', 'File Attachment'),
        ('image', 'Image'),
        ('system', 'System Message'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    attachment = models.FileField(upload_to='message_attachments/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'matcher_message'
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['conversation', 'sent_at']),
            models.Index(fields=['sender', 'sent_at']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.sent_at}"
    
    def mark_as_read(self, user=None):
        """Mark message as read"""
        if not self.is_read and (user is None or user != self.sender):
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class ResumeTemplate(models.Model):
    """
    Model for resume templates used in the resume builder.
    """
    TEMPLATE_CATEGORIES = [
        ('professional', 'Professional'),
        ('creative', 'Creative'),
        ('modern', 'Modern'),
        ('classic', 'Classic'),
        ('academic', 'Academic'),
        ('technical', 'Technical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=TEMPLATE_CATEGORIES, default='professional')
    template_data = models.JSONField(default=dict, help_text="Template structure and styling data")
    preview_image = models.ImageField(upload_to='resume_templates/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    version = models.CharField(max_length=20, default='1.0')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(default=0)
    
    # Template sections configuration
    sections = models.JSONField(default=list, help_text="List of available sections for this template")
    
    class Meta:
        db_table = 'matcher_resumetemplate'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_premium', 'is_active']),
            models.Index(fields=['usage_count']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    def increment_usage_count(self):
        """Increment usage count atomically"""
        from django.db.models import F
        ResumeTemplate.objects.filter(id=self.id).update(usage_count=F('usage_count') + 1)
    
    @property
    def is_popular(self):
        """Check if template is popular based on usage"""
        return self.usage_count > 100
    
    def get_default_sections(self):
        """Get default sections for this template"""
        if not self.sections:
            return [
                {'name': 'personal_info', 'title': 'Personal Information', 'required': True, 'order': 1},
                {'name': 'summary', 'title': 'Professional Summary', 'required': False, 'order': 2},
                {'name': 'experience', 'title': 'Work Experience', 'required': True, 'order': 3},
                {'name': 'education', 'title': 'Education', 'required': True, 'order': 4},
                {'name': 'skills', 'title': 'Skills', 'required': False, 'order': 5},
                {'name': 'certifications', 'title': 'Certifications', 'required': False, 'order': 6},
                {'name': 'projects', 'title': 'Projects', 'required': False, 'order': 7},
            ]
        return self.sections


class ResumeTemplateVersion(models.Model):
    """
    Model for tracking resume template versions and changes.
    """
    template = models.ForeignKey(ResumeTemplate, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=20)
    template_data = models.JSONField()
    sections = models.JSONField(default=list)
    change_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'matcher_resumetemplateversion'
        unique_together = ('template', 'version_number')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.template.name} v{self.version_number}"
    
    def make_current(self):
        """Make this version the current version"""
        # Set all other versions to not current
        ResumeTemplateVersion.objects.filter(template=self.template).update(is_current=False)
        # Set this version as current
        self.is_current = True
        self.save(update_fields=['is_current'])
        # Update the main template
        self.template.version = self.version_number
        self.template.template_data = self.template_data
        self.template.sections = self.sections
        self.template.save(update_fields=['version', 'template_data', 'sections'])


class UserResumeTemplate(models.Model):
    """
    Model for tracking user's customized resume templates.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resume_templates')
    base_template = models.ForeignKey(ResumeTemplate, on_delete=models.CASCADE, related_name='user_customizations')
    name = models.CharField(max_length=255)
    customized_data = models.JSONField(default=dict, help_text="User's customizations to the base template")
    customized_sections = models.JSONField(default=list, help_text="User's customized sections")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'matcher_userresumetemplate'
        unique_together = ('user', 'name')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def get_merged_template_data(self):
        """Get template data merged with user customizations"""
        import copy
        
        # Deep copy the base template data
        base_data = copy.deepcopy(self.base_template.template_data)
        
        # Deep merge customized data
        def deep_merge(base_dict, custom_dict):
            for key, value in custom_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_merge(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_merge(base_data, self.customized_data)
        return base_data
    
    def get_merged_sections(self):
        """Get sections merged with user customizations"""
        if self.customized_sections:
            return self.customized_sections
        return self.base_template.get_default_sections()