from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost,
    Application, AIAnalysisResult, InterviewSession, Skill, UserSkill
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
    applications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = JobPost
        fields = '__all__'
        read_only_fields = ['id', 'recruiter', 'created_at', 'updated_at', 'views_count']
    
    def get_applications_count(self, obj):
        return obj.applications.count()


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
