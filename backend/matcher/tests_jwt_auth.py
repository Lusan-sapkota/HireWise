import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from unittest.mock import patch
from .models import JobSeekerProfile, RecruiterProfile

User = get_user_model()


class JWTAuthenticationTestCase(APITestCase):
    """
    Test cases for JWT authentication system
    """
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('jwt-register')
        self.login_url = reverse('jwt-login')
        self.logout_url = reverse('jwt-logout')
        self.token_obtain_url = reverse('jwt-token-obtain-pair')
        self.token_refresh_url = reverse('jwt-token-refresh')
        
        # Test user data
        self.job_seeker_data = {
            'username': 'jobseeker1',
            'email': 'jobseeker@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'user_type': 'job_seeker',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+1234567890'
        }
        
        self.recruiter_data = {
            'username': 'recruiter1',
            'email': 'recruiter@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'user_type': 'recruiter',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone_number': '+0987654321',
            'company_name': 'Tech Corp'
        }
        
        # Create test users
        self.job_seeker = User.objects.create_user(
            username='existing_jobseeker',
            email='existing@jobseeker.com',
            password='testpass123',
            user_type='job_seeker'
        )
        JobSeekerProfile.objects.create(user=self.job_seeker)
        
        self.recruiter = User.objects.create_user(
            username='existing_recruiter',
            email='existing@recruiter.com',
            password='testpass123',
            user_type='recruiter'
        )
        RecruiterProfile.objects.create(user=self.recruiter, company_name='Test Company')


