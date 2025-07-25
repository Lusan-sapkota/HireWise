from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost,
    Application, AIAnalysisResult, InterviewSession, Skill, UserSkill,
    EmailVerificationToken, PasswordResetToken, JobAnalytics, JobView
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
