from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser


class IsJobSeeker(permissions.BasePermission):
    """
    Custom permission to only allow job seekers to access certain views.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'job_seeker'
        )


class IsRecruiter(permissions.BasePermission):
    """
    Custom permission to only allow recruiters to access certain views.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'recruiter'
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsJobSeekerOwner(permissions.BasePermission):
    """
    Custom permission for job seeker specific resources.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'job_seeker'
        )
    
    def has_object_permission(self, request, view, obj):
        # Check if the object belongs to the job seeker
        if hasattr(obj, 'job_seeker'):
            return obj.job_seeker == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsRecruiterOwner(permissions.BasePermission):
    """
    Custom permission for recruiter specific resources.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'recruiter'
        )
    
    def has_object_permission(self, request, view, obj):
        # Check if the object belongs to the recruiter
        if hasattr(obj, 'recruiter'):
            return obj.recruiter == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsApplicationOwner(permissions.BasePermission):
    """
    Custom permission for application resources - accessible by both job seeker and recruiter.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type in ['job_seeker', 'recruiter']
        )
    
    def has_object_permission(self, request, view, obj):
        # Job seeker can access their own applications
        if request.user.user_type == 'job_seeker':
            return obj.job_seeker == request.user
        # Recruiter can access applications for their job posts
        elif request.user.user_type == 'recruiter':
            return obj.job_post.recruiter == request.user
        return False


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication class with enhanced error handling
    """
    
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except TokenError as e:
            # Log the token error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"JWT Token Error: {str(e)}")
            return None
        except InvalidToken as e:
            # Log the invalid token for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid JWT Token: {str(e)}")
            return None
    
    def get_user(self, validated_token):
        """
        Override to add additional user validation
        """
        try:
            user = super().get_user(validated_token)
            
            # Additional checks
            if not user.is_active:
                raise InvalidToken('User account is disabled')
            
            return user
        except Exception as e:
            raise InvalidToken(f'Token contained no recognizable user identification: {str(e)}')


class RoleBasedPermission(permissions.BasePermission):
    """
    Permission class that checks user roles based on view action
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Define role-based access rules
        role_permissions = {
            'job_seeker': [
                'list', 'retrieve', 'create', 'update', 'partial_update',
                'apply', 'recommendations', 'dashboard_stats'
            ],
            'recruiter': [
                'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy',
                'applications', 'update_status', 'dashboard_stats'
            ],
            'admin': ['*']  # Admin has access to everything
        }
        
        user_role = request.user.user_type
        allowed_actions = role_permissions.get(user_role, [])
        
        # Admin has access to everything
        if user_role == 'admin' or '*' in allowed_actions:
            return True
        
        # Check if the current action is allowed for the user's role
        current_action = getattr(view, 'action', None)
        return current_action in allowed_actions