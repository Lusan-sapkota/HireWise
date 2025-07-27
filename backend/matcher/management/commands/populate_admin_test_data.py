from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from faker import Faker

from matcher.models import (
    User, JobSeekerProfile, RecruiterProfile, Resume, JobPost, 
    Application, AIAnalysisResult, InterviewSession, AIInterviewQuestion,
    Skill, UserSkill, EmailVerificationToken, PasswordResetToken,
    JobAnalytics, JobView, Notification, NotificationPreference,
    NotificationTemplate
)


class Command(BaseCommand):
    help = 'Populate database with test data for admin interface testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of users to create'
        )
        parser.add_argument(
            '--jobs',
            type=int,
            default=20,
            help='Number of job posts to create'
        )
        parser.add_argument(
            '--applications',
            type=int,
            default=100,
            help='Number of applications to create'
        )

    def __init__(self):
        super().__init__()
        self.fake = Faker()
        
    def handle(self, *args, **options):
        self.stdout.write('Starting admin test data population...')
        
        # Create skills first
        self.create_skills()
        
        # Create users and profiles
        self.create_users(options['users'])
        
        # Create job posts
        self.create_job_posts(options['jobs'])
        
        # Create applications
        self.create_applications(options['applications'])
        
        # Create additional test data
        self.create_analytics_data()
        self.create_notification_data()
        self.create_interview_data()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated admin test data!')
        )

    def create_skills(self):
        """Create sample skills"""
        skills_data = [
            ('Python', 'language'),
            ('JavaScript', 'language'),
            ('Java', 'language'),
            ('React', 'framework'),
            ('Django', 'framework'),
            ('Node.js', 'framework'),
            ('PostgreSQL', 'technical'),
            ('MongoDB', 'technical'),
            ('AWS', 'tool'),
            ('Docker', 'tool'),
            ('Communication', 'soft'),
            ('Leadership', 'soft'),
            ('Problem Solving', 'soft'),
            ('Project Management', 'soft'),
            ('Machine Learning', 'technical'),
            ('Data Analysis', 'technical'),
            ('UI/UX Design', 'technical'),
            ('DevOps', 'technical'),
            ('Agile', 'certification'),
            ('Scrum Master', 'certification'),
        ]
        
        for name, category in skills_data:
            skill, created = Skill.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'description': f'{name} skill',
                    'is_verified': random.choice([True, False])
                }
            )
            if created:
                self.stdout.write(f'Created skill: {name}')

    def create_users(self, count):
        """Create sample users with profiles"""
        job_seeker_count = int(count * 0.7)  # 70% job seekers
        recruiter_count = count - job_seeker_count  # 30% recruiters
        
        # Create job seekers
        for i in range(job_seeker_count):
            user = User.objects.create_user(
                username=f'jobseeker_{i}',
                email=f'jobseeker_{i}@example.com',
                password='testpass123',
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name(),
                user_type='job_seeker',
                phone_number=self.fake.phone_number()[:15],
                is_verified=random.choice([True, False]),
                date_joined=self.fake.date_time_between(start_date='-1y', end_date='now', tzinfo=timezone.get_current_timezone()),
                last_login=self.fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone()) if random.choice([True, False]) else None
            )
            
            # Create job seeker profile
            profile = JobSeekerProfile.objects.create(
                user=user,
                date_of_birth=self.fake.date_of_birth(minimum_age=22, maximum_age=65),
                location=self.fake.city(),
                experience_level=random.choice(['entry', 'mid', 'senior', 'lead']),
                current_position=self.fake.job(),
                current_company=self.fake.company(),
                expected_salary=random.randint(40000, 200000),
                skills=', '.join(random.sample([
                    'Python', 'JavaScript', 'React', 'Django', 'PostgreSQL',
                    'AWS', 'Docker', 'Machine Learning', 'Data Analysis'
                ], k=random.randint(3, 6))),
                bio=self.fake.text(max_nb_chars=500),
                linkedin_url=f'https://linkedin.com/in/{user.username}' if random.choice([True, False]) else '',
                github_url=f'https://github.com/{user.username}' if random.choice([True, False]) else '',
                availability=random.choice([True, False])
            )
            
            # Create user skills
            skills = Skill.objects.order_by('?')[:random.randint(3, 8)]
            for skill in skills:
                UserSkill.objects.create(
                    user=user,
                    skill=skill,
                    proficiency_level=random.choice(['beginner', 'intermediate', 'advanced', 'expert']),
                    years_of_experience=random.randint(0, 10),
                    is_verified=random.choice([True, False]),
                    last_used=self.fake.date_between(start_date='-2y', end_date='today') if random.choice([True, False]) else None
                )
            
            # Create resume
            Resume.objects.create(
                job_seeker=user,
                original_filename=f'{user.username}_resume.pdf',
                is_primary=True,
                parsed_text=f'Resume content for {user.get_full_name()}. {self.fake.text(max_nb_chars=1000)}',
                file_size=random.randint(50000, 2000000),
                uploaded_at=self.fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone())
            )
            
            self.stdout.write(f'Created job seeker: {user.username}')
        
        # Create recruiters
        for i in range(recruiter_count):
            user = User.objects.create_user(
                username=f'recruiter_{i}',
                email=f'recruiter_{i}@example.com',
                password='testpass123',
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name(),
                user_type='recruiter',
                phone_number=self.fake.phone_number()[:15],
                is_verified=random.choice([True, False]),
                date_joined=self.fake.date_time_between(start_date='-1y', end_date='now', tzinfo=timezone.get_current_timezone()),
                last_login=self.fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone()) if random.choice([True, False]) else None
            )
            
            # Create recruiter profile
            RecruiterProfile.objects.create(
                user=user,
                company_name=self.fake.company(),
                company_website=self.fake.url(),
                company_size=random.choice(['1-10', '11-50', '51-200', '201-500', '500+']),
                industry=random.choice([
                    'Technology', 'Healthcare', 'Finance', 'Education', 'Manufacturing',
                    'Retail', 'Consulting', 'Media', 'Government', 'Non-profit'
                ]),
                company_description=self.fake.text(max_nb_chars=1000),
                location=self.fake.city()
            )
            
            self.stdout.write(f'Created recruiter: {user.username}')

    def create_job_posts(self, count):
        """Create sample job posts"""
        recruiters = User.objects.filter(user_type='recruiter')
        
        job_titles = [
            'Senior Software Engineer', 'Frontend Developer', 'Backend Developer',
            'Full Stack Developer', 'Data Scientist', 'Machine Learning Engineer',
            'DevOps Engineer', 'Product Manager', 'UI/UX Designer',
            'Quality Assurance Engineer', 'Database Administrator', 'System Administrator',
            'Mobile App Developer', 'Cloud Architect', 'Security Engineer'
        ]
        
        for i in range(count):
            recruiter = random.choice(recruiters)
            
            job = JobPost.objects.create(
                recruiter=recruiter,
                title=random.choice(job_titles),
                description=self.fake.text(max_nb_chars=2000),
                requirements=self.fake.text(max_nb_chars=1000),
                responsibilities=self.fake.text(max_nb_chars=1000),
                location=random.choice(['Remote', 'New York', 'San Francisco', 'Seattle', 'Austin', 'Boston']),
                remote_work_allowed=random.choice([True, False]),
                job_type=random.choice(['full_time', 'part_time', 'contract', 'internship']),
                experience_level=random.choice(['entry', 'mid', 'senior', 'lead', 'executive']),
                salary_min=random.randint(50000, 150000),
                salary_max=random.randint(80000, 250000),
                skills_required=', '.join(random.sample([
                    'Python', 'JavaScript', 'React', 'Django', 'Node.js',
                    'PostgreSQL', 'AWS', 'Docker', 'Kubernetes', 'Git'
                ], k=random.randint(3, 6))),
                benefits=self.fake.text(max_nb_chars=500),
                application_deadline=self.fake.date_time_between(start_date='now', end_date='+3m', tzinfo=timezone.get_current_timezone()),
                priority=random.choice(['low', 'normal', 'high', 'urgent']),
                is_active=random.choice([True, False]),
                is_featured=random.choice([True, False]) if random.random() < 0.2 else False,
                created_at=self.fake.date_time_between(start_date='-3m', end_date='now', tzinfo=timezone.get_current_timezone()),
                views_count=random.randint(0, 1000),
                applications_count=random.randint(0, 50)
            )
            
            # Create job analytics
            JobAnalytics.objects.create(
                job_post=job,
                total_views=job.views_count,
                unique_views=int(job.views_count * 0.8),
                total_applications=job.applications_count,
                conversion_rate=random.uniform(1.0, 15.0),
                avg_time_on_page=random.uniform(30.0, 300.0),
                bounce_rate=random.uniform(20.0, 80.0),
                top_referral_sources={'google': 40, 'linkedin': 30, 'direct': 20, 'other': 10},
                geographic_distribution={'US': 60, 'CA': 20, 'UK': 10, 'Other': 10},
                skill_match_distribution={'80-100': 20, '60-79': 40, '40-59': 30, '0-39': 10}
            )
            
            self.stdout.write(f'Created job post: {job.title}')

    def create_applications(self, count):
        """Create sample applications"""
        job_seekers = User.objects.filter(user_type='job_seeker')
        job_posts = JobPost.objects.all()
        
        for i in range(count):
            job_seeker = random.choice(job_seekers)
            job_post = random.choice(job_posts)
            
            # Check if application already exists
            if Application.objects.filter(job_seeker=job_seeker, job_post=job_post).exists():
                continue
            
            resume = Resume.objects.filter(job_seeker=job_seeker).first()
            if not resume:
                continue
            
            application = Application.objects.create(
                job_seeker=job_seeker,
                job_post=job_post,
                resume=resume,
                cover_letter=self.fake.text(max_nb_chars=1000) if random.choice([True, False]) else '',
                status=random.choice(['pending', 'reviewed', 'shortlisted', 'interview_scheduled', 'interviewed', 'hired', 'rejected']),
                applied_at=self.fake.date_time_between(start_date='-2m', end_date='now', tzinfo=timezone.get_current_timezone()),
                recruiter_notes=self.fake.text(max_nb_chars=500) if random.choice([True, False]) else '',
                match_score=random.uniform(0, 100)
            )
            
            # Create AI analysis result
            AIAnalysisResult.objects.create(
                resume=resume,
                job_post=job_post,
                application=application,
                analysis_type=random.choice(['resume_parse', 'job_match', 'skill_extraction']),
                input_data=f'Analysis input for {application}',
                analysis_result={
                    'skills_matched': random.sample(['Python', 'JavaScript', 'React', 'Django'], k=random.randint(1, 4)),
                    'experience_match': random.uniform(0.5, 1.0),
                    'education_match': random.uniform(0.6, 1.0),
                    'overall_score': application.match_score
                },
                confidence_score=random.uniform(0.7, 1.0),
                processing_time=random.uniform(0.5, 5.0)
            )
            
            self.stdout.write(f'Created application: {job_seeker.username} -> {job_post.title}')

    def create_analytics_data(self):
        """Create sample analytics data"""
        job_posts = JobPost.objects.all()
        job_seekers = User.objects.filter(user_type='job_seeker')
        
        # Create job views
        for _ in range(500):
            job_post = random.choice(job_posts)
            viewer = random.choice(job_seekers) if random.choice([True, False]) else None
            
            JobView.objects.create(
                job_post=job_post,
                viewer=viewer,
                ip_address=self.fake.ipv4(),
                user_agent=self.fake.user_agent(),
                referrer=random.choice(['https://google.com', 'https://linkedin.com', '', 'https://indeed.com']),
                session_id=self.fake.uuid4(),
                view_duration=random.randint(10, 600),
                viewed_at=self.fake.date_time_between(start_date='-1m', end_date='now', tzinfo=timezone.get_current_timezone())
            )
        
        self.stdout.write('Created job view analytics data')

    def create_notification_data(self):
        """Create sample notification data"""
        users = User.objects.all()
        job_posts = JobPost.objects.all()
        applications = Application.objects.all()
        
        # Create notification templates
        template_data = [
            ('job_posted', 'websocket', 'New Job Posted', 'A new job "{job_title}" has been posted by {company_name}'),
            ('application_received', 'websocket', 'Application Received', 'You received a new application for "{job_title}"'),
            ('application_status_changed', 'email', 'Application Status Update', 'Your application status for "{job_title}" has been updated to {status}'),
            ('match_score_calculated', 'websocket', 'Match Score Ready', 'Your match score for "{job_title}" is {score}%'),
        ]
        
        for template_type, delivery_channel, title, message in template_data:
            NotificationTemplate.objects.get_or_create(
                template_type=template_type,
                delivery_channel=delivery_channel,
                defaults={
                    'title_template': title,
                    'message_template': message,
                    'is_active': True,
                    'is_default': True
                }
            )
        
        # Create notification preferences for users
        for user in users:
            NotificationPreference.objects.get_or_create(
                user=user,
                defaults={
                    'job_posted_enabled': random.choice([True, False]),
                    'application_received_enabled': True,
                    'application_status_changed_enabled': True,
                    'match_score_calculated_enabled': random.choice([True, False]),
                    'digest_frequency': random.choice(['immediate', 'hourly', 'daily', 'weekly']),
                    'quiet_hours_enabled': random.choice([True, False])
                }
            )
        
        # Create notifications
        for _ in range(200):
            recipient = random.choice(users)
            notification_type = random.choice(['job_posted', 'application_received', 'application_status_changed', 'match_score_calculated'])
            
            Notification.objects.create(
                recipient=recipient,
                notification_type=notification_type,
                title=f'Test {notification_type.replace("_", " ").title()}',
                message=self.fake.text(max_nb_chars=200),
                priority=random.choice(['low', 'normal', 'high', 'urgent']),
                job_post=random.choice(job_posts) if random.choice([True, False]) else None,
                application=random.choice(applications) if random.choice([True, False]) else None,
                is_read=random.choice([True, False]),
                is_sent=random.choice([True, False]),
                created_at=self.fake.date_time_between(start_date='-1m', end_date='now', tzinfo=timezone.get_current_timezone())
            )
        
        self.stdout.write('Created notification data')

    def create_interview_data(self):
        """Create sample interview data"""
        applications = Application.objects.filter(status__in=['shortlisted', 'interview_scheduled', 'interviewed'])
        
        for application in applications[:20]:  # Create interviews for first 20 eligible applications
            interview = InterviewSession.objects.create(
                application=application,
                interview_type=random.choice(['ai_screening', 'technical', 'hr', 'final']),
                scheduled_at=self.fake.date_time_between(start_date='now', end_date='+1m', tzinfo=timezone.get_current_timezone()),
                duration_minutes=random.choice([30, 45, 60, 90]),
                status=random.choice(['scheduled', 'in_progress', 'completed', 'cancelled']),
                interviewer=application.job_post.recruiter if random.choice([True, False]) else None,
                meeting_link=self.fake.url() if random.choice([True, False]) else '',
                notes=self.fake.text(max_nb_chars=500) if random.choice([True, False]) else '',
                rating=random.randint(1, 10) if random.choice([True, False]) else None,
                feedback=self.fake.text(max_nb_chars=1000) if random.choice([True, False]) else ''
            )
            
            # Create AI interview questions for AI screening interviews
            if interview.interview_type == 'ai_screening':
                for _ in range(random.randint(3, 8)):
                    AIInterviewQuestion.objects.create(
                        interview_session=interview,
                        question_text=self.fake.text(max_nb_chars=200) + '?',
                        question_type=random.choice(['technical', 'behavioral', 'situational', 'coding']),
                        difficulty_level=random.choice(['easy', 'medium', 'hard']),
                        expected_answer=self.fake.text(max_nb_chars=300),
                        candidate_answer=self.fake.text(max_nb_chars=400) if random.choice([True, False]) else '',
                        ai_score=random.uniform(0, 100),
                        time_taken_seconds=random.randint(30, 300)
                    )
        
        self.stdout.write('Created interview data')

        # Create some verification tokens for testing
        unverified_users = User.objects.filter(is_verified=False)[:10]
        for user in unverified_users:
            EmailVerificationToken.objects.create(
                user=user,
                token=self.fake.uuid4().replace('-', ''),
                expires_at=timezone.now() + timedelta(hours=24)
            )
        
        # Create some password reset tokens
        for user in User.objects.order_by('?')[:5]:
            PasswordResetToken.objects.create(
                user=user,
                token=self.fake.uuid4().replace('-', ''),
                expires_at=timezone.now() + timedelta(hours=1)
            )
        
        self.stdout.write('Created token data')