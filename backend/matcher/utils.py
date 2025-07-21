"""
AI and utility functions for Hirewise platform
"""
import os
import re
import json
import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import google.generativeai as genai
from datetime import datetime
import logging
import secrets
import string

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

logger = logging.getLogger(__name__)


def parse_resume(file_path):
    """
    Parse resume from PDF or DOCX file and extract text content
    """
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            text = extract_text_from_pdf(file_path)
        elif file_extension in ['.doc', '.docx']:
            text = extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Clean and process the text
        cleaned_text = clean_text(text)
        
        # Extract structured information
        extracted_info = extract_resume_sections(cleaned_text)
        
        return {
            'text': cleaned_text,
            'sections': extracted_info,
            'confidence': 0.85,
            'processed_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error parsing resume {file_path}: {str(e)}")
        return {
            'text': '',
            'sections': {},
            'confidence': 0.0,
            'error': str(e)
        }


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\\n"
    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {str(e)}")
        raise
    
    return text


def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\\n"
    except Exception as e:
        logger.error(f"Error reading DOCX {file_path}: {str(e)}")
        raise
    
    return text


def clean_text(text):
    """Clean and normalize text"""
    # Remove extra whitespace and normalize
    text = re.sub(r'\\s+', ' ', text)
    text = re.sub(r'\\n+', '\\n', text)
    text = text.strip()
    
    return text


def extract_resume_sections(text):
    """
    Extract different sections from resume text using pattern matching
    """
    sections = {}
    
    # Email extraction
    email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
    emails = re.findall(email_pattern, text)
    sections['emails'] = emails
    
    # Phone number extraction
    phone_pattern = r'\\b(?:\\+?1[-.]?)?\\(?([0-9]{3})\\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\\b'
    phones = re.findall(phone_pattern, text)
    sections['phones'] = ['-'.join(phone) for phone in phones]
    
    # Extract skills (simple keyword matching)
    technical_skills = extract_technical_skills(text)
    sections['technical_skills'] = technical_skills
    
    # Extract education (simple pattern matching)
    education = extract_education_info(text)
    sections['education'] = education
    
    # Extract experience years
    experience_years = extract_experience_years(text)
    sections['experience_years'] = experience_years
    
    return sections


def extract_technical_skills(text):
    """Extract technical skills from text"""
    # Common technical skills (this can be expanded)
    skill_keywords = [
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
        'django', 'flask', 'spring', 'sql', 'mysql', 'postgresql', 'mongodb',
        'aws', 'azure', 'docker', 'kubernetes', 'git', 'linux', 'windows',
        'html', 'css', 'bootstrap', 'jquery', 'php', 'c++', 'c#', 'ruby',
        'machine learning', 'ai', 'data science', 'tensorflow', 'pytorch',
        'rest api', 'graphql', 'microservices', 'devops', 'ci/cd', 'jenkins'
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in skill_keywords:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    
    return list(set(found_skills))  # Remove duplicates


def extract_education_info(text):
    """Extract education information"""
    education_keywords = [
        'bachelor', 'master', 'phd', 'degree', 'university', 'college',
        'diploma', 'certification', 'b.tech', 'm.tech', 'mba', 'b.sc', 'm.sc'
    ]
    
    education_info = []
    lines = text.split('\\n')
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in education_keywords):
            education_info.append(line.strip())
    
    return education_info


def extract_experience_years(text):
    """Extract years of experience from text"""
    # Pattern for "X years of experience"
    patterns = [
        r'(\\d+)\\+?\\s*years?\\s*of\\s*experience',
        r'(\\d+)\\+?\\s*years?\\s*experience',
        r'experience\\s*:?\\s*(\\d+)\\+?\\s*years?'
    ]
    
    text_lower = text.lower()
    years = []
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        years.extend([int(match) for match in matches])
    
    return max(years) if years else 0


def extract_skills_from_text(text):
    """
    Enhanced skill extraction using NLP techniques
    """
    try:
        # Tokenize and process text
        tokens = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        
        # Remove stopwords and non-alphabetic tokens
        filtered_tokens = [
            token for token in tokens 
            if token.isalpha() and token not in stop_words and len(token) > 2
        ]
        
        # Extract skills using keyword matching and context
        technical_skills = extract_technical_skills(text)
        
        # Add skills extracted from tokens (this can be enhanced with ML models)
        skill_candidates = []
        for token in filtered_tokens:
            if token in ['programming', 'development', 'design', 'management']:
                skill_candidates.append(token)
        
        all_skills = list(set(technical_skills + skill_candidates))
        
        return {
            'skills': all_skills,
            'technical_skills': technical_skills,
            'confidence': 0.8,
            'extracted_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error extracting skills: {str(e)}")
        return {
            'skills': [],
            'technical_skills': [],
            'confidence': 0.0,
            'error': str(e)
        }


def calculate_match_score(resume, job_post):
    """
    Calculate matching score between resume and job post using TF-IDF and cosine similarity
    """
    try:
        # Prepare texts
        resume_text = resume.parsed_text if resume.parsed_text else ""
        job_text = f"{job_post.title} {job_post.description} {job_post.requirements} {job_post.skills_required}"
        
        if not resume_text or not job_text:
            return 0.0
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)
        similarity_score = similarity_matrix[0][1]
        
        # Normalize score to 0-1 range and apply some adjustments
        normalized_score = min(max(similarity_score * 1.5, 0.0), 1.0)
        
        return round(normalized_score, 3)
    
    except Exception as e:
        logger.error(f"Error calculating match score: {str(e)}")
        return 0.0


def analyze_job_match(resume, job_post):
    """
    Detailed analysis of job match with skill comparison
    """
    try:
        # Extract skills from resume and job post
        resume_skills = set(extract_technical_skills(resume.parsed_text.lower()))
        job_skills_text = f"{job_post.requirements} {job_post.skills_required}".lower()
        job_skills = set(extract_technical_skills(job_skills_text))
        
        # Find matching and missing skills
        matching_skills = list(resume_skills.intersection(job_skills))
        missing_skills = list(job_skills - resume_skills)
        
        # Generate recommendations
        recommendations = generate_match_recommendations(matching_skills, missing_skills, job_post)
        
        return {
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'recommendations': recommendations,
            'skill_match_percentage': len(matching_skills) / len(job_skills) * 100 if job_skills else 0,
            'analyzed_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error analyzing job match: {str(e)}")
        return {
            'matching_skills': [],
            'missing_skills': [],
            'recommendations': 'Analysis temporarily unavailable',
            'skill_match_percentage': 0,
            'error': str(e)
        }


def generate_match_recommendations(matching_skills, missing_skills, job_post):
    """Generate recommendations for job seekers"""
    recommendations = []
    
    if len(matching_skills) > len(missing_skills):
        recommendations.append("Great match! You have most of the required skills.")
    elif len(missing_skills) > 0:
        recommendations.append(f"Consider learning: {', '.join(missing_skills[:3])}")
    
    if job_post.experience_level == 'entry' and len(matching_skills) >= 2:
        recommendations.append("Your skills align well with this entry-level position.")
    elif job_post.experience_level == 'senior' and len(matching_skills) < 5:
        recommendations.append("This senior role requires more experience. Consider building more skills.")
    
    return " ".join(recommendations) if recommendations else "Apply and highlight your relevant experience."


def generate_interview_questions(job_post, interview_type='technical'):
    """
    Generate AI-powered interview questions based on job post
    """
    try:
        # Mock AI question generation (replace with actual AI service)
        questions = []
        
        if interview_type == 'technical':
            # Extract key skills from job post
            skills = extract_technical_skills(job_post.skills_required.lower())
            
            # Generate technical questions
            for skill in skills[:5]:  # Top 5 skills
                questions.append({
                    'question': f"Can you explain your experience with {skill}?",
                    'type': 'technical',
                    'difficulty': 'medium',
                    'skill_focus': skill
                })
            
            # Add general technical questions
            questions.extend([
                {
                    'question': "Describe a challenging project you worked on recently.",
                    'type': 'technical',
                    'difficulty': 'medium',
                    'skill_focus': 'problem_solving'
                },
                {
                    'question': "How do you stay updated with new technologies?",
                    'type': 'technical',
                    'difficulty': 'easy',
                    'skill_focus': 'learning'
                }
            ])
        
        elif interview_type == 'behavioral':
            questions = [
                {
                    'question': "Tell me about yourself and your career journey.",
                    'type': 'behavioral',
                    'difficulty': 'easy'
                },
                {
                    'question': "Describe a time when you had to work under pressure.",
                    'type': 'behavioral',
                    'difficulty': 'medium'
                },
                {
                    'question': "How do you handle conflicts in a team?",
                    'type': 'behavioral',
                    'difficulty': 'medium'
                }
            ]
        
        elif interview_type == 'hr':
            questions = [
                {
                    'question': f"Why are you interested in working at {job_post.recruiter.recruiter_profile.company_name}?",
                    'type': 'hr',
                    'difficulty': 'easy'
                },
                {
                    'question': "What are your salary expectations?",
                    'type': 'hr',
                    'difficulty': 'medium'
                },
                {
                    'question': "Where do you see yourself in 5 years?",
                    'type': 'hr',
                    'difficulty': 'easy'
                }
            ]
        
        return questions
    
    except Exception as e:
        logger.error(f"Error generating interview questions: {str(e)}")
        return [
            {
                'question': "Please introduce yourself.",
                'type': 'general',
                'difficulty': 'easy'
            }
        ]


def analyze_interview_response(question, response):
    """
    Analyze interview response using AI (mock implementation)
    """
    try:
        # Mock analysis - in production, use actual AI/NLP models
        word_count = len(response.split())
        
        # Simple scoring based on response length and keywords
        score = min(word_count / 50 * 10, 10)  # Basic scoring
        
        feedback = []
        if word_count < 10:
            feedback.append("Consider providing more detailed responses.")
        elif word_count > 200:
            feedback.append("Try to be more concise in your answers.")
        else:
            feedback.append("Good response length.")
        
        return {
            'score': round(score, 1),
            'feedback': " ".join(feedback),
            'word_count': word_count,
            'analyzed_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error analyzing interview response: {str(e)}")
        return {
            'score': 0.0,
            'feedback': 'Analysis unavailable',
            'error': str(e)
        }


# Gemini Integration (Google Generative AI)
def get_ai_insights(text, context="resume"):
    """
    Get AI insights using Gemini (Google Generative AI)
    """
    try:
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return "AI insights require Gemini API key configuration"
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""
        Analyze the following {context} and provide insights:\n\n{text}\n\nPlease provide:\n1. Key strengths\n2. Areas for improvement\n3. Recommendations
        """
        response = model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else str(response)
    except Exception as e:
        logger.error(f"Error getting AI insights: {str(e)}")
        return "AI insights temporarily unavailable"


# Email and Authentication Utilities
def generate_secure_token(length=32):
    """
    Generate a secure random token for email verification and password reset
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def send_verification_email(user, token):
    """
    Send email verification email to user
    """
    try:
        subject = 'Verify Your HireWise Account'
        
        # Create verification URL (you may need to adjust the domain)
        verification_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={token}"
        
        # Email content
        html_message = f"""
        <html>
        <body>
            <h2>Welcome to HireWise!</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>Thank you for registering with HireWise. Please click the link below to verify your email address:</p>
            <p><a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>Or copy and paste this link in your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account with HireWise, please ignore this email.</p>
            <br>
            <p>Best regards,<br>The HireWise Team</p>
        </body>
        </html>
        """
        
        plain_message = f"""
        Welcome to HireWise!
        
        Hi {user.first_name or user.username},
        
        Thank you for registering with HireWise. Please visit the following link to verify your email address:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account with HireWise, please ignore this email.
        
        Best regards,
        The HireWise Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hirewise.com'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(user, token):
    """
    Send password reset email to user
    """
    try:
        subject = 'Reset Your HireWise Password'
        
        # Create reset URL (you may need to adjust the domain)
        reset_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}"
        
        # Email content
        html_message = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>We received a request to reset your password for your HireWise account.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_url}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>Or copy and paste this link in your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
            <br>
            <p>Best regards,<br>The HireWise Team</p>
        </body>
        </html>
        """
        
        plain_message = f"""
        Password Reset Request
        
        Hi {user.first_name or user.username},
        
        We received a request to reset your password for your HireWise account.
        
        Please visit the following link to reset your password:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
        
        Best regards,
        The HireWise Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hirewise.com'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending password reset email to {user.email}: {str(e)}")
        return False


def send_welcome_email(user):
    """
    Send welcome email to newly verified users
    """
    try:
        subject = 'Welcome to HireWise - Your Account is Ready!'
        
        # Email content
        html_message = f"""
        <html>
        <body>
            <h2>Welcome to HireWise!</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>Your email has been successfully verified and your HireWise account is now active!</p>
            
            {'<p>As a job seeker, you can now:</p><ul><li>Upload and manage your resumes</li><li>Search and apply for jobs</li><li>Get AI-powered job recommendations</li><li>Track your applications</li></ul>' if user.user_type == 'job_seeker' else ''}
            
            {'<p>As a recruiter, you can now:</p><ul><li>Post job openings</li><li>Review applications</li><li>Schedule interviews</li><li>Manage your company profile</li></ul>' if user.user_type == 'recruiter' else ''}
            
            <p>Get started by logging into your account:</p>
            <p><a href="{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/login" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Login to HireWise</a></p>
            
            <p>If you have any questions, feel free to contact our support team.</p>
            <br>
            <p>Best regards,<br>The HireWise Team</p>
        </body>
        </html>
        """
        
        plain_message = f"""
        Welcome to HireWise!
        
        Hi {user.first_name or user.username},
        
        Your email has been successfully verified and your HireWise account is now active!
        
        Get started by logging into your account at: {getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/login
        
        If you have any questions, feel free to contact our support team.
        
        Best regards,
        The HireWise Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hirewise.com'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending welcome email to {user.email}: {str(e)}")
        return False
