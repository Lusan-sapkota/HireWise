from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from .serializers import UserSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes user role information in the token
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims to the token
        token['user_type'] = user.user_type
        token['user_id'] = str(user.id)
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_verified'] = user.is_verified
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user information to the response
        user_data = UserSerializer(self.user).data
        data['user'] = user_data
        data['message'] = 'Login successful'
        
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom JWT refresh serializer with additional validation
    """
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom response data
        data['message'] = 'Token refreshed successfully'
        
        return data


class JWTRegistrationSerializer(serializers.ModelSerializer):
    """
    Registration serializer that returns JWT tokens
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'user_type', 
                 'first_name', 'last_name', 'phone_number']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"non_field_errors": ["Passwords don't match"]})
        
        # Validate user_type
        if data['user_type'] not in ['job_seeker', 'recruiter']:
            raise serializers.ValidationError({"non_field_errors": ["Invalid user type"]})
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user
    
    def to_representation(self, instance):
        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(instance)
        access = refresh.access_token
        
        # Add custom claims
        access['user_type'] = instance.user_type
        access['user_id'] = str(instance.id)
        access['username'] = instance.username
        access['email'] = instance.email
        access['first_name'] = instance.first_name
        access['last_name'] = instance.last_name
        access['is_verified'] = instance.is_verified
        
        return {
            'refresh': str(refresh),
            'access': str(access),
            'user': UserSerializer(instance).data,
            'message': 'Registration successful'
        }


class JWTLoginSerializer(serializers.Serializer):
    """
    Login serializer that returns JWT tokens
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            # Add custom claims
            access['user_type'] = user.user_type
            access['user_id'] = str(user.id)
            access['username'] = user.username
            access['email'] = user.email
            access['first_name'] = user.first_name
            access['last_name'] = user.last_name
            access['is_verified'] = user.is_verified
            
            data['refresh'] = str(refresh)
            data['access'] = str(access)
            data['user'] = UserSerializer(user).data
            data['message'] = 'Login successful'
            
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return data