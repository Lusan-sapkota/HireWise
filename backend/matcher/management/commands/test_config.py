"""
Management command to test the Django configuration setup.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import redis
from celery import Celery


class Command(BaseCommand):
    help = 'Test Django configuration setup'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Django Configuration...'))
        
        # Test basic settings
        self.stdout.write(f'DEBUG: {settings.DEBUG}')
        self.stdout.write(f'SECRET_KEY configured: {"Yes" if settings.SECRET_KEY else "No"}')
        self.stdout.write(f'Database Engine: {settings.DATABASES["default"]["ENGINE"]}')
        
        # Test JWT settings
        if hasattr(settings, 'SIMPLE_JWT'):
            self.stdout.write(self.style.SUCCESS('✓ JWT settings configured'))
        else:
            self.stdout.write(self.style.ERROR('✗ JWT settings missing'))
        
        # Test Channels settings
        if hasattr(settings, 'CHANNEL_LAYERS'):
            self.stdout.write(self.style.SUCCESS('✓ Channels settings configured'))
        else:
            self.stdout.write(self.style.ERROR('✗ Channels settings missing'))
        
        # Test Celery settings
        if hasattr(settings, 'CELERY_BROKER_URL'):
            self.stdout.write(self.style.SUCCESS('✓ Celery settings configured'))
        else:
            self.stdout.write(self.style.ERROR('✗ Celery settings missing'))
        
        # Test AI settings
        if hasattr(settings, 'GEMINI_API_KEY'):
            self.stdout.write(self.style.SUCCESS('✓ AI settings configured'))
        else:
            self.stdout.write(self.style.ERROR('✗ AI settings missing'))
        
        # Test Redis connection (optional)
        try:
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None
            )
            r.ping()
            self.stdout.write(self.style.SUCCESS('✓ Redis connection successful'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Redis connection failed: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Configuration test completed!'))