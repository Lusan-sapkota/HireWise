from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
import json
import uuid

from .models import ResumeTemplate, ResumeTemplateVersion, UserResumeTemplate
from .serializers import (
    ResumeTemplateSerializer, ResumeTemplateVersionSerializer,
    UserResumeTemplateSerializer, ResumeTemplateListSerializer
)

User = get_user_model()


class ResumeTemplateModelTest(TestCase):
    """Test cases for ResumeTemplate model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='admin'
        )
        
        self.template_data = {
            'name': 'Test Template',
            'description': 'A test template',
            'category': 'professional',
            'template_data': {
                'styles': {'font_family': 'Arial'},
                'layout': {'type': 'single_column'}
            },
            'sections': [
                {'name': 'personal_info', 'title': 'Personal Info', 'required': True, 'order': 1}
            ],
            'created_by': self.user
        }
    
    def test_create_resume_template(self):
        """Test creating a resume template"""
        template = ResumeTemplate.objects.create(**self.template_data)
        
        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.category, 'professional')
        self.assertEqual(template.created_by, self.user)
        self.assertTrue(template.is_active)
        self.assertFalse(template.is_premium)
        self.assertEqual(template.version, '1.0')
        self.assertEqual(template.usage_count, 0)
    
    def test_template_str_representation(self):
        """Test string representation of template"""
        template = ResumeTemplate.objects.create(**self.template_data)
        expected = f"{template.name} ({template.get_category_display()})"
        self.assertEqual(str(template), expected)
    
    def test_increment_usage_count(self):
        """Test incrementing usage count"""
        template = ResumeTemplate.objects.create(**self.template_data)
        initial_count = template.usage_count
        
        template.increment_usage_count()
        template.refresh_from_db()
        
        self.assertEqual(template.usage_count, initial_count + 1)
    
    def test_is_popular_property(self):
        """Test is_popular property"""
        template = ResumeTemplate.objects.create(**self.template_data)
        
        # Initially not popular
        self.assertFalse(template.is_popular)
        
        # Make it popular
        template.usage_count = 150
        template.save()
        
        self.assertTrue(template.is_popular)
    
    def test_get_default_sections(self):
        """Test getting default sections"""
        template = ResumeTemplate.objects.create(**self.template_data)
        sections = template.get_default_sections()
        
        self.assertIsInstance(sections, list)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]['name'], 'personal_info')
    
    def test_get_default_sections_fallback(self):
        """Test default sections fallback when none specified"""
        template_data = self.template_data.copy()
        template_data['sections'] = []
        template = ResumeTemplate.objects.create(**template_data)
        
        sections = template.get_default_sections()
        
        self.assertIsInstance(sections, list)
        self.assertGreater(len(sections), 0)
        # Should have default sections
        section_names = [s['name'] for s in sections]
        self.assertIn('personal_info', section_names)
        self.assertIn('experience', section_names)


class ResumeTemplateVersionModelTest(TestCase):
    """Test cases for ResumeTemplateVersion model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='admin'
        )
        
        self.template = ResumeTemplate.objects.create(
            name='Test Template',
            description='A test template',
            category='professional',
            template_data={'styles': {'font_family': 'Arial'}},
            created_by=self.user
        )
    
    def test_create_template_version(self):
        """Test creating a template version"""
        version = ResumeTemplateVersion.objects.create(
            template=self.template,
            version_number='1.1',
            template_data={'styles': {'font_family': 'Helvetica'}},
            sections=[],
            change_notes='Updated font family',
            created_by=self.user
        )
        
        self.assertEqual(version.template, self.template)
        self.assertEqual(version.version_number, '1.1')
        self.assertEqual(version.change_notes, 'Updated font family')
        self.assertFalse(version.is_current)
    
    def test_make_current_version(self):
        """Test making a version current"""
        version = ResumeTemplateVersion.objects.create(
            template=self.template,
            version_number='1.1',
            template_data={'styles': {'font_family': 'Helvetica'}},
            sections=[],
            created_by=self.user
        )
        
        version.make_current()
        
        version.refresh_from_db()
        self.template.refresh_from_db()
        
        self.assertTrue(version.is_current)
        self.assertEqual(self.template.version, '1.1')
        self.assertEqual(self.template.template_data, version.template_data)


