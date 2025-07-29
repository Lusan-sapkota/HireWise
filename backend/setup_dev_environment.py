#!/usr/bin/env python3
"""
HireWise Development Environment Setup Script
This script sets up the complete development environment including:
- Database migrations
- Redis configuration verification
- Celery setup verification
- Logging infrastructure
- Health checks
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirewise.settings')

import django
django.setup()

from django.core.management import execute_from_command_line
from django.conf import settings
from django.core.cache import cache
from django.db import connection
import redis

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DevEnvironmentSetup:
    """Development environment setup manager"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.success_count = 0
        self.total_steps = 8
    
    def run_setup(self):
        """Run complete development environment setup"""
        logger.info("🚀 Starting HireWise Development Environment Setup")
        logger.info("=" * 60)
        
        try:
            self.create_directories()
            self.check_dependencies()
            self.setup_database()
            self.verify_redis()
            self.setup_celery()
            self.setup_logging()
            self.run_health_checks()
            self.create_superuser()
            
            logger.info("=" * 60)
            logger.info(f"✅ Setup completed successfully! ({self.success_count}/{self.total_steps} steps)")
            logger.info("🎉 Your HireWise development environment is ready!")
            logger.info("\nNext steps:")
            logger.info("1. Start Redis: redis-server")
            logger.info("2. Start Celery worker: celery -A hirewise worker --loglevel=info")
            logger.info("3. Start Django server: python manage.py runserver")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {str(e)}")
            sys.exit(1)
    
    def create_directories(self):
        """Create necessary directories"""
        logger.info("📁 Creating necessary directories...")
        
        directories = [
            'logs',
            'media',
            'media/resumes',
            'media/pdf',
            'media/temp',
            'static',
            'staticfiles',
            'matcher/models'
        ]
        
        for directory in directories:
            dir_path = self.base_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"   ✓ Created {directory}")
        
        self.success_count += 1
        logger.info("✅ Directories created successfully")
    
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        logger.info("🔍 Checking dependencies...")
        
        required_packages = [
            'django',
            'rest_framework',
            'celery',
            'redis',
            'channels',
            'psycopg',
            'google.generativeai'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.info(f"   ✓ {package}")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"   ❌ {package} - MISSING")
        
        if missing_packages:
            logger.error(f"Missing packages: {', '.join(missing_packages)}")
            logger.error("Please install missing packages with: pip install -r requirements.txt")
            raise Exception("Missing required dependencies")
        
        self.success_count += 1
        logger.info("✅ All dependencies are installed")
    
    def setup_database(self):
        """Setup database and run migrations"""
        logger.info("🗄️  Setting up database...")
        
        try:
            # Check database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            logger.info("   ✓ Database connection successful")
            
            # Run migrations
            logger.info("   📋 Running database migrations...")
            execute_from_command_line(['manage.py', 'migrate', '--verbosity=1'])
            logger.info("   ✓ Database migrations completed")
            
            # Create initial data if needed
            self._create_initial_data()
            
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise
        
        self.success_count += 1
        logger.info("✅ Database setup completed")
    
    def _create_initial_data(self):
        """Create initial data for development"""
        logger.info("   📊 Creating initial development data...")
        
        try:
            # Import here to avoid circular imports
            from matcher.models import User, NotificationTemplate
            
            # Create notification templates if they don't exist
            templates = [
                {
                    'name': 'job_match_found',
                    'subject': 'New Job Match Found!',
                    'body': 'We found a job that matches your profile: {job_title} at {company_name}',
                    'notification_type': 'job_match'
                },
                {
                    'name': 'application_received',
                    'subject': 'Application Received',
                    'body': 'Your application for {job_title} has been received and is under review.',
                    'notification_type': 'application'
                },
                {
                    'name': 'interview_scheduled',
                    'subject': 'Interview Scheduled',
                    'body': 'Your interview for {job_title} has been scheduled for {interview_date}.',
                    'notification_type': 'interview'
                }
            ]
            
            for template_data in templates:
                template, created = NotificationTemplate.objects.get_or_create(
                    name=template_data['name'],
                    defaults=template_data
                )
                if created:
                    logger.info(f"   ✓ Created notification template: {template_data['name']}")
            
        except Exception as e:
            logger.warning(f"   ⚠️  Could not create initial data: {str(e)}")
    
    def verify_redis(self):
        """Verify Redis connection and configuration"""
        logger.info("🔴 Verifying Redis connection...")
        
        try:
            # Test Django cache (Redis)
            test_key = 'dev_setup_test'
            test_value = 'test_value_123'
            
            cache.set(test_key, test_value, 30)
            retrieved_value = cache.get(test_key)
            
            if retrieved_value != test_value:
                raise Exception("Redis cache test failed")
            
            cache.delete(test_key)
            logger.info("   ✓ Django cache (Redis) working correctly")
            
            # Test direct Redis connection
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None
            )
            
            redis_client.ping()
            logger.info("   ✓ Direct Redis connection successful")
            
            # Test Redis info
            info = redis_client.info()
            logger.info(f"   ✓ Redis version: {info.get('redis_version', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Redis verification failed: {str(e)}")
            logger.error("Please ensure Redis is running: redis-server")
            raise
        
        self.success_count += 1
        logger.info("✅ Redis verification completed")
    
    def setup_celery(self):
        """Setup and verify Celery configuration"""
        logger.info("🌿 Setting up Celery...")
        
        try:
            # Import Celery app
            from hirewise.celery import app as celery_app
            
            # Check Celery configuration
            logger.info("   ✓ Celery app imported successfully")
            logger.info(f"   ✓ Broker URL: {celery_app.conf.broker_url}")
            logger.info(f"   ✓ Result backend: {celery_app.conf.result_backend}")
            
            # Test Celery broker connection
            try:
                inspect = celery_app.control.inspect()
                # This will raise an exception if broker is not available
                stats = inspect.stats()
                if stats:
                    logger.info("   ✓ Celery broker connection successful")
                else:
                    logger.info("   ⚠️  No Celery workers running (this is normal for setup)")
            except Exception as e:
                logger.warning(f"   ⚠️  Celery broker connection test: {str(e)}")
                logger.warning("   This is normal if Celery worker is not running yet")
            
            # Create Celery management commands
            self._create_celery_scripts()
            
        except Exception as e:
            logger.error(f"Celery setup failed: {str(e)}")
            raise
        
        self.success_count += 1
        logger.info("✅ Celery setup completed")
    
    def _create_celery_scripts(self):
        """Create helper scripts for Celery management"""
        scripts_dir = self.base_dir / 'scripts'
        scripts_dir.mkdir(exist_ok=True)
        
        # Celery worker script
        worker_script = scripts_dir / 'start_celery_worker.sh'
        worker_script.write_text("""#!/bin/bash
# Start Celery worker for HireWise
echo "Starting Celery worker..."
celery -A hirewise worker --loglevel=info --concurrency=2
""")
        worker_script.chmod(0o755)
        
        # Celery beat script
        beat_script = scripts_dir / 'start_celery_beat.sh'
        beat_script.write_text("""#!/bin/bash
# Start Celery beat scheduler for HireWise
echo "Starting Celery beat scheduler..."
celery -A hirewise beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
""")
        beat_script.chmod(0o755)
        
        logger.info("   ✓ Created Celery management scripts")
    
    def setup_logging(self):
        """Setup logging infrastructure"""
        logger.info("📝 Setting up logging infrastructure...")
        
        try:
            # Create log files
            logs_dir = self.base_dir / 'logs'
            log_files = ['django.log', 'errors.log', 'security.log']
            
            for log_file in log_files:
                log_path = logs_dir / log_file
                if not log_path.exists():
                    log_path.touch()
                    logger.info(f"   ✓ Created log file: {log_file}")
            
            # Test logging configuration
            from matcher.logging_config import ai_logger, api_logger, security_logger
            
            # Test each logger
            ai_logger.logger.info("AI logger test - setup completed")
            api_logger.logger.info("API logger test - setup completed")
            security_logger.logger.info("Security logger test - setup completed")
            
            logger.info("   ✓ Logging configuration verified")
            
        except Exception as e:
            logger.error(f"Logging setup failed: {str(e)}")
            raise
        
        self.success_count += 1
        logger.info("✅ Logging infrastructure setup completed")
    
    def run_health_checks(self):
        """Run system health checks"""
        logger.info("🏥 Running health checks...")
        
        try:
            from matcher.health_views import DetailedHealthCheckView
            from django.test import RequestFactory
            
            # Create a mock request
            factory = RequestFactory()
            request = factory.get('/health/')
            
            # Run health check
            health_view = DetailedHealthCheckView()
            response = health_view.get(request)
            
            if response.status_code == 200:
                logger.info("   ✓ All health checks passed")
            else:
                logger.warning(f"   ⚠️  Some health checks failed (status: {response.status_code})")
                # This is not critical for development setup
            
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            # Don't fail the setup for health check issues
        
        self.success_count += 1
        logger.info("✅ Health checks completed")
    
    def create_superuser(self):
        """Create superuser for development"""
        logger.info("👤 Setting up superuser...")
        
        try:
            from matcher.models import User
            
            # Check if superuser already exists
            if User.objects.filter(is_superuser=True).exists():
                logger.info("   ✓ Superuser already exists")
            else:
                logger.info("   📝 Creating development superuser...")
                logger.info("   Username: admin")
                logger.info("   Email: admin@hirewise.dev")
                logger.info("   Password: admin123")
                
                User.objects.create_superuser(
                    username='admin',
                    email='admin@hirewise.dev',
                    password='admin123',
                    user_type='admin'
                )
                logger.info("   ✓ Development superuser created")
            
        except Exception as e:
            logger.warning(f"Superuser creation failed: {str(e)}")
            # Don't fail setup for this
        
        self.success_count += 1
        logger.info("✅ Superuser setup completed")


def main():
    """Main setup function"""
    setup = DevEnvironmentSetup()
    setup.run_setup()


if __name__ == '__main__':
    main()