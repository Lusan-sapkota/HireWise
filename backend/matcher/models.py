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
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    bio = models.TextField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    availability = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


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
