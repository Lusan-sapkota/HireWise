#!/usr/bin/env python
"""
Simple test script to verify AI interview functionality
"""

import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirewise.settings')
django.setup()

from matcher.models import User, JobPost, Application, Resume, InterviewSession, AIInterviewQuestion
from matcher.ml_services import generate_interview_questions, analyze_interview_response, generate_interview_analysis
from django.utils import timezone
import uuid

def test_ai_interview_functionality():
    """Test the AI interview functionality"""
    print("Testing AI Interview Functionality...")
    
    try:
        # Create test users with unique names
        print("1. Creating test users...")
        unique_id = str(uuid.uuid4())[:8]
        job_seeker = User.objects.create_user(
            username=f'test_job_seeker_{unique_id}',
            email=f'jobseeker_{unique_id}@test.com',
            password='testpass123',
            user_type='job_seeker'
        )
        
        recruiter = User.objects.create_user(
            username=f'test_recruiter_{unique_id}',
            email=f'recruiter_{unique_id}@test.com',
            password='testpass123',
            user_type='recruiter'
        )
        
        # Create recruiter profile
        from matcher.models import RecruiterProfile
        recruiter_profile = RecruiterProfile.objects.create(
            user=recruiter,
            company_name='Test Company',
            industry='Technology'
        )
        
        # Create job seeker profile
        from matcher.models import JobSeekerProfile
        job_seeker_profile = JobSeekerProfile.objects.create(
            user=job_seeker,
            experience_level='mid',
            skills='Python, Django, JavaScript, React'
        )
        
        print("✓ Users created successfully")
        
        # Create a job post
        print("2. Creating job post...")
        job_post = JobPost.objects.create(
            recruiter=recruiter,
            title='Senior Python Developer',
            description='We are looking for a senior Python developer with Django experience.',
            requirements='5+ years Python experience, Django framework, REST APIs',
            skills_required='Python, Django, REST API, PostgreSQL',
            experience_level='senior',
            job_type='full_time',
            location='Remote'
        )
        print("✓ Job post created successfully")
        
        # Create a resume
        print("3. Creating resume...")
        resume = Resume.objects.create(
            job_seeker=job_seeker,
            original_filename='test_resume.pdf',
            parsed_text='Senior Python Developer with 6 years of experience in Django, REST APIs, and PostgreSQL. Built scalable web applications and microservices.',
            file_size=1024
        )
        print("✓ Resume created successfully")
        
        # Create an application
        print("4. Creating application...")
        application = Application.objects.create(
            job_seeker=job_seeker,
            job_post=job_post,
            resume=resume,
            status='shortlisted'
        )
        print("✓ Application created successfully")
        
        # Create interview session
        print("5. Creating interview session...")
        interview_session = InterviewSession.objects.create(
            application=application,
            interview_type='technical',
            status='in_progress',
            scheduled_at=timezone.now()
        )
        print("✓ Interview session created successfully")
        
        # Test question generation
        print("6. Testing question generation...")
        questions = generate_interview_questions(
            job_post=job_post,
            resume=resume,
            interview_type='technical',
            num_questions=3
        )
        
        if questions:
            print(f"✓ Generated {len(questions)} questions successfully")
            for i, question in enumerate(questions, 1):
                print(f"   Question {i}: {question['question_text'][:80]}...")
        else:
            print("✗ Failed to generate questions")
            return False
        
        # Store questions in database
        print("7. Storing questions in database...")
        stored_questions = []
        for question_data in questions:
            question = AIInterviewQuestion.objects.create(
                interview_session=interview_session,
                question_text=question_data['question_text'],
                question_type=question_data['question_type'],
                difficulty_level=question_data['difficulty_level']
            )
            stored_questions.append(question)
        print(f"✓ Stored {len(stored_questions)} questions in database")
        
        # Test response analysis
        print("8. Testing response analysis...")
        test_response = "I have extensive experience with Python and Django. I've built REST APIs using Django REST Framework and worked with PostgreSQL databases. In my previous role, I developed a microservices architecture that handled millions of requests per day."
        
        # Add response to first question
        first_question = stored_questions[0]
        analysis = analyze_interview_response(
            question_id=first_question.id,
            response=test_response,
            session=interview_session
        )
        
        if analysis and 'score' in analysis:
            print(f"✓ Response analysis completed with score: {analysis['score']}")
            print(f"   Feedback: {analysis.get('detailed_feedback', 'No feedback')[:100]}...")
        else:
            print("✗ Failed to analyze response")
            return False
        
        # Complete the interview session
        print("9. Testing session completion...")
        interview_session.status = 'completed'
        interview_session.save()
        
        # Test comprehensive analysis
        final_analysis = generate_interview_analysis(interview_session)
        
        if final_analysis and 'overall_score' in final_analysis:
            print(f"✓ Session analysis completed with overall score: {final_analysis['overall_score']}")
            print(f"   Performance summary: {final_analysis.get('performance_summary', 'No summary')[:100]}...")
        else:
            print("✗ Failed to generate session analysis")
            return False
        
        print("\n🎉 All AI interview functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup test data
        print("\n10. Cleaning up test data...")
        try:
            User.objects.filter(username__startswith='test_job_seeker_').delete()
            User.objects.filter(username__startswith='test_recruiter_').delete()
            print("✓ Test data cleaned up")
        except Exception as e:
            print(f"Warning: Cleanup failed: {str(e)}")

if __name__ == '__main__':
    success = test_ai_interview_functionality()
    sys.exit(0 if success else 1)