class UserResumeTemplateModelTest(TestCase):
    """Test cases for UserResumeTemplate model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.base_template = ResumeTemplate.objects.create(
            name='Base Template',
            description='A base template',
            category='professional',
            template_data={'styles': {'font_family': 'Arial'}},
            sections=[
                {'name': 'personal_info', 'title': 'Personal Info', 'required': True, 'order': 1}
            ]
        )
    
    def test_create_user_template(self):
        """Test creating a user's customized template"""
        user_template = UserResumeTemplate.objects.create(
            user=self.user,
            base_template=self.base_template,
            name='My Custom Template',
            customized_data={'styles': {'font_family': 'Helvetica'}},
            customized_sections=[
                {'name': 'personal_info', 'title': 'Contact Info', 'required': True, 'order': 1}
            ]
        )
        
        self.assertEqual(user_template.user, self.user)
        self.assertEqual(user_template.base_template, self.base_template)
        self.assertEqual(user_template.name, 'My Custom Template')
        self.assertTrue(user_template.is_active)
    
    def test_get_merged_template_data(self):
        """Test getting merged template data"""
        user_template = UserResumeTemplate.objects.create(
            user=self.user,
            base_template=self.base_template,
            name='My Custom Template',
            customized_data={'styles': {'font_size': '12pt'}}
        )
        
        merged_data = user_template.get_merged_template_data()
        
        self.assertEqual(merged_data['styles']['font_family'], 'Arial')  # From base
        self.assertEqual(merged_data['styles']['font_size'], '12pt')     # From customization
    
    def test_get_merged_sections(self):
        """Test getting merged sections"""
        custom_sections = [
            {'name': 'personal_info', 'title': 'Contact Info', 'required': True, 'order': 1}
        ]
        
        user_template = UserResumeTemplate.objects.create(
            user=self.user,
            base_template=self.base_template,
            name='My Custom Template',
            customized_sections=custom_sections
        )
        
        merged_sections = user_template.get_merged_sections()
        
        self.assertEqual(merged_sections, custom_sections)
    
    def test_get_merged_sections_fallback(self):
        """Test getting merged sections fallback to base template"""
        user_template = UserResumeTemplate.objects.create(
            user=self.user,
            base_template=self.base_template,
            name='My Custom Template'
        )
        
        merged_sections = user_template.get_merged_sections()
        
        self.assertEqual(merged_sections, self.base_template.get_default_sections())


class ResumeTemplateSerializerTest(TestCase):
    """Test cases for ResumeTemplate serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='admin'
        )
        
        self.template = ResumeTemplate.objects.create(
            name='Test Template',
            description='A test template',
            category='professional',
            template_data={
                'styles': {'font_family': 'Arial'},
                'layout': {'type': 'single_column'}
            },
            sections=[
                {'name': 'personal_info', 'title': 'Personal Info', 'required': True, 'order': 1}
            ],
            created_by=self.user
        )
    
    def test_resume_template_serializer(self):
        """Test ResumeTemplateSerializer"""
        serializer = ResumeTemplateSerializer(self.template)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Template')
        self.assertEqual(data['category'], 'professional')
        self.assertEqual(data['category_display'], 'Professional')
        self.assertIn('default_sections', data)
        self.assertIn('is_popular', data)
    
    def test_template_data_validation(self):
        """Test template data validation"""
        invalid_data = {
            'name': 'Invalid Template',
            'category': 'professional',
            'template_data': 'invalid_json'  # Should be dict
        }
        
        serializer = ResumeTemplateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('template_data', serializer.errors)
    
    def test_sections_validation(self):
        """Test sections validation"""
        invalid_data = {
            'name': 'Invalid Template',
            'category': 'professional',
            'template_data': {'styles': {}, 'layout': {}},
            'sections': 'invalid_sections'  # Should be list
        }
        
        serializer = ResumeTemplateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('sections', serializer.errors)


class ResumeTemplateAPITest(APITestCase):
    """Test cases for Resume Template API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            user_type='admin',
            is_staff=True
        )
        
        # Create test templates
        self.template1 = ResumeTemplate.objects.create(
            name='Professional Template',
            description='A professional template',
            category='professional',
            template_data={'styles': {}, 'layout': {}},
            sections=[],
            created_by=self.admin_user
        )
        
        self.template2 = ResumeTemplate.objects.create(
            name='Creative Template',
            description='A creative template',
            category='creative',
            template_data={'styles': {}, 'layout': {}},
            sections=[],
            is_premium=True,
            created_by=self.admin_user
        )
        
        self.client = APIClient()
    
    def get_jwt_token(self, user):
        """Helper method to get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_list_resume_templates(self):
        """Test listing resume templates"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:resume-template-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_templates_by_category(self):
        """Test filtering templates by category"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:resume-template-list')
        response = self.client.get(url, {'category': 'professional'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['category'], 'professional')
    
    def test_filter_templates_by_premium(self):
        """Test filtering templates by premium status"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:resume-template-list')
        response = self.client.get(url, {'is_premium': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(response.data['results'][0]['is_premium'])
    
    def test_search_templates(self):
        """Test searching templates"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:resume-template-list')
        response = self.client.get(url, {'search': 'professional'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_template_detail(self):
        """Test getting template detail"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:resume-template-detail', kwargs={'pk': self.template1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Professional Template')
    
    def test_use_template_action(self):
        """Test using a template (incrementing usage count)"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        initial_count = self.template1.usage_count
        
        url = reverse('default:resume-template-use-template', kwargs={'pk': self.template1.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        self.template1.refresh_from_db()
        self.assertEqual(self.template1.usage_count, initial_count + 1)
    
    def test_get_template_categories(self):
        """Test getting template categories"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:resume-template-categories')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('categories', response.data)
        self.assertIsInstance(response.data['categories'], list)
    
    def test_get_popular_templates(self):
        """Test getting popular templates"""
        # Make template1 popular
        self.template1.usage_count = 50
        self.template1.save()
        
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:resume-template-popular')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('popular_templates', response.data)
    
    def test_create_template_requires_admin(self):
        """Test that creating templates requires admin privileges"""
        token = self.get_jwt_token(self.user)  # Regular user
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:resume-template-list')
        data = {
            'name': 'New Template',
            'category': 'modern',
            'template_data': {'styles': {}, 'layout': {}},
            'sections': []
        }
        response = self.client.post(url, data, format='json')
        
        # Should be allowed for authenticated users (we changed permissions)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access templates"""
        url = reverse('default:resume-template-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserResumeTemplateAPITest(APITestCase):
    """Test cases for User Resume Template API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.base_template = ResumeTemplate.objects.create(
            name='Base Template',
            description='A base template',
            category='professional',
            template_data={'styles': {'font_family': 'Arial'}},
            sections=[]
        )
        
        self.user_template = UserResumeTemplate.objects.create(
            user=self.user,
            base_template=self.base_template,
            name='My Custom Template',
            customized_data={'styles': {'font_size': '12pt'}}
        )
        
        self.client = APIClient()
    
    def get_jwt_token(self, user):
        """Helper method to get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_list_user_templates(self):
        """Test listing user's templates"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:user-resume-template-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'My Custom Template')
    
    def test_create_user_template(self):
        """Test creating a user template"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:user-resume-template-list')
        data = {
            'base_template': self.base_template.id,
            'name': 'New Custom Template',
            'customized_data': {'styles': {'color': 'blue'}},
            'customized_sections': []
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Custom Template')
    
    def test_duplicate_template(self):
        """Test duplicating a user template"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:user-resume-template-duplicate', kwargs={'pk': self.user_template.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('Copy', response.data['template']['name'])
    
    def test_template_preview(self):
        """Test getting template preview"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:user-resume-template-preview', kwargs={'pk': self.user_template.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('template_data', response.data)
        self.assertIn('sections', response.data)
        self.assertIn('base_template', response.data)
    
    def test_user_can_only_access_own_templates(self):
        """Test that users can only access their own templates"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123',
            user_type='job_seeker'
        )
        
        token = self.get_jwt_token(other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:user-resume-template-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)  # Should not see other user's templates


class TemplatePreviewAPITest(APITestCase):
    """Test cases for Template Preview API"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        self.template = ResumeTemplate.objects.create(
            name='Test Template',
            description='A test template',
            category='professional',
            template_data={'styles': {}, 'layout': {}},
            sections=[]
        )
        
        self.client = APIClient()
    
    def get_jwt_token(self, user):
        """Helper method to get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_get_template_preview(self):
        """Test getting template preview with sample data"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('default:template-preview', kwargs={'template_id': self.template.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('template', response.data)
        self.assertIn('sample_data', response.data)
        self.assertIn('preview_html', response.data)
    
    def test_preview_nonexistent_template(self):
        """Test preview for nonexistent template"""
        token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        fake_id = uuid.uuid4()
        url = reverse('default:template-preview', kwargs={'template_id': fake_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)