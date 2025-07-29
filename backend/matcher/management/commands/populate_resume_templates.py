from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from matcher.models import ResumeTemplate
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample resume templates'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample resume templates...')
        
        # Get or create admin user for templates
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@hirewise.com',
                'user_type': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        templates_data = [
            {
                'name': 'Professional Classic',
                'description': 'A clean, professional template perfect for corporate environments and traditional industries.',
                'category': 'professional',
                'template_data': {
                    'styles': {
                        'font_family': 'Arial, sans-serif',
                        'font_size': '11pt',
                        'line_height': '1.2',
                        'margins': {'top': '1in', 'bottom': '1in', 'left': '1in', 'right': '1in'},
                        'colors': {
                            'primary': '#000000',
                            'secondary': '#333333',
                            'accent': '#0066cc'
                        }
                    },
                    'layout': {
                        'type': 'single_column',
                        'header_style': 'centered',
                        'section_spacing': '12pt',
                        'bullet_style': 'bullet'
                    }
                },
                'sections': [
                    {'name': 'personal_info', 'title': 'Contact Information', 'required': True, 'order': 1},
                    {'name': 'summary', 'title': 'Professional Summary', 'required': False, 'order': 2},
                    {'name': 'experience', 'title': 'Professional Experience', 'required': True, 'order': 3},
                    {'name': 'education', 'title': 'Education', 'required': True, 'order': 4},
                    {'name': 'skills', 'title': 'Core Competencies', 'required': False, 'order': 5},
                    {'name': 'certifications', 'title': 'Certifications', 'required': False, 'order': 6}
                ],
                'is_premium': False
            },
            {
                'name': 'Modern Creative',
                'description': 'A contemporary design with creative elements, ideal for design, marketing, and creative roles.',
                'category': 'creative',
                'template_data': {
                    'styles': {
                        'font_family': 'Helvetica, Arial, sans-serif',
                        'font_size': '10pt',
                        'line_height': '1.3',
                        'margins': {'top': '0.75in', 'bottom': '0.75in', 'left': '0.75in', 'right': '0.75in'},
                        'colors': {
                            'primary': '#2c3e50',
                            'secondary': '#34495e',
                            'accent': '#e74c3c'
                        }
                    },
                    'layout': {
                        'type': 'two_column',
                        'header_style': 'left_aligned',
                        'section_spacing': '10pt',
                        'bullet_style': 'arrow'
                    }
                },
                'sections': [
                    {'name': 'personal_info', 'title': 'Contact', 'required': True, 'order': 1},
                    {'name': 'summary', 'title': 'About Me', 'required': False, 'order': 2},
                    {'name': 'experience', 'title': 'Experience', 'required': True, 'order': 3},
                    {'name': 'skills', 'title': 'Skills & Expertise', 'required': False, 'order': 4},
                    {'name': 'education', 'title': 'Education', 'required': True, 'order': 5},
                    {'name': 'projects', 'title': 'Featured Projects', 'required': False, 'order': 6},
                    {'name': 'awards', 'title': 'Awards & Recognition', 'required': False, 'order': 7}
                ],
                'is_premium': True
            },
            {
                'name': 'Tech Professional',
                'description': 'Optimized for software developers, engineers, and technical professionals.',
                'category': 'technical',
                'template_data': {
                    'styles': {
                        'font_family': 'Consolas, Monaco, monospace',
                        'font_size': '10pt',
                        'line_height': '1.4',
                        'margins': {'top': '1in', 'bottom': '1in', 'left': '1in', 'right': '1in'},
                        'colors': {
                            'primary': '#1a1a1a',
                            'secondary': '#666666',
                            'accent': '#007acc'
                        }
                    },
                    'layout': {
                        'type': 'single_column',
                        'header_style': 'left_aligned',
                        'section_spacing': '14pt',
                        'bullet_style': 'dash'
                    }
                },
                'sections': [
                    {'name': 'personal_info', 'title': 'Contact Information', 'required': True, 'order': 1},
                    {'name': 'summary', 'title': 'Technical Summary', 'required': False, 'order': 2},
                    {'name': 'skills', 'title': 'Technical Skills', 'required': True, 'order': 3},
                    {'name': 'experience', 'title': 'Professional Experience', 'required': True, 'order': 4},
                    {'name': 'projects', 'title': 'Key Projects', 'required': False, 'order': 5},
                    {'name': 'education', 'title': 'Education', 'required': True, 'order': 6},
                    {'name': 'certifications', 'title': 'Certifications', 'required': False, 'order': 7}
                ],
                'is_premium': False
            },
            {
                'name': 'Academic Scholar',
                'description': 'Designed for academic positions, research roles, and educational institutions.',
                'category': 'academic',
                'template_data': {
                    'styles': {
                        'font_family': 'Times New Roman, serif',
                        'font_size': '12pt',
                        'line_height': '1.5',
                        'margins': {'top': '1in', 'bottom': '1in', 'left': '1.25in', 'right': '1.25in'},
                        'colors': {
                            'primary': '#000000',
                            'secondary': '#333333',
                            'accent': '#8b0000'
                        }
                    },
                    'layout': {
                        'type': 'single_column',
                        'header_style': 'centered',
                        'section_spacing': '16pt',
                        'bullet_style': 'bullet'
                    }
                },
                'sections': [
                    {'name': 'personal_info', 'title': 'Contact Information', 'required': True, 'order': 1},
                    {'name': 'education', 'title': 'Education', 'required': True, 'order': 2},
                    {'name': 'experience', 'title': 'Academic Experience', 'required': True, 'order': 3},
                    {'name': 'publications', 'title': 'Publications', 'required': False, 'order': 4},
                    {'name': 'research', 'title': 'Research Experience', 'required': False, 'order': 5},
                    {'name': 'awards', 'title': 'Honors and Awards', 'required': False, 'order': 6},
                    {'name': 'conferences', 'title': 'Conference Presentations', 'required': False, 'order': 7}
                ],
                'is_premium': True
            },
            {
                'name': 'Modern Minimalist',
                'description': 'A sleek, modern design with clean lines and plenty of white space.',
                'category': 'modern',
                'template_data': {
                    'styles': {
                        'font_family': 'Lato, sans-serif',
                        'font_size': '11pt',
                        'line_height': '1.4',
                        'margins': {'top': '0.8in', 'bottom': '0.8in', 'left': '0.8in', 'right': '0.8in'},
                        'colors': {
                            'primary': '#2c3e50',
                            'secondary': '#7f8c8d',
                            'accent': '#3498db'
                        }
                    },
                    'layout': {
                        'type': 'hybrid',
                        'header_style': 'modern',
                        'section_spacing': '18pt',
                        'bullet_style': 'circle'
                    }
                },
                'sections': [
                    {'name': 'personal_info', 'title': 'Contact', 'required': True, 'order': 1},
                    {'name': 'summary', 'title': 'Profile', 'required': False, 'order': 2},
                    {'name': 'experience', 'title': 'Experience', 'required': True, 'order': 3},
                    {'name': 'skills', 'title': 'Skills', 'required': False, 'order': 4},
                    {'name': 'education', 'title': 'Education', 'required': True, 'order': 5},
                    {'name': 'languages', 'title': 'Languages', 'required': False, 'order': 6}
                ],
                'is_premium': False
            },
            {
                'name': 'Executive Classic',
                'description': 'A sophisticated template for senior executives and C-level positions.',
                'category': 'professional',
                'template_data': {
                    'styles': {
                        'font_family': 'Georgia, serif',
                        'font_size': '11pt',
                        'line_height': '1.3',
                        'margins': {'top': '1in', 'bottom': '1in', 'left': '1in', 'right': '1in'},
                        'colors': {
                            'primary': '#1a1a1a',
                            'secondary': '#4a4a4a',
                            'accent': '#b8860b'
                        }
                    },
                    'layout': {
                        'type': 'single_column',
                        'header_style': 'executive',
                        'section_spacing': '14pt',
                        'bullet_style': 'bullet'
                    }
                },
                'sections': [
                    {'name': 'personal_info', 'title': 'Executive Profile', 'required': True, 'order': 1},
                    {'name': 'summary', 'title': 'Executive Summary', 'required': True, 'order': 2},
                    {'name': 'experience', 'title': 'Leadership Experience', 'required': True, 'order': 3},
                    {'name': 'achievements', 'title': 'Key Achievements', 'required': False, 'order': 4},
                    {'name': 'education', 'title': 'Education', 'required': True, 'order': 5},
                    {'name': 'board_positions', 'title': 'Board Positions', 'required': False, 'order': 6}
                ],
                'is_premium': True
            }
        ]
        
        created_count = 0
        for template_data in templates_data:
            template, created = ResumeTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'description': template_data['description'],
                    'category': template_data['category'],
                    'template_data': template_data['template_data'],
                    'sections': template_data['sections'],
                    'is_premium': template_data['is_premium'],
                    'created_by': admin_user,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Template already exists: {template.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new resume templates')
        )