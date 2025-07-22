"""
Management command to populate default notification templates.
"""

from django.core.management.base import BaseCommand
from matcher.models import NotificationTemplate


class Command(BaseCommand):
    help = 'Populate default notification templates'

    def handle(self, *args, **options):
        """Create default notification templates."""
        
        templates = [
            # Job Posted Templates
            {
                'template_type': 'job_posted',
                'delivery_channel': 'websocket',
                'title_template': 'New Job: {job_title}',
                'message_template': 'A new {job_type} position at {company_name} in {location} has been posted. Required skills: {skills_required}',
                'available_variables': {
                    'job_title': 'Job title',
                    'company_name': 'Company name',
                    'location': 'Job location',
                    'job_type': 'Job type (full-time, part-time, etc.)',
                    'skills_required': 'Required skills',
                    'user_name': 'Recipient name'
                },
                'is_default': True
            },
            {
                'template_type': 'job_posted',
                'delivery_channel': 'email',
                'title_template': 'New Job Opportunity: {job_title}',
                'message_template': 'Hi {user_name}, a new {job_type} position at {company_name} in {location} has been posted that might interest you.',
                'email_subject_template': 'New Job Alert: {job_title} at {company_name}',
                'email_html_template': '''
                <h2>New Job Opportunity</h2>
                <p>Hi {user_name},</p>
                <p>A new <strong>{job_type}</strong> position has been posted that might interest you:</p>
                <ul>
                    <li><strong>Position:</strong> {job_title}</li>
                    <li><strong>Company:</strong> {company_name}</li>
                    <li><strong>Location:</strong> {location}</li>
                    <li><strong>Required Skills:</strong> {skills_required}</li>
                </ul>
                <p>Visit HireWise to learn more and apply!</p>
                ''',
                'available_variables': {
                    'job_title': 'Job title',
                    'company_name': 'Company name',
                    'location': 'Job location',
                    'job_type': 'Job type',
                    'skills_required': 'Required skills',
                    'user_name': 'Recipient name'
                },
                'is_default': True
            },
            
            # Application Received Templates
            {
                'template_type': 'application_received',
                'delivery_channel': 'websocket',
                'title_template': 'New Application: {job_title}',
                'message_template': '{applicant_name} has applied for the {job_title} position.',
                'available_variables': {
                    'applicant_name': 'Name of the applicant',
                    'job_title': 'Job title',
                    'company_name': 'Company name',
                    'application_date': 'Application date',
                    'recruiter_name': 'Recruiter name'
                },
                'is_default': True
            },
            {
                'template_type': 'application_received',
                'delivery_channel': 'email',
                'title_template': 'New Application Received',
                'message_template': 'Hi {recruiter_name}, you have received a new application for {job_title}.',
                'email_subject_template': 'New Application: {job_title} - {applicant_name}',
                'email_html_template': '''
                <h2>New Application Received</h2>
                <p>Hi {recruiter_name},</p>
                <p>You have received a new application for the <strong>{job_title}</strong> position:</p>
                <ul>
                    <li><strong>Applicant:</strong> {applicant_name}</li>
                    <li><strong>Position:</strong> {job_title}</li>
                    <li><strong>Application Date:</strong> {application_date}</li>
                </ul>
                <p>Log in to HireWise to review the application.</p>
                ''',
                'available_variables': {
                    'applicant_name': 'Name of the applicant',
                    'job_title': 'Job title',
                    'company_name': 'Company name',
                    'application_date': 'Application date',
                    'recruiter_name': 'Recruiter name'
                },
                'is_default': True
            },
            
            # Application Status Changed Templates
            {
                'template_type': 'application_status_changed',
                'delivery_channel': 'websocket',
                'title_template': 'Application Update: {job_title}',
                'message_template': 'Your application for {job_title} at {company_name} {status_message}.',
                'available_variables': {
                    'job_title': 'Job title',
                    'company_name': 'Company name',
                    'old_status': 'Previous status',
                    'new_status': 'New status',
                    'status_message': 'Human-readable status message',
                    'user_name': 'Applicant name'
                },
                'is_default': True
            },
            {
                'template_type': 'application_status_changed',
                'delivery_channel': 'email',
                'title_template': 'Application Status Update',
                'message_template': 'Hi {user_name}, your application status has been updated.',
                'email_subject_template': 'Application Update: {job_title} - {new_status}',
                'email_html_template': '''
                <h2>Application Status Update</h2>
                <p>Hi {user_name},</p>
                <p>Your application for <strong>{job_title}</strong> at {company_name} has been updated:</p>
                <ul>
                    <li><strong>Position:</strong> {job_title}</li>
                    <li><strong>Company:</strong> {company_name}</li>
                    <li><strong>Previous Status:</strong> {old_status}</li>
                    <li><strong>New Status:</strong> {new_status}</li>
                </ul>
                <p>Your application {status_message}.</p>
                <p>Log in to HireWise for more details.</p>
                ''',
                'available_variables': {
                    'job_title': 'Job title',
                    'company_name': 'Company name',
                    'old_status': 'Previous status',
                    'new_status': 'New status',
                    'status_message': 'Human-readable status message',
                    'user_name': 'Applicant name'
                },
                'is_default': True
            },
            
            # Match Score Calculated Templates
            {
                'template_type': 'match_score_calculated',
                'delivery_channel': 'websocket',
                'title_template': 'Match Score: {job_title}',
                'message_template': 'Your compatibility score with {job_title} at {company_name} is {match_score}%.',
                'available_variables': {
                    'job_title': 'Job title',
                    'match_score': 'Match score percentage',
                    'company_name': 'Company name',
                    'user_name': 'Job seeker name'
                },
                'is_default': True
            },
            {
                'template_type': 'match_score_calculated',
                'delivery_channel': 'email',
                'title_template': 'Job Match Score Available',
                'message_template': 'Hi {user_name}, your job match score is ready.',
                'email_subject_template': 'Match Score: {match_score}% for {job_title}',
                'email_html_template': '''
                <h2>Job Match Score</h2>
                <p>Hi {user_name},</p>
                <p>Your compatibility score with <strong>{job_title}</strong> at {company_name} has been calculated:</p>
                <div style="text-align: center; font-size: 24px; color: #007bff; margin: 20px 0;">
                    <strong>{match_score}% Match</strong>
                </div>
                <p>Log in to HireWise to see detailed analysis and apply if interested.</p>
                ''',
                'available_variables': {
                    'job_title': 'Job title',
                    'match_score': 'Match score percentage',
                    'company_name': 'Company name',
                    'user_name': 'Job seeker name'
                },
                'is_default': True
            },
            
            # Interview Scheduled Templates
            {
                'template_type': 'interview_scheduled',
                'delivery_channel': 'websocket',
                'title_template': 'Interview Scheduled: {job_title}',
                'message_template': 'Your interview for {job_title} has been scheduled for {interview_datetime}.',
                'available_variables': {
                    'job_title': 'Job title',
                    'company_name': 'Company name',
                    'interview_datetime': 'Interview date and time',
                    'interview_type': 'Interview type',
                    'user_name': 'Participant name'
                },
                'is_default': True
            },
            {
                'template_type': 'interview_scheduled',
                'delivery_channel': 'email',
                'title_template': 'Interview Scheduled',
                'message_template': 'Hi {user_name}, your interview has been scheduled.',
                'email_subject_template': 'Interview Scheduled: {job_title} - {interview_datetime}',
                'email_html_template': '''
                <h2>Interview Scheduled</h2>
                <p>Hi {user_name},</p>
                <p>Your interview for <strong>{job_title}</strong> at {company_name} has been scheduled:</p>
                <ul>
                    <li><strong>Position:</strong> {job_title}</li>
                    <li><strong>Company:</strong> {company_name}</li>
                    <li><strong>Date & Time:</strong> {interview_datetime}</li>
                    <li><strong>Interview Type:</strong> {interview_type}</li>
                </ul>
                <p>Please prepare accordingly and log in to HireWise for more details.</p>
                ''',
                'available_variables': {
                    'job_title': 'Job title',
                    'company_name': 'Company name',
                    'interview_datetime': 'Interview date and time',
                    'interview_type': 'Interview type',
                    'user_name': 'Participant name'
                },
                'is_default': True
            },
            
            # System Message Templates
            {
                'template_type': 'system_message',
                'delivery_channel': 'websocket',
                'title_template': 'System Notification',
                'message_template': '{message}',
                'available_variables': {
                    'message': 'System message content',
                    'user_name': 'Recipient name'
                },
                'is_default': True
            },
            {
                'template_type': 'system_message',
                'delivery_channel': 'email',
                'title_template': 'HireWise System Notification',
                'message_template': 'Hi {user_name}, you have a system notification.',
                'email_subject_template': 'HireWise System Notification',
                'email_html_template': '''
                <h2>System Notification</h2>
                <p>Hi {user_name},</p>
                <p>{message}</p>
                <p>Best regards,<br>The HireWise Team</p>
                ''',
                'available_variables': {
                    'message': 'System message content',
                    'user_name': 'Recipient name'
                },
                'is_default': True
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                template_type=template_data['template_type'],
                delivery_channel=template_data['delivery_channel'],
                is_default=template_data['is_default'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created template: {template.template_type} - {template.delivery_channel}'
                    )
                )
            else:
                # Update existing template if needed
                updated = False
                for field, value in template_data.items():
                    if field not in ['template_type', 'delivery_channel', 'is_default']:
                        if getattr(template, field) != value:
                            setattr(template, field, value)
                            updated = True
                
                if updated:
                    template.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Updated template: {template.template_type} - {template.delivery_channel}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed notification templates: '
                f'{created_count} created, {updated_count} updated'
            )
        )