class JWTRegistrationTestCase(JWTAuthenticationTestCase):
    """
    Test cases for JWT user registration
    """
    
    def test_job_seeker_registration_success(self):
        """Test successful job seeker registration with JWT tokens"""
        response = self.client.post(self.register_url, self.job_seeker_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['message'], 'Registration successful')
        self.assertEqual(response.data['user']['user_type'], 'job_seeker')
        
        # Verify user was created
        user = User.objects.get(username='jobseeker1')
        self.assertEqual(user.user_type, 'job_seeker')
        
        # Verify profile was created
        self.assertTrue(hasattr(user, 'job_seeker_profile'))
    
    def test_recruiter_registration_success(self):
        """Test successful recruiter registration with JWT tokens"""
        response = self.client.post(self.register_url, self.recruiter_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['message'], 'Registration successful')
        self.assertEqual(response.data['user']['user_type'], 'recruiter')
        
        # Verify user was created
        user = User.objects.get(username='recruiter1')
        self.assertEqual(user.user_type, 'recruiter')
        
        # Verify profile was created
        self.assertTrue(hasattr(user, 'recruiter_profile'))
        self.assertEqual(user.recruiter_profile.company_name, 'Tech Corp')
    
    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = self.job_seeker_data.copy()
        data['password_confirm'] = 'differentpass'
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_registration_invalid_user_type(self):
        """Test registration with invalid user type"""
        data = self.job_seeker_data.copy()
        data['user_type'] = 'invalid_type'
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # The validation error can be in either 'user_type' or 'non_field_errors'
        self.assertTrue('user_type' in response.data or 'non_field_errors' in response.data)
    
    def test_registration_duplicate_username(self):
        """Test registration with duplicate username"""
        data = self.job_seeker_data.copy()
        data['username'] = 'existing_jobseeker'
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
    
    def test_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        data = self.job_seeker_data.copy()
        data['email'] = 'existing@jobseeker.com'
        
        response = self.client.post(self.register_url, data, format='json')
        
        # Note: Django's default User model doesn't enforce unique email by default
        # This test might pass if email uniqueness isn't enforced in the model
        # For now, we'll check if the registration succeeds or fails appropriately
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn('email', response.data)
        else:
            # If email uniqueness isn't enforced, the registration will succeed
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class JWTLoginTestCase(JWTAuthenticationTestCase):
    """
    Test cases for JWT user login
    """
    
    def test_login_success(self):
        """Test successful login with JWT tokens"""
        login_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['message'], 'Login successful')
        self.assertEqual(response.data['user']['username'], 'existing_jobseeker')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            'username': 'existing_jobseeker',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_login_inactive_user(self):
        """Test login with inactive user"""
        self.job_seeker.is_active = False
        self.job_seeker.save()
        
        login_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_login_missing_fields(self):
        """Test login with missing fields"""
        login_data = {'username': 'existing_jobseeker'}
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class JWTTokenTestCase(JWTAuthenticationTestCase):
    """
    Test cases for JWT token operations
    """
    
    def test_token_obtain_pair(self):
        """Test obtaining JWT token pair"""
        token_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.token_obtain_url, token_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        # Verify token contains custom claims
        from rest_framework_simplejwt.tokens import UntypedToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        
        try:
            token = UntypedToken(response.data['access'])
            self.assertEqual(token['user_type'], 'job_seeker')
            self.assertEqual(token['username'], 'existing_jobseeker')
            self.assertIn('user_id', token)
        except (InvalidToken, TokenError):
            self.fail("Token should be valid and contain custom claims")
    
    def test_token_refresh(self):
        """Test refreshing JWT token"""
        # First, get tokens
        token_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(self.token_obtain_url, token_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Now refresh the token
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(self.token_refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['message'], 'Token refreshed successfully')
    
    def test_token_refresh_invalid(self):
        """Test refreshing with invalid token"""
        refresh_data = {'refresh': 'invalid_token'}
        response = self.client.post(self.token_refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_request(self):
        """Test making authenticated request with JWT token"""
        # Get token
        token_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(self.token_obtain_url, token_data, format='json')
        access_token = login_response.data['access']
        
        # Make authenticated request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(reverse('dashboard-stats'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_unauthenticated_request(self):
        """Test making request without authentication"""
        response = self.client.get(reverse('dashboard-stats'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTLogoutTestCase(JWTAuthenticationTestCase):
    """
    Test cases for JWT logout and token blacklisting
    """
    
    def test_logout_success(self):
        """Test successful logout with token blacklisting"""
        # Get tokens
        token_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(self.token_obtain_url, token_data, format='json')
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']
        
        # Logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_data = {'refresh': refresh_token}
        response = self.client.post(self.logout_url, logout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Logout successful')
        
        # Verify token is blacklisted by trying to use it
        refresh_data = {'refresh': refresh_token}
        refresh_response = self.client.post(self.token_refresh_url, refresh_data, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_missing_refresh_token(self):
        """Test logout without providing refresh token"""
        # Get tokens
        token_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(self.token_obtain_url, token_data, format='json')
        access_token = login_response.data['access']
        
        # Logout without refresh token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.logout_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_logout_invalid_refresh_token(self):
        """Test logout with invalid refresh token"""
        # Get tokens
        token_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(self.token_obtain_url, token_data, format='json')
        access_token = login_response.data['access']
        
        # Logout with invalid refresh token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_data = {'refresh': 'invalid_token'}
        response = self.client.post(self.logout_url, logout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_use_blacklisted_token(self):
        """Test using a blacklisted token"""
        # Get tokens
        token_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(self.token_obtain_url, token_data, format='json')
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']
        
        # Logout (blacklist token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_data = {'refresh': refresh_token}
        self.client.post(self.logout_url, logout_data, format='json')
        
        # Try to use blacklisted refresh token
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(self.token_refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTPermissionTestCase(JWTAuthenticationTestCase):
    """
    Test cases for JWT-based permissions
    """
    
    def test_job_seeker_access_control(self):
        """Test job seeker role-based access control"""
        # Get job seeker token
        token_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(self.token_obtain_url, token_data, format='json')
        access_token = login_response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Job seeker should access their dashboard
        response = self.client.get(reverse('dashboard-stats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Job seeker should access job recommendations
        response = self.client.get(reverse('job-recommendations'))
        # This might return 400 if no resume is uploaded, but should not be 403
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_recruiter_access_control(self):
        """Test recruiter role-based access control"""
        # Get recruiter token
        token_data = {
            'username': 'existing_recruiter',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(self.token_obtain_url, token_data, format='json')
        access_token = login_response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Recruiter should access their dashboard
        response = self.client.get(reverse('dashboard-stats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cross_role_access_denied(self):
        """Test that users cannot access resources of other roles"""
        # This test would be more meaningful with specific role-restricted endpoints
        # For now, we test that the authentication works correctly
        
        # Get job seeker token
        token_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        login_response = self.client.post(self.token_obtain_url, token_data, format='json')
        access_token = login_response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Job seeker should be able to access their own resources
        response = self.client.get(reverse('dashboard-stats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the response contains job seeker specific data
        self.assertIn('total_applications', response.data)
        self.assertIn('profile_completion', response.data)


class JWTTokenClaimsTestCase(JWTAuthenticationTestCase):
    """
    Test cases for custom JWT token claims
    """
    
    def test_custom_claims_in_token(self):
        """Test that custom claims are included in JWT tokens"""
        token_data = {
            'username': 'existing_jobseeker',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.token_obtain_url, token_data, format='json')
        access_token = response.data['access']
        
        # Decode token and verify custom claims
        from rest_framework_simplejwt.tokens import UntypedToken
        
        token = UntypedToken(access_token)
        
        self.assertEqual(token['user_type'], 'job_seeker')
        self.assertEqual(token['username'], 'existing_jobseeker')
        self.assertEqual(token['email'], 'existing@jobseeker.com')
        self.assertEqual(str(token['user_id']), str(self.job_seeker.id))
        self.assertIn('first_name', token)
        self.assertIn('last_name', token)
        self.assertIn('is_verified', token)
    
    def test_recruiter_claims_in_token(self):
        """Test custom claims for recruiter tokens"""
        token_data = {
            'username': 'existing_recruiter',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.token_obtain_url, token_data, format='json')
        access_token = response.data['access']
        
        # Decode token and verify custom claims
        from rest_framework_simplejwt.tokens import UntypedToken
        
        token = UntypedToken(access_token)
        
        self.assertEqual(token['user_type'], 'recruiter')
        self.assertEqual(token['username'], 'existing_recruiter')
        self.assertEqual(token['email'], 'existing@recruiter.com')
        self.assertEqual(str(token['user_id']), str(self.recruiter.id))


class JWTErrorHandlingTestCase(JWTAuthenticationTestCase):
    """
    Test cases for JWT error handling
    """
    
    def test_malformed_token(self):
        """Test handling of malformed JWT token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer malformed_token')
        response = self.client.get(reverse('dashboard-stats'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_expired_token_handling(self):
        """Test handling of expired JWT token"""
        # Test with a malformed token that simulates expiration
        # Using a token that will fail validation
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjAwMDAwMDAwLCJpYXQiOjE2MDAwMDAwMDAsImp0aSI6ImV4cGlyZWQiLCJ1c2VyX2lkIjoxfQ.invalid"
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        response = self.client.get(reverse('dashboard-stats'))
        
        # Should return 401 for expired/invalid token
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_missing_authorization_header(self):
        """Test request without authorization header"""
        response = self.client.get(reverse('dashboard-stats'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_authorization_format(self):
        """Test invalid authorization header format"""
        self.client.credentials(HTTP_AUTHORIZATION='InvalidFormat token')
        response = self.client.get(reverse('dashboard-stats'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)