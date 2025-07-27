#!/usr/bin/env python
"""
Django management command for seeding the database
Usage: python manage.py seed_database --users 20 --jobs 50 --applications 100
"""

import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker

from matcher.models import (
    User, JobSeekerProfile, RecruiterProfile, JobPost, 
    Application, Resume, NotificationTemplate
)

fake = Faker()

class Command(BaseCommand):
    help = 'Seed the database with initial data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create (default: 20)'
        )
        parser.add_argument(
            '--jobs',
            type=int,
            default=50,
            help='Number of job posts to create (default: 50)'
        )
        parser.add_argument(
            '--applications',
            type=int,
            default=100,
            help='Number of applications to create (default: 100)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write('Starting database seeding...')
        
        try:
            with transaction.atomic():
                # Create admin user
                admin_user = self.create_admin_user()
                
                # Create notification templates
                self.create_notification_templates()
                
                # Create users
                users = self.create_users(options['users'])
                
                # Create job posts
                jobs = self.create_job_posts(users, options['jobs'])
                
                # Create applications
                applications_created = self.create_applications(users, jobs, options['applications'])

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully seeded database with:\n'
                    f'- 1 admin user (username: admin, password: admin123)\n'
                    f'- {len(users)} regular users (password: password123)\n'
                    f'- {len(jobs)} job posts\n'
                    f'- {applications_created} applications\n'
                    f'- Notification templates'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error seeding database: {str(e)}')
            )
            raise

    def clear_data(self):
        """Clear existing data"""
        Application.objects.all().delete()
        Resume.objects.all().delete()
        JobPost.objects.all().delete()
        JobSeekerProfile.objects.all().delete()
        RecruiterProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        NotificationTemplate.objects.all().delete()
        self.stdout.write('Existing data cleared.')

    def create_admin_user(self):
        """Create admin user"""
        User = get_user_model()
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@hirewise.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'user_type': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f'Created admin user: admin/admin123')
        else:
            self.stdout.write('Admin user already exists')
        return admin_user

    def create_notification_templates(self):
        """Create notification templates"""
        templates = [
            {
                'name': 'job_application_received',
                'subject': 'New Job Application Received',
                'message': 'You have received a new application for your job posting: {job_title}',
                'notification_type': 'job_application'
            },
            {
                'name': 'application_status_updated',
                'subject': 'Application Status Updated',
                'message': 'Your application for {job_title} has been updated to: {status}',
                'notification_type': 'application_status'
            },
            {
                'name': 'new_job_match',
                'subject': 'New Job Match Found',
                'message': 'We found a new job that matches your profile: {job_title}',
                'notification_type': 'job_match'
            },
            {
                'name': 'resume_parsed',
                'subject': 'Resume Successfully Parsed',
                'message': 'Your resume has been successfully parsed and analyzed.',
                'notification_type': 'resume_processing'
            }
        ]

        created_count = 0
        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                created_count += 1

        self.stdout.write(f'Created {created_count} notification templates')

    def create_users(self, count):
        """Create users with profiles"""
        users = []
        User = get_user_model()

        for i in range(count):
            # Randomly assign user type (70% job seekers, 30% recruiters)
            user_type = 'job_seeker' if random.random() < 0.7 else 'recruiter'
            
            user = User.objects.create_user(
                username=f'user{i}',
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                user_type=user_type,
                phone_number=fake.phone_number()[:15],
                is_verified=True
            )
            user.set_password('password123')
            user.save()

            # Create profile based on user type
            if user_type == 'job_seeker':
                self.create_job_seeker_profile(user)
            else:
                self.create_recruiter_profile(user)

            users.append(user)

        self.stdout.write(f'Created {count} users with profiles')
        return users

    def create_job_seeker_profile(self, user):
        """Create job seeker profile"""
        skills = [
            'Python', 'JavaScript', 'React', 'Django', 'Node.js',
            'SQL', 'MongoDB', 'AWS', 'Docker', 'Git', 'HTML', 'CSS',
            'Java', 'C++', 'Machine Learning', 'Data Analysis',
            'Vue.js', 'Angular', 'Flask', 'FastAPI', 'PostgreSQL',
            'Redis', 'Kubernetes', 'CI/CD', 'TypeScript', 'GraphQL'
        ]

        profile = JobSeekerProfile.objects.create(
            user=user,
            location=fake.city(),
            experience_level=random.choice(['entry', 'mid', 'senior', 'lead']),
            current_position=fake.job(),
            expected_salary=random.randint(50000, 150000),
            skills=', '.join(random.sample(skills, random.randint(3, 8))),
            bio=fake.text(max_nb_chars=500),
            linkedin_url=f'https://linkedin.com/in/{user.username}',
            github_url=f'https://github.com/{user.username}',
            availability=True
        )

        # Create a resume for the job seeker
        Resume.objects.create(
            job_seeker=user,
            original_filename=f'{user.username}_resume.pdf',
            parsed_text=self.generate_resume_text(profile),
            is_primary=True,
            file_size=random.randint(100000, 1000000)
        )

        return profile

    def generate_resume_text(self, profile):
        """Generate realistic resume text"""
        return f"""
        {profile.user.first_name} {profile.user.last_name}
        {profile.user.email} | {profile.user.phone_number}
        Location: {profile.location}
        
        PROFESSIONAL SUMMARY
        {profile.bio}
        
        EXPERIENCE
        {profile.current_position}
        - {fake.text(max_nb_chars=200)}
        - {fake.text(max_nb_chars=200)}
        
        SKILLS
        {profile.skills}
        
        EDUCATION
        {fake.text(max_nb_chars=300)}
        """

    def create_recruiter_profile(self, user):
        """Create recruiter profile"""
        companies = [
            'TechCorp', 'InnovateLabs', 'DataSystems', 'CloudTech',
            'StartupHub', 'Enterprise Solutions', 'Digital Dynamics',
            'Future Systems', 'Smart Technologies', 'Global Tech',
            'NextGen Software', 'Quantum Computing Inc', 'AI Innovations'
        ]

        industries = [
            'Technology', 'Healthcare', 'Finance', 'Education',
            'E-commerce', 'Manufacturing', 'Consulting', 'Media',
            'Telecommunications', 'Automotive', 'Aerospace'
        ]

        company_name = random.choice(companies)
        profile = RecruiterProfile.objects.create(
            user=user,
            company_name=company_name,
            company_website=f'https://{company_name.lower().replace(" ", "")}.com',
            company_size=random.choice(['1-10', '11-50', '51-200', '201-500', '500+']),
            industry=random.choice(industries),
            company_description=fake.text(max_nb_chars=1000),
            location=fake.city()
        )

        return profile

    def create_job_posts(self, users, count):
        """Create job posts"""
        jobs = []
        recruiters = [user for user in users if user.user_type == 'recruiter']
        
        if not recruiters:
            self.stdout.write(self.style.WARNING('No recruiters found, skipping job creation'))
            return jobs

        job_titles = [
            'Software Engineer', 'Frontend Developer', 'Backend Developer',
            'Full Stack Developer', 'Data Scientist', 'DevOps Engineer',
            'Product Manager', 'UI/UX Designer', 'QA Engineer',
            'Machine Learning Engineer', 'Mobile Developer', 'System Administrator',
            'Cloud Architect', 'Security Engineer', 'Database Administrator'
        ]

        skills_sets = [
            ['Python', 'Django', 'PostgreSQL', 'Redis'],
            ['JavaScript', 'React', 'Node.js', 'MongoDB'],
            ['Java', 'Spring Boot', 'MySQL', 'Docker'],
            ['Python', 'Machine Learning', 'TensorFlow', 'AWS'],
            ['React Native', 'iOS', 'Android', 'Firebase'],
            ['DevOps', 'Kubernetes', 'AWS', 'CI/CD'],
            ['Vue.js', 'TypeScript', 'GraphQL', 'PostgreSQL'],
            ['Angular', 'C#', '.NET', 'SQL Server']
        ]

        locations = ['Remote', 'New York', 'San Francisco', 'London', 'Berlin', 'Toronto', 'Sydney', 'Tokyo']

        for i in range(count):
            recruiter = random.choice(recruiters)
            skills = random.choice(skills_sets)
            title = random.choice(job_titles)

            salary_min = random.randint(50000, 120000)
            salary_max = salary_min + random.randint(20000, 80000)

            job = JobPost.objects.create(
                recruiter=recruiter,
                title=title,
                description=self.generate_job_description(title, skills),
                requirements=self.generate_job_requirements(skills),
                location=random.choice(locations),
                job_type=random.choice(['full_time', 'part_time', 'contract', 'internship']),
                experience_level=random.choice(['entry', 'mid', 'senior', 'lead']),
                salary_min=salary_min,
                salary_max=salary_max,
                skills_required=', '.join(skills),
                is_active=True,
                views_count=random.randint(0, 1000)
            )

            jobs.append(job)

        self.stdout.write(f'Created {count} job posts')
        return jobs

    def generate_job_description(self, title, skills):
        """Generate realistic job description"""
        return f"""
        We are looking for a talented {title} to join our growing team.
        
        In this role, you will:
        - {fake.text(max_nb_chars=100)}
        - {fake.text(max_nb_chars=100)}
        - Work with technologies including {', '.join(skills[:3])}
        - {fake.text(max_nb_chars=100)}
        
        What we offer:
        - Competitive salary and benefits
        - Flexible working arrangements
        - Professional development opportunities
        - Modern tech stack and tools
        """

    def generate_job_requirements(self, skills):
        """Generate job requirements"""
        return f"""
        Required Skills:
        - {', '.join(skills)}
        - Strong problem-solving abilities
        - Excellent communication skills
        - {fake.text(max_nb_chars=100)}
        
        Preferred:
        - {fake.text(max_nb_chars=100)}
        - Experience with agile methodologies
        - Bachelor's degree in Computer Science or related field
        """

    def create_applications(self, users, jobs, count):
        """Create job applications"""
        job_seekers = [user for user in users if user.user_type == 'job_seeker']
        
        if not job_seekers or not jobs:
            self.stdout.write(self.style.WARNING('No job seekers or jobs found, skipping applications'))
            return 0

        applications_created = 0
        attempts = 0
        max_attempts = count * 3  # Prevent infinite loop

        while applications_created < count and attempts < max_attempts:
            attempts += 1
            job_seeker = random.choice(job_seekers)
            job = random.choice(jobs)
            
            # Avoid duplicate applications
            if Application.objects.filter(job_seeker=job_seeker, job_post=job).exists():
                continue

            resume = Resume.objects.filter(job_seeker=job_seeker).first()
            if not resume:
                continue

            Application.objects.create(
                job_seeker=job_seeker,
                job_post=job,
                resume=resume,
                cover_letter=fake.text(max_nb_chars=1000),
                status=random.choice(['pending', 'reviewed', 'interview', 'rejected', 'accepted']),
                match_score=random.uniform(60.0, 95.0),
                recruiter_notes=fake.text(max_nb_chars=500) if random.choice([True, False]) else ''
            )
            applications_created += 1

        self.stdout.write(f'Created {applications_created} applications')
        return applications_created