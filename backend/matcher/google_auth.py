import requests
from django.conf import settings
from .models import User, JobSeekerProfile, RecruiterProfile
from rest_framework_simplejwt.tokens import RefreshToken

def verify_google_id_token(id_token):
    # Google's tokeninfo endpoint
    response = requests.get(
        'https://oauth2.googleapis.com/tokeninfo',
        params={'id_token': id_token}
    )
    if response.status_code != 200:
        return None
    data = response.json()
    # Check audience
    if data.get('aud') != settings.OAUTH_CLIENT_ID:
        return None
    return data

def get_or_create_user_from_google(data):
    email = data.get('email')
    first_name = data.get('given_name', '')
    last_name = data.get('family_name', '')
    # Try to find user
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email.split('@')[0],
            'first_name': first_name,
            'last_name': last_name,
            'user_type': 'job_seeker',
            'is_verified': True,
        }
    )
    if created:
        JobSeekerProfile.objects.create(user=user)
    return user

def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
