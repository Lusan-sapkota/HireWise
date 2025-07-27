#!/usr/bin/env python
"""
Test script to verify Celery setup and background task functionality.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirewise.settings')
django.setup()

def test_celery_configuration():
    """Test Celery configuration."""
    print("Testing Celery configuration...")
    
    try:
        from hirewise.celery import app
        print(f"✓ Celery app loaded: {app.main}")
        print(f"✓ Broker URL: {app.conf.broker_url}")
        print(f"✓ Result backend: {app.conf.result_backend}")
        print(f"✓ Task serializer: {app.conf.task_serializer}")
        print(f"✓ Result serializer: {app.conf.result_serializer}")
        return True
    except Exception as e:
        print(f"✗ Celery configuration error: {e}")
        return False


def test_redis_connection():
    """Test Redis connection."""
    print("\nTesting Redis connection...")
    
    try:
        import redis
        redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        redis_client.ping()
        print("✓ Redis connection successful")
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False


def test_task_imports():
    """Test task imports."""
    print("\nTesting task imports...")
    
    try:
        from matcher.tasks import (
            test_celery_task, parse_resume_task, calculate_match_score_task,
            send_notification_task, health_check_task
        )
        print("✓ All tasks imported successfully")
        return True
    except Exception as e:
        print(f"✗ Task import error: {e}")
        return False


def test_task_monitoring():
    """Test task monitoring utilities."""
    print("\nTesting task monitoring utilities...")
    
    try:
        from matcher.task_monitoring import TaskMonitor, TaskResultTracker
        print("✓ Task monitoring utilities imported successfully")
        return True
    except Exception as e:
        print(f"✗ Task monitoring import error: {e}")
        return False


def test_basic_task_execution():
    """Test basic task execution in eager mode."""
    print("\nTesting basic task execution...")
    
    try:
        # Configure Celery for testing
        from hirewise.celery import app
        app.conf.update(
            task_always_eager=True,
            task_eager_propagates=True,
        )
        
        from matcher.tasks import test_celery_task
        result = test_celery_task.apply()
        
        if result.successful():
            print("✓ Test task executed successfully")
            print(f"  Result: {result.result}")
            return True
        else:
            print(f"✗ Test task failed: {result.result}")
            return False
    except Exception as e:
        print(f"✗ Task execution error: {e}")
        return False


def run_unit_tests():
    """Run Celery-specific unit tests."""
    print("\nRunning Celery unit tests...")
    
    try:
        # Configure test settings
        os.environ['DJANGO_SETTINGS_MODULE'] = 'hirewise.settings'
        
        # Run specific test module
        from django.core.management import execute_from_command_line
        
        test_command = [
            'manage.py',
            'test',
            'matcher.tests_celery_tasks',
            '--verbosity=2',
            '--keepdb'
        ]
        
        execute_from_command_line(test_command)
        return True
    except Exception as e:
        print(f"✗ Unit tests failed: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("CELERY SETUP VERIFICATION")
    print("=" * 60)
    
    tests = [
        test_celery_configuration,
        test_redis_connection,
        test_task_imports,
        test_task_monitoring,
        test_basic_task_execution,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All Celery setup tests passed!")
        
        # Ask if user wants to run unit tests
        response = input("\nRun comprehensive unit tests? (y/n): ")
        if response.lower() in ['y', 'yes']:
            run_unit_tests()
    else:
        print("✗ Some tests failed. Please check the configuration.")
        sys.exit(1)


if __name__ == '__main__':
    main()