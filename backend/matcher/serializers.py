from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost,
    Application, AIAnalysisResult, InterviewSession, Skill, UserSkill,
    EmailVerificationToken, PasswordResetToken, JobAnalytics, JobView,
    Notification, ResumeTemplate, ResumeTemplateVersion, UserResumeTemplate,
    Conversation, Message
)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'user_type', 
                 'first_name', 'last_name', 'phone_number']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            data['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'user_type', 'phone_number', 'profile_picture', 'is_verified']
        read_only_fields = ['id', 'is_verified']


class JobSeekerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = JobSeekerProfile
        fields = '__all__'
        read_only_fields = ['user']


class RecruiterProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = RecruiterProfile
        fields = '__all__'
        read_only_fields = ['user']


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'file', 'original_filename', 'uploaded_at', 'is_primary', 'file_size']
        read_only_fields = ['id', 'uploaded_at', 'file_size', 'parsed_text']


class JobPostSerializer(serializers.ModelSerializer):
    recruiter_name = serializers.CharField(source='recruiter.username', read_only=True)
    company_name = serializers.CharField(source='recruiter.recruiter_profile.company_name', read_only=True)
    company_logo = serializers.ImageField(source='recruiter.recruiter_profile.company_logo', read_only=True)
    applications_count = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()
    days_since_posted = serializers.ReadOnlyField()
    skills_list = serializers.SerializerMethodField()
    
    class Meta:
        model = JobPost
        fields = '__all__'
        read_only_fields = [
            'id', 'recruiter', 'created_at', 'updated_at', 'views_count', 
            'applications_count', 'slug', 'is_expired', 'days_since_posted'
        ]
    
    def get_applications_count(self, obj):
        return obj.applications.count()
    
    def get_skills_list(self, obj):
        """Convert comma-separated skills to list"""
        if obj.skills_required:
            return [skill.strip() for skill in obj.skills_required.split(',') if skill.strip()]
        return []
    
    def validate_salary_min(self, value):
        """Validate minimum salary"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Minimum salary cannot be negative")
        return value
    
    def validate_salary_max(self, value):
        """Validate maximum salary"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Maximum salary cannot be negative")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        salary_min = data.get('salary_min')
        salary_max = data.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise serializers.ValidationError({
                'salary_max': 'Maximum salary must be greater than minimum salary'
            })
        
        # Validate application deadline
        application_deadline = data.get('application_deadline')
        if application_deadline and application_deadline <= timezone.now():
            raise serializers.ValidationError({
                'application_deadline': 'Application deadline must be in the future'
            })
        
        return data


class JobPostCreateSerializer(JobPostSerializer):
    """Serializer for creating job posts with additional validation"""
    
    def validate_title(self, value):
        """Validate job title"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Job title must be at least 3 characters long")
        return value.strip()
    
    def validate_description(self, value):
        """Validate job description"""
        if len(value.strip()) < 50:
            raise serializers.ValidationError("Job description must be at least 50 characters long")
        return value.strip()
    
    def validate_requirements(self, value):
        """Validate job requirements"""
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Job requirements must be at least 20 characters long")
        return value.strip()
    
    def validate(self, data):
        """Cross-field validation for job post creation"""
        # Call parent validation first
        data = super().validate(data)
        
        # Additional validation for required fields during creation
        required_fields = ['location', 'job_type', 'experience_level', 'skills_required']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError({field: 'This field is required.'})
        
        return data


class JobPostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for job post listings"""
    recruiter_name = serializers.CharField(source='recruiter.username', read_only=True)
    company_name = serializers.CharField(source='recruiter.recruiter_profile.company_name', read_only=True)
    company_logo = serializers.ImageField(source='recruiter.recruiter_profile.company_logo', read_only=True)
    is_expired = serializers.ReadOnlyField()
    days_since_posted = serializers.ReadOnlyField()
    skills_list = serializers.SerializerMethodField()
    
    class Meta:
        model = JobPost
        fields = [
            'id', 'title', 'company_name', 'company_logo', 'recruiter_name', 'location', 'job_type',
            'experience_level', 'salary_min', 'salary_max', 'salary_currency',
            'skills_list', 'is_active', 'is_featured', 'created_at', 'views_count',
            'applications_count', 'is_expired', 'days_since_posted', 'slug'
        ]
    
    def get_skills_list(self, obj):
        """Convert comma-separated skills to list (limited to first 5)"""
        if obj.skills_required:
            skills = [skill.strip() for skill in obj.skills_required.split(',') if skill.strip()]
            return skills[:5]  # Limit to first 5 skills for list view
        return []


class JobAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for job analytics data"""
    
    class Meta:
        model = JobAnalytics
        fields = '__all__'
        read_only_fields = ['job_post', 'created_at', 'updated_at']


class JobViewSerializer(serializers.ModelSerializer):
    """Serializer for job view tracking"""
    viewer_name = serializers.CharField(source='viewer.username', read_only=True)
    
    class Meta:
        model = JobView
        fields = '__all__'
        read_only_fields = ['viewed_at']


class ApplicationSerializer(serializers.ModelSerializer):
    job_seeker_name = serializers.CharField(source='job_seeker.username', read_only=True)
    job_title = serializers.CharField(source='job_post.title', read_only=True)
    company_name = serializers.CharField(source='job_post.recruiter.recruiter_profile.company_name', read_only=True)
    
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ['id', 'applied_at', 'updated_at', 'match_score']


class AIAnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAnalysisResult
        fields = '__all__'
        read_only_fields = ['id', 'processed_at', 'processing_time']


class InterviewSessionSerializer(serializers.ModelSerializer):
    job_seeker_name = serializers.CharField(source='application.job_seeker.username', read_only=True)
    job_title = serializers.CharField(source='application.job_post.title', read_only=True)
    
    class Meta:
        model = InterviewSession
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class UserSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_category = serializers.CharField(source='skill.category', read_only=True)
    
    class Meta:
        model = UserSkill
        fields = '__all__'
        read_only_fields = ['user']


class JobMatchSerializer(serializers.Serializer):
    job_post = JobPostSerializer(read_only=True)
    match_score = serializers.FloatField()
    matching_skills = serializers.ListField(child=serializers.CharField())
    missing_skills = serializers.ListField(child=serializers.CharField())
    recommendations = serializers.CharField()


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification request
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.is_verified:
                raise serializers.ValidationError("Email is already verified")
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist")
        return value


class EmailVerificationConfirmSerializer(serializers.Serializer):
    """
    Serializer for email verification confirmation
    """
    token = serializers.CharField(max_length=64)
    
    def validate_token(self, value):
        try:
            verification_token = EmailVerificationToken.objects.get(token=value, is_used=False)
            if verification_token.is_expired():
                raise serializers.ValidationError("Verification token has expired")
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation
    """
    token = serializers.CharField(max_length=64)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_token(self, value):
        try:
            reset_token = PasswordResetToken.objects.get(token=value, is_used=False)
            if reset_token.is_expired():
                raise serializers.ValidationError("Reset token has expired")
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid reset token")
        return value
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match"})
        
        # Validate password strength
        try:
            validate_password(data['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password while authenticated
    """
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match"})
        
        # Validate password strength
        try:
            validate_password(data['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})
        
        return data


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'profile_picture']
    
    def validate_phone_number(self, value):
        if value and len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value
    
    def validate_profile_picture(self, value):
        """Validate profile picture upload"""
        if value:
            # Import file validation utilities
            from .file_utils import FileSecurityValidator
            from .file_optimization import FileOptimizer
            
            # Validate file security
            validation_result = FileSecurityValidator.validate_file(value, 'image')
            if not validation_result['is_valid']:
                raise serializers.ValidationError(
                    f"Invalid image file: {', '.join(validation_result['errors'])}"
                )
            
            # Check file size (5MB limit)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image file size must be less than 5MB")
            
            # Optimize and resize image
            try:
                optimizer = FileOptimizer()
                optimized_file, _ = optimizer.optimize_file(value)
                return optimized_file
            except Exception as e:
                raise serializers.ValidationError(f"Error processing image: {str(e)}")
        
        return value

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'notification_type', 'title', 'message',
            'is_read', 'read_at', 'data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add human-readable notification type
        data['notification_type_display'] = instance.get_notification_type_display()
        return data


class ResumeTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ResumeTemplate model"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    default_sections = serializers.SerializerMethodField()
    is_popular = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ResumeTemplate
        fields = [
            'id', 'name', 'description', 'category', 'category_display',
            'template_data', 'preview_image', 'is_active', 'is_premium',
            'version', 'created_by', 'created_by_name', 'created_at',
            'updated_at', 'usage_count', 'sections', 'default_sections',
            'is_popular'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'usage_count']
    
    def get_default_sections(self, obj):
        """Get default sections for the template"""
        return obj.get_default_sections()
    
    def validate_template_data(self, value):
        """Validate template data structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Template data must be a valid JSON object")
        
        required_keys = ['styles', 'layout']
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(f"Template data must contain '{key}' key")
        
        return value
    
    def validate_sections(self, value):
        """Validate sections structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Sections must be a list")
        
        for section in value:
            if not isinstance(section, dict):
                raise serializers.ValidationError("Each section must be a dictionary")
            
            required_keys = ['name', 'title', 'required', 'order']
            for key in required_keys:
                if key not in section:
                    raise serializers.ValidationError(f"Section must contain '{key}' key")
        
        return value


class ResumeTemplateVersionSerializer(serializers.ModelSerializer):
    """Serializer for ResumeTemplateVersion model"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ResumeTemplateVersion
        fields = [
            'id', 'template', 'template_name', 'version_number',
            'template_data', 'sections', 'change_notes', 'created_by',
            'created_by_name', 'created_at', 'is_current'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_version_number(self, value):
        """Validate version number format"""
        import re
        if not re.match(r'^\d+\.\d+(\.\d+)?$', value):
            raise serializers.ValidationError("Version number must be in format X.Y or X.Y.Z")
        return value


class UserResumeTemplateSerializer(serializers.ModelSerializer):
    """Serializer for UserResumeTemplate model"""
    base_template_name = serializers.CharField(source='base_template.name', read_only=True)
    base_template_category = serializers.CharField(source='base_template.category', read_only=True)
    merged_template_data = serializers.SerializerMethodField()
    merged_sections = serializers.SerializerMethodField()
    
    class Meta:
        model = UserResumeTemplate
        fields = [
            'id', 'user', 'base_template', 'base_template_name',
            'base_template_category', 'name', 'customized_data',
            'customized_sections', 'merged_template_data', 'merged_sections',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_merged_template_data(self, obj):
        """Get merged template data"""
        return obj.get_merged_template_data()
    
    def get_merged_sections(self, obj):
        """Get merged sections"""
        return obj.get_merged_sections()
    
    def validate_name(self, value):
        """Validate template name uniqueness for user"""
        user = self.context['request'].user
        if UserResumeTemplate.objects.filter(user=user, name=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("You already have a template with this name")
        return value


class ResumeTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for resume template listings"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    is_popular = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ResumeTemplate
        fields = [
            'id', 'name', 'description', 'category', 'category_display',
            'preview_image', 'is_premium', 'usage_count', 'is_popular',
            'created_at'
        ]


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model"""
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'participants', 'conversation_type', 'subject',
            'related_job', 'related_application', 'is_active',
            'last_message', 'unread_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        last_msg = obj.last_message
        if last_msg:
            return {
                'id': str(last_msg.id),
                'content': last_msg.content,
                'sender': last_msg.sender.username,
                'sent_at': last_msg.sent_at
            }
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model"""
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'content', 'message_type',
            'attachment', 'is_read', 'read_at', 'sent_at', 'edited_at'
        ]
        read_only_fields = ['id', 'sender', 'sent_at', 'edited_at']
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


# =============================================================================
# AI RESUME ASSISTANCE SERIALIZERS
# =============================================================================

class ResumeAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for resume analysis requests"""
    resume_content = serializers.CharField(required=True, min_length=50)
    target_job = serializers.CharField(required=False, allow_blank=True)
    job_requirements = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        allow_empty=True
    )
    
    def validate_resume_content(self, value):
        if len(value.split()) < 20:
            raise serializers.ValidationError("Resume content is too short for meaningful analysis")
        return value


class ResumeJobAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for resume-job analysis requests"""
    resume_id = serializers.UUIDField(required=True)
    job_id = serializers.UUIDField(required=True)
    
    def validate_resume_id(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.user_type == 'job_seeker':
                if not Resume.objects.filter(id=value, job_seeker=request.user).exists():
                    raise serializers.ValidationError("Resume not found or access denied")
            else:
                if not Resume.objects.filter(id=value).exists():
                    raise serializers.ValidationError("Resume not found")
        return value
    
    def validate_job_id(self, value):
        if not JobPost.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Job post not found or inactive")
        return value


class SkillGapAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for skill gap analysis requests"""
    resume_content = serializers.CharField(required=True, min_length=50)
    job_requirements = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=True,
        min_length=1
    )
    
    def validate_job_requirements(self, value):
        if not value:
            raise serializers.ValidationError("At least one job requirement is required")
        return value


class KeywordOptimizationRequestSerializer(serializers.Serializer):
    """Serializer for keyword optimization requests"""
    resume_content = serializers.CharField(required=True, min_length=50)
    target_job = serializers.CharField(required=False, allow_blank=True)
    job_requirements = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        allow_empty=True
    )
    
    def validate(self, data):
        if not data.get('target_job') and not data.get('job_requirements'):
            raise serializers.ValidationError(
                "Either target_job or job_requirements must be provided"
            )
        return data


class ResumeScoreRequestSerializer(serializers.Serializer):
    """Serializer for resume scoring requests"""
    resume_content = serializers.CharField(required=True, min_length=50)


class ResumeContentSuggestionsRequestSerializer(serializers.Serializer):
    """Serializer for resume content suggestions requests"""
    job_title = serializers.CharField(required=True, max_length=255)
    experience_level = serializers.ChoiceField(
        choices=['entry', 'mid', 'senior', 'lead'],
        required=True
    )
    skills = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    industry = serializers.CharField(required=False, allow_blank=True, max_length=100)
    
    def validate_job_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Job title must be at least 3 characters long")
        return value.strip()


class ResumeAnalysisResponseSerializer(serializers.Serializer):
    """Serializer for resume analysis responses"""
    success = serializers.BooleanField()
    overall_score = serializers.FloatField(required=False)
    category_scores = serializers.DictField(required=False)
    strengths = serializers.ListField(child=serializers.CharField(), required=False)
    weaknesses = serializers.ListField(child=serializers.CharField(), required=False)
    suggestions = serializers.ListField(child=serializers.CharField(), required=False)
    keyword_analysis = serializers.DictField(required=False)
    skill_gap_analysis = serializers.DictField(required=False)
    improvement_recommendations = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    processing_time = serializers.FloatField(required=False)
    error = serializers.CharField(required=False)


class SkillGapAnalysisResponseSerializer(serializers.Serializer):
    """Serializer for skill gap analysis responses"""
    success = serializers.BooleanField()
    alignment_score = serializers.FloatField(required=False)
    technical_skills = serializers.DictField(required=False)
    soft_skills = serializers.DictField(required=False)
    certifications = serializers.DictField(required=False)
    priority_gaps = serializers.ListField(child=serializers.CharField(), required=False)
    error = serializers.CharField(required=False)


class KeywordOptimizationResponseSerializer(serializers.Serializer):
    """Serializer for keyword optimization responses"""
    success = serializers.BooleanField()
    score = serializers.FloatField(required=False)
    found_keywords = serializers.ListField(child=serializers.CharField(), required=False)
    missing_keywords = serializers.ListField(child=serializers.CharField(), required=False)
    industry = serializers.CharField(required=False)
    keyword_density = serializers.FloatField(required=False)
    error = serializers.CharField(required=False)


class ResumeScoreResponseSerializer(serializers.Serializer):
    """Serializer for resume scoring responses"""
    success = serializers.BooleanField()
    overall_score = serializers.FloatField(required=False)
    category_scores = serializers.DictField(required=False)
    strengths = serializers.ListField(child=serializers.CharField(), required=False)
    weaknesses = serializers.ListField(child=serializers.CharField(), required=False)
    word_count = serializers.IntegerField(required=False)
    character_count = serializers.IntegerField(required=False)
    error = serializers.CharField(required=False)


class ResumeContentSuggestionsResponseSerializer(serializers.Serializer):
    """Serializer for resume content suggestions responses"""
    success = serializers.BooleanField()
    suggestions = serializers.DictField(required=False)
    job_title = serializers.CharField(required=False)
    experience_level = serializers.CharField(required=False)
    industry = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class ResumeAnalysisHistorySerializer(serializers.ModelSerializer):
    """Serializer for resume analysis history"""
    job_post = serializers.SerializerMethodField()
    
    class Meta:
        model = AIAnalysisResult
        fields = [
            'id', 'analysis_type', 'processed_at', 'confidence_score',
            'processing_time', 'analysis_result', 'job_post'
        ]
        read_only_fields = ['id', 'processed_at']
    
    def get_job_post(self, obj):
        if obj.job_post:
            return {
                'id': str(obj.job_post.id),
                'title': obj.job_post.title,
                'company': (obj.job_post.recruiter.recruiter_profile.company_name 
                           if hasattr(obj.job_post.recruiter, 'recruiter_profile') 
                           else 'Unknown')
            }
        return None
        return super().create(validated_data)