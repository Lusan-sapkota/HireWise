"""
Django management command for validating configuration and startup checks
Usage: python manage.py validate_config
"""

import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import redis
import google.generativeai as genai
import joblib

class Command(BaseCommand):
    help = 'Validate system configuration and perform startup checks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Fail on warnings (treat warnings as errors)'
        )
        parser.add_argument(
            '--skip-external',
            action='store_true',
            help='Skip external service checks (Gemini API, etc.)'
        )

    def handle(self, *args, **options):
        self.strict_mode = options['strict']
        self.skip_external = options['skip_external']
        
        self.stdout.write('Starting configuration validation...\n')
        
        errors = []
        warnings = []
        
        # Core Django settings validation
        core_errors, core_warnings = self._validate_core_settings()
        errors.extend(core_errors)
        warnings.extend(core_warnings)
        
        # Database validation
        db_errors, db_warnings = self._validate_database()
        errors.extend(db_errors)
        warnings.extend(db_warnings)
        
        # Redis validation
        redis_errors, redis_warnings = self._validate_redis()
        errors.extend(redis_errors)
        warnings.extend(redis_warnings)
        
        # File system validation
        fs_errors, fs_warnings = self._validate_file_system()
        errors.extend(fs_errors)
        warnings.extend(fs_warnings)
        
        # External services validation
        if not self.skip_external:
            ext_errors, ext_warnings = self._validate_external_services()
            errors.extend(ext_errors)
            warnings.extend(ext_warnings)
        
        # Security validation
        sec_errors, sec_warnings = self._validate_security_settings()
        errors.extend(sec_errors)
        warnings.extend(sec_warnings)
        
        # Environment-specific validation
        env_errors, env_warnings = self._validate_environment_settings()
        errors.extend(env_errors)
        warnings.extend(env_warnings)
        
        # Report results
        self._report_results(errors, warnings)
        
        # Exit with appropriate code
        if errors or (self.strict_mode and warnings):
            sys.exit(1)
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✅ Configuration validation passed!')
            )

    def _validate_core_settings(self):
        """Validate core Django settings"""
        errors = []
        warnings = []
        
        self.stdout.write('🔍 Validating core Django settings...')
        
        # SECRET_KEY validation
        secret_key = getattr(settings, 'SECRET_KEY', '')
        if not secret_key:
            errors.append('SECRET_KEY is not set')
        elif secret_key == 'django-insecure-fallback-key':
            warnings.append('SECRET_KEY is using default fallback value')
        elif len(secret_key) < 50:
            warnings.append('SECRET_KEY should be at least 50 characters long')
        
        # DEBUG validation
        debug = getattr(settings, 'DEBUG', True)
        environment = os.getenv('ENVIRONMENT', 'development')
        if debug and environment == 'production':
            errors.append('DEBUG should be False in production')
        
        # ALLOWED_HOSTS validation
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if not allowed_hosts and not debug:
            errors.append('ALLOWED_HOSTS must be set when DEBUG=False')
        
        # Database configuration
        databases = getattr(settings, 'DATABASES', {})
        if not databases or 'default' not in databases:
            errors.append('Database configuration is missing')
        
        return errors, warnings

    def _validate_database(self):
        """Validate database connectivity and configuration"""
        errors = []
        warnings = []
        
        self.stdout.write('🔍 Validating database configuration...')
        
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Check database engine
            db_engine = settings.DATABASES['default']['ENGINE']
            if 'sqlite3' in db_engine:
                environment = os.getenv('ENVIRONMENT', 'development')
                if environment == 'production':
                    warnings.append('SQLite is not recommended for production use')
            
        except Exception as e:
            errors.append(f'Database connection failed: {str(e)}')
        
        return errors, warnings

    def _validate_redis(self):
        """Validate Redis connectivity and configuration"""
        errors = []
        warnings = []
        
        self.stdout.write('🔍 Validating Redis configuration...')
        
        try:
            # Test cache connection
            cache.set('config_test', 'test_value', 10)
            value = cache.get('config_test')
            if value != 'test_value':
                errors.append('Redis cache test failed')
            cache.delete('config_test')
            
            # Test Redis connection directly
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            redis_password = getattr(settings, 'REDIS_PASSWORD', '')
            
            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password if redis_password else None,
                decode_responses=True
            )
            r.ping()
            
        except Exception as e:
            errors.append(f'Redis connection failed: {str(e)}')
        
        return errors, warnings

    def _validate_file_system(self):
        """Validate file system permissions and directories"""
        errors = []
        warnings = []
        
        self.stdout.write('🔍 Validating file system configuration...')
        
        # Check media directory
        media_root = getattr(settings, 'MEDIA_ROOT', '')
        if not media_root:
            errors.append('MEDIA_ROOT is not configured')
        else:
            try:
                os.makedirs(media_root, exist_ok=True)
                # Test write permission
                test_file = os.path.join(media_root, 'config_test.txt')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                errors.append(f'Media directory not writable: {str(e)}')
        
        # Check static directory
        static_root = getattr(settings, 'STATIC_ROOT', '')
        if static_root:
            try:
                os.makedirs(static_root, exist_ok=True)
            except Exception as e:
                warnings.append(f'Static directory creation failed: {str(e)}')
        
        # Check logs directory
        log_file = getattr(settings, 'LOGGING', {}).get('handlers', {}).get('file', {}).get('filename', '')
        if log_file:
            log_dir = os.path.dirname(log_file)
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception as e:
                errors.append(f'Log directory not accessible: {str(e)}')
        
        return errors, warnings

    def _validate_external_services(self):
        """Validate external service configurations"""
        errors = []
        warnings = []
        
        self.stdout.write('🔍 Validating external services...')
        
        # Gemini API validation
        gemini_api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not gemini_api_key:
            warnings.append('GEMINI_API_KEY is not configured')
        else:
            try:
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-pro')
                # Test with minimal request
                response = model.generate_content(
                    "Test",
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=5,
                        temperature=0.1
                    )
                )
                if not response.text:
                    warnings.append('Gemini API test returned empty response')
            except Exception as e:
                warnings.append(f'Gemini API test failed: {str(e)}')
        
        # ML Model validation
        ml_model_path = getattr(settings, 'ML_MODEL_PATH', '')
        if not ml_model_path:
            warnings.append('ML_MODEL_PATH is not configured')
        else:
            full_path = os.path.join(settings.BASE_DIR, ml_model_path)
            if not os.path.exists(full_path):
                warnings.append(f'ML model file not found: {full_path}')
            else:
                try:
                    joblib.load(full_path)
                except Exception as e:
                    warnings.append(f'ML model loading failed: {str(e)}')
        
        return errors, warnings

    def _validate_security_settings(self):
        """Validate security-related settings"""
        errors = []
        warnings = []
        
        self.stdout.write('🔍 Validating security settings...')
        
        environment = os.getenv('ENVIRONMENT', 'development')
        
        if environment == 'production':
            # HTTPS settings
            if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
                warnings.append('SECURE_SSL_REDIRECT should be True in production')
            
            if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
                warnings.append('SESSION_COOKIE_SECURE should be True in production')
            
            if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
                warnings.append('CSRF_COOKIE_SECURE should be True in production')
        
        # JWT settings validation
        jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
        access_lifetime = jwt_settings.get('ACCESS_TOKEN_LIFETIME')
        if access_lifetime and access_lifetime.total_seconds() > 3600:  # 1 hour
            warnings.append('JWT access token lifetime is longer than recommended (1 hour)')
        
        # CORS settings
        cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        if '*' in cors_origins or 'http://localhost:3000' in cors_origins:
            if environment == 'production':
                warnings.append('CORS configuration may be too permissive for production')
        
        return errors, warnings

    def _validate_environment_settings(self):
        """Validate environment-specific settings"""
        errors = []
        warnings = []
        
        self.stdout.write('🔍 Validating environment settings...')
        
        environment = os.getenv('ENVIRONMENT', 'development')
        
        # Required environment variables
        required_vars = [
            'SECRET_KEY',
            'DB_ENGINE',
            'REDIS_HOST',
        ]
        
        if environment == 'production':
            required_vars.extend([
                'DB_PASSWORD',
                'EMAIL_HOST_USER',
                'EMAIL_HOST_PASSWORD',
                'ALLOWED_HOSTS',
            ])
        
        for var in required_vars:
            if not os.getenv(var):
                errors.append(f'Required environment variable {var} is not set')
        
        # Email configuration
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        if 'console' in email_backend and environment == 'production':
            warnings.append('Email backend is set to console in production')
        
        return errors, warnings

    def _report_results(self, errors, warnings):
        """Report validation results"""
        if errors:
            self.stdout.write('\n❌ Configuration Errors:')
            for error in errors:
                self.stdout.write(f'  • {error}', self.style.ERROR)
        
        if warnings:
            self.stdout.write('\n⚠️  Configuration Warnings:')
            for warning in warnings:
                self.stdout.write(f'  • {warning}', self.style.WARNING)
        
        if not errors and not warnings:
            self.stdout.write('\n✅ No configuration issues found!')
        
        # Summary
        self.stdout.write(f'\nSummary: {len(errors)} errors, {len(warnings)} warnings')
        
        if errors:
            self.stdout.write(
                '\n❌ Configuration validation failed! Please fix the errors above.',
                self.style.ERROR
            )
        elif warnings and self.strict_mode:
            self.stdout.write(
                '\n⚠️  Configuration validation failed in strict mode due to warnings.',
                self.style.WARNING
            )
        elif warnings:
            self.stdout.write(
                '\n⚠️  Configuration validation passed with warnings.',
                self.style.WARNING
            )