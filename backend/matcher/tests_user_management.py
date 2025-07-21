import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
from datetime import timedelta

from .models import (
    JobSeekerProfile, RecruiterProfile, EmailVerificationToken, 
    PasswordResetToken
)

User = get_user_model()


class UserRegistrationTestCase(APITestCase):
    """
    Test cases for user registration with role-based profile creation
    """
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('jwt-register')
        
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
    
    def test_job_seeker_registration_creates_profile(self):
        """Test that job seeker registration creates corresponding profile"""
        response = self.client.post(self.register_url, self.job_seeker_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertTrue(response.data.get('verification_email_sent', False))
        
        # Verify user was created
        user = User.objects.get(username='jobseeker1')
        self.assertEqual(user.user_type, 'job_seeker')
        self.assertFalse(user.is_verified)  # Should not be verified initially
        
        # Verify job seeker profile was created
        self.assertTrue(hasattr(user, 'job_seeker_profile'))
        self.assertIsInstance(user.job_seeker_profile, JobSeekerProfile)
    
    def test_recruiter_registration_creates_profile(self):
        """Test that recruiter registration creates corresponding profile"""
        response = self.client.post(self.register_url, self.recruiter_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertTrue(response.data.get('verification_email_sent', False))
        
        # Verify user was created
        user = User.objects.get(username='recruiter1')
        self.assertEqual(user.user_type, 'recruiter')
        self.assertFalse(user.is_verified)  # Should not be verified initially
        
        # Verify recruiter profile was created
        self.assertTrue(hasattr(user, 'recruiter_profile'))
        self.assertIsInstance(user.recruiter_profile, RecruiterProfile)
        self.assertEqual(user.recruiter_profile.company_name, 'Tech Corp')
    
    @patch('matcher.views.send_verification_email')
    def test_registration_sends_verification_email(self, mock_send_email):
        """Test that registration sends verification email"""
        mock_send_email.return_value = True
        
        response = self.client.post(self.register_url, self.job_seeker_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify verification token was created
        user = User.objects.get(username='jobseeker1')
        verification_token = EmailVerificationToken.objects.filter(user=user).first()
        self.assertIsNotNone(verification_token)
        self.assertFalse(verification_token.is_used)
        
        # Verify email sending was attempted
        mock_send_email.assert_called_once()
    
    def test_registration_with_invalid_user_type(self):
        """Test registration with invalid user type"""
        data = self.job_seeker_data.copy()
        data['user_type'] = 'invalid_type'
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # The validation error can be in either 'user_type' or 'non_field_errors'
        self.assertTrue('user_type' in response.data or 'non_field_errors' in response.data)
    
    def test_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        data = self.job_seeker_data.copy()
        data['password_confirm'] = 'differentpass'
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)


class EmailVerificationTestCase(APITestCase):
    """
    Test cases for email verification functionality
    """
    
    def setUp(self):
        self.client = APIClient()
        self.request_verification_url = reverse('request-email-verification')
        self.verify_email_url = reverse('verify-email')
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker',
            is_verified=False
        )
        JobSeekerProfile.objects.create(user=self.user)
    
    def test_request_email_verification_success(self):
        """Test successful email verification request"""
        data = {'email': 'test@example.com'}
        
        with patch('matcher.utils.send_verification_email', return_value=True):
            response = self.client.post(self.request_verification_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['email'], 'test@example.com')
        
        # Verify token was created
        token = EmailVerificationToken.objects.filter(user=self.user).first()
        self.assertIsNotNone(token)
        self.assertFalse(token.is_used)
    
    def test_request_verification_for_already_verified_user(self):
        """Test requesting verification for already verified user"""
        self.user.is_verified = True
        self.user.save()
        
        data = {'email': 'test@example.com'}
        response = self.client.post(self.request_verification_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_request_verification_for_nonexistent_user(self):
        """Test requesting verification for non-existent user"""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.request_verification_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_verify_email_success(self):
        """Test successful email verification"""
        # Create verification token
        token = EmailVerificationToken.objects.create(user=self.user, token='valid_token')
        
        data = {'token': 'valid_token'}
        
        with patch('matcher.utils.send_welcome_email', return_value=True):
            response = self.client.post(self.verify_email_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        
        # Verify user is now verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)
        
        # Verify token is marked as used
        token.refresh_from_db()
        self.assertTrue(token.is_used)
    
    def test_verify_email_with_invalid_token(self):
        """Test email verification with invalid token"""
        data = {'token': 'invalid_token'}
        response = self.client.post(self.verify_email_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.data)
    
    def test_verify_email_with_expired_token(self):
        """Test email verification with expired token"""
        # Create expired token
        token = EmailVerificationToken.objects.create(
            user=self.user, 
            token='expired_token',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        data = {'token': 'expired_token'}
        response = self.client.post(self.verify_email_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.data)
    
    def test_verify_email_with_used_token(self):
        """Test email verification with already used token"""
        # Create used token
        token = EmailVerificationToken.objects.create(
            user=self.user, 
            token='used_token',
            is_used=True
        )
        
        data = {'token': 'used_token'}
        response = self.client.post(self.verify_email_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.data)


class PasswordResetTestCase(APITestCase):
    """
    Test cases for password reset functionality
    """
    
    def setUp(self):
        self.client = APIClient()
        self.request_reset_url = reverse('request-password-reset')
        self.reset_password_url = reverse('reset-password')
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123',
            user_type='job_seeker'
        )
        JobSeekerProfile.objects.create(user=self.user)
    
    def test_request_password_reset_success(self):
        """Test successful password reset request"""
        data = {'email': 'test@example.com'}
        
        with patch('matcher.utils.send_password_reset_email', return_value=True):
            response = self.client.post(self.request_reset_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['email'], 'test@example.com')
        
        # Verify reset token was created
        token = PasswordResetToken.objects.filter(user=self.user).first()
        self.assertIsNotNone(token)
        self.assertFalse(token.is_used)
    
    def test_request_reset_for_nonexistent_user(self):
        """Test requesting reset for non-existent user"""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.request_reset_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_request_reset_for_inactive_user(self):
        """Test requesting reset for inactive user"""
        self.user.is_active = False
        self.user.save()
        
        data = {'email': 'test@example.com'}
        response = self.client.post(self.request_reset_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_reset_password_success(self):
        """Test successful password reset"""
        # Create reset token
        token = PasswordResetToken.objects.create(user=self.user, token='valid_reset_token')
        
        data = {
            'token': 'valid_reset_token',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.reset_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
        self.assertFalse(self.user.check_password('oldpassword123'))
        
        # Verify token is marked as used
        token.refresh_from_db()
        self.assertTrue(token.is_used)
    
    def test_reset_password_with_invalid_token(self):
        """Test password reset with invalid token"""
        data = {
            'token': 'invalid_token',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.reset_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.data)
    
    def test_reset_password_with_expired_token(self):
        """Test password reset with expired token"""
        # Create expired token
        token = PasswordResetToken.objects.create(
            user=self.user,
            token='expired_reset_token',
            expires_at=timezone.now() - timedelta(minutes=30)
        )
        
        data = {
            'token': 'expired_reset_token',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.reset_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.data)
    
    def test_reset_password_mismatch(self):
        """Test password reset with password mismatch"""
        token = PasswordResetToken.objects.create(user=self.user, token='valid_reset_token')
        
        data = {
            'token': 'valid_reset_token',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }
        
        response = self.client.post(self.reset_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)
    
    def test_reset_password_weak_password(self):
        """Test password reset with weak password"""
        token = PasswordResetToken.objects.create(user=self.user, token='valid_reset_token')
        
        data = {
            'token': 'valid_reset_token',
            'new_password': '123',  # Too short
            'confirm_password': '123'
        }
        
        response = self.client.post(self.reset_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Should have validation errors for weak password


class UserProfileManagementTestCase(APITestCase):
    """
    Test cases for user profile management APIs
    """
    
    def setUp(self):
        self.client = APIClient()
        self.change_password_url = reverse('change-password')
        self.profile_url = reverse('user-profile')
        self.delete_account_url = reverse('delete-account')
        
        # Create test users
        self.job_seeker = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@example.com',
            password='testpass123',
            user_type='job_seeker',
            first_name='John',
            last_name='Doe'
        )
        JobSeekerProfile.objects.create(user=self.job_seeker)
        
        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@example.com',
            password='testpass123',
            user_type='recruiter',
            first_name='Jane',
            last_name='Smith'
        )
        RecruiterProfile.objects.create(user=self.recruiter, company_name='Test Company')
    
    def test_change_password_success(self):
        """Test successful password change"""
        self.client.force_authenticate(user=self.job_seeker)
        
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.change_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify password was changed
        self.job_seeker.refresh_from_db()
        self.assertTrue(self.job_seeker.check_password('newpassword123'))
        self.assertFalse(self.job_seeker.check_password('testpass123'))
    
    def test_change_password_wrong_current_password(self):
        """Test password change with wrong current password"""
        self.client.force_authenticate(user=self.job_seeker)
        
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.change_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data)
    
    def test_change_password_mismatch(self):
        """Test password change with password mismatch"""
        self.client.force_authenticate(user=self.job_seeker)
        
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }
        
        response = self.client.post(self.change_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)
    
    def test_change_password_unauthenticated(self):
        """Test password change without authentication"""
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.change_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_user_profile(self):
        """Test getting user profile information"""
        self.client.force_authenticate(user=self.job_seeker)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'jobseeker')
        self.assertEqual(response.data['email'], 'jobseeker@example.com')
        self.assertEqual(response.data['user_type'], 'job_seeker')
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')
    
    def test_update_user_profile_patch(self):
        """Test updating user profile with PATCH"""
        self.client.force_authenticate(user=self.job_seeker)
        
        data = {
            'first_name': 'Johnny',
            'phone_number': '+1234567890'
        }
        
        response = self.client.patch(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        
        # Verify profile was updated
        self.job_seeker.refresh_from_db()
        self.assertEqual(self.job_seeker.first_name, 'Johnny')
        self.assertEqual(self.job_seeker.phone_number, '+1234567890')
        self.assertEqual(self.job_seeker.last_name, 'Doe')  # Should remain unchanged
    
    def test_update_user_profile_put(self):
        """Test updating user profile with PUT"""
        self.client.force_authenticate(user=self.job_seeker)
        
        data = {
            'first_name': 'Johnny',
            'last_name': 'Smith',
            'phone_number': '+1234567890'
        }
        
        response = self.client.put(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        
        # Verify profile was updated
        self.job_seeker.refresh_from_db()
        self.assertEqual(self.job_seeker.first_name, 'Johnny')
        self.assertEqual(self.job_seeker.last_name, 'Smith')
        self.assertEqual(self.job_seeker.phone_number, '+1234567890')
    
    def test_update_profile_invalid_phone(self):
        """Test updating profile with invalid phone number"""
        self.client.force_authenticate(user=self.job_seeker)
        
        data = {
            'phone_number': '123'  # Too short
        }
        
        response = self.client.patch(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)
    
    def test_delete_account(self):
        """Test account deletion (soft delete)"""
        self.client.force_authenticate(user=self.job_seeker)
        
        response = self.client.delete(self.delete_account_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify account was deactivated (soft delete)
        self.job_seeker.refresh_from_db()
        self.assertFalse(self.job_seeker.is_active)
    
    def test_delete_account_unauthenticated(self):
        """Test account deletion without authentication"""
        response = self.client.delete(self.delete_account_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileViewSetTestCase(APITestCase):
    """
    Test cases for job seeker and recruiter profile viewsets
    """
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.job_seeker = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        self.job_seeker_profile = JobSeekerProfile.objects.create(
            user=self.job_seeker,
            location='New York',
            experience_level='mid',
            current_position='Software Developer'
        )
        
        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@example.com',
            password='testpass123',
            user_type='recruiter'
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Tech Corp',
            industry='Technology',
            location='San Francisco'
        )
        
        # Create another user to test access control
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        JobSeekerProfile.objects.create(user=self.other_user)
    
    def test_job_seeker_can_access_own_profile(self):
        """Test that job seeker can access their own profile"""
        self.client.force_authenticate(user=self.job_seeker)
        
        url = reverse('job-seeker-profile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['user']['username'], 'jobseeker')
    
    def test_job_seeker_cannot_access_other_profiles(self):
        """Test that job seeker cannot access other profiles"""
        self.client.force_authenticate(user=self.other_user)
        
        url = reverse('job-seeker-profile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        # Should only see their own profile, not the job_seeker's profile
        self.assertEqual(response.data['results'][0]['user']['username'], 'otheruser')
    
    def test_recruiter_can_access_own_profile(self):
        """Test that recruiter can access their own profile"""
        self.client.force_authenticate(user=self.recruiter)
        
        url = reverse('recruiter-profile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['user']['username'], 'recruiter')
    
    def test_job_seeker_cannot_access_recruiter_profiles(self):
        """Test that job seeker cannot access recruiter profiles"""
        self.client.force_authenticate(user=self.job_seeker)
        
        url = reverse('recruiter-profile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)  # Should be empty
    
    def test_update_job_seeker_profile(self):
        """Test updating job seeker profile"""
        self.client.force_authenticate(user=self.job_seeker)
        
        url = reverse('job-seeker-profile-detail', kwargs={'pk': self.job_seeker_profile.pk})
        data = {
            'location': 'Los Angeles',
            'experience_level': 'senior',
            'bio': 'Experienced software developer'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify profile was updated
        self.job_seeker_profile.refresh_from_db()
        self.assertEqual(self.job_seeker_profile.location, 'Los Angeles')
        self.assertEqual(self.job_seeker_profile.experience_level, 'senior')
        self.assertEqual(self.job_seeker_profile.bio, 'Experienced software developer')
    
    def test_update_recruiter_profile(self):
        """Test updating recruiter profile"""
        self.client.force_authenticate(user=self.recruiter)
        
        url = reverse('recruiter-profile-detail', kwargs={'pk': self.recruiter_profile.pk})
        data = {
            'company_name': 'Updated Tech Corp',
            'industry': 'Software',
            'company_description': 'Leading software company'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify profile was updated
        self.recruiter_profile.refresh_from_db()
        self.assertEqual(self.recruiter_profile.company_name, 'Updated Tech Corp')
        self.assertEqual(self.recruiter_profile.industry, 'Software')
        self.assertEqual(self.recruiter_profile.company_description, 'Leading software company')


class EmailUtilityTestCase(TestCase):
    """
    Test cases for email utility functions
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker',
            first_name='Test',
            last_name='User'
        )
    
    @patch('matcher.utils.send_mail')
    def test_send_verification_email(self, mock_send_mail):
        """Test sending verification email"""
        from .utils import send_verification_email
        
        mock_send_mail.return_value = True
        
        result = send_verification_email(self.user, 'test_token')
        
        self.assertTrue(result)
        mock_send_mail.assert_called_once()
        
        # Check email content
        call_args = mock_send_mail.call_args
        self.assertIn('Verify Your HireWise Account', call_args[1]['subject'])
        self.assertIn('test_token', call_args[1]['html_message'])
        self.assertEqual(call_args[1]['recipient_list'], ['test@example.com'])
    
    @patch('matcher.utils.send_mail')
    def test_send_password_reset_email(self, mock_send_mail):
        """Test sending password reset email"""
        from .utils import send_password_reset_email
        
        mock_send_mail.return_value = True
        
        result = send_password_reset_email(self.user, 'reset_token')
        
        self.assertTrue(result)
        mock_send_mail.assert_called_once()
        
        # Check email content
        call_args = mock_send_mail.call_args
        self.assertIn('Reset Your HireWise Password', call_args[1]['subject'])
        self.assertIn('reset_token', call_args[1]['html_message'])
        self.assertEqual(call_args[1]['recipient_list'], ['test@example.com'])
    
    @patch('matcher.utils.send_mail')
    def test_send_welcome_email(self, mock_send_mail):
        """Test sending welcome email"""
        from .utils import send_welcome_email
        
        mock_send_mail.return_value = True
        
        result = send_welcome_email(self.user)
        
        self.assertTrue(result)
        mock_send_mail.assert_called_once()
        
        # Check email content
        call_args = mock_send_mail.call_args
        self.assertIn('Welcome to HireWise', call_args[1]['subject'])
        self.assertIn('job seeker', call_args[1]['html_message'])
        self.assertEqual(call_args[1]['recipient_list'], ['test@example.com'])


class TokenModelTestCase(TestCase):
    """
    Test cases for EmailVerificationToken and PasswordResetToken models
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
    
    def test_email_verification_token_creation(self):
        """Test EmailVerificationToken creation and expiration"""
        token = EmailVerificationToken.objects.create(
            user=self.user,
            token='test_token'
        )
        
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token, 'test_token')
        self.assertFalse(token.is_used)
        self.assertIsNotNone(token.expires_at)
        self.assertFalse(token.is_expired())
    
    def test_email_verification_token_expiration(self):
        """Test EmailVerificationToken expiration check"""
        token = EmailVerificationToken.objects.create(
            user=self.user,
            token='expired_token',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        self.assertTrue(token.is_expired())
    
    def test_password_reset_token_creation(self):
        """Test PasswordResetToken creation and expiration"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token='reset_token'
        )
        
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token, 'reset_token')
        self.assertFalse(token.is_used)
        self.assertIsNotNone(token.expires_at)
        self.assertFalse(token.is_expired())
    
    def test_password_reset_token_expiration(self):
        """Test PasswordResetToken expiration check"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token='expired_reset_token',
            expires_at=timezone.now() - timedelta(minutes=30)
        )
        
        self.assertTrue(token.is_expired())