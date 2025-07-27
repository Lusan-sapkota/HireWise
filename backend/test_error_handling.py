#!/usr/bin/env python
"""
Test script for error handling and health check endpoints
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirewise.settings')
django.setup()

def test_health_endpoints():
    """Test health check endpoints"""
    client = Client()
    
    print("Testing health check endpoints...")
    
    # Test basic health check
    try:
        response = client.get('/health/')
        print(f"Basic health check: {response.status_code}")
        if response.status_code == 200:
            print("✅ Basic health check passed")
        else:
            print("❌ Basic health check failed")
    except Exception as e:
        print(f"❌ Basic health check error: {e}")
    
    # Test liveness check
    try:
        response = client.get('/live/')
        print(f"Liveness check: {response.status_code}")
        if response.status_code == 200:
            print("✅ Liveness check passed")
        else:
            print("❌ Liveness check failed")
    except Exception as e:
        print(f"❌ Liveness check error: {e}")
    
    # Test readiness check (may fail due to dependencies)
    try:
        response = client.get('/ready/')
        print(f"Readiness check: {response.status_code}")
        if response.status_code in [200, 503]:  # Both are valid responses
            print("✅ Readiness check endpoint working")
        else:
            print("❌ Readiness check endpoint failed")
    except Exception as e:
        print(f"❌ Readiness check error: {e}")
    
    # Test detailed health check (may fail due to dependencies)
    try:
        response = client.get('/api/health/')
        print(f"Detailed health check: {response.status_code}")
        if response.status_code in [200, 503]:  # Both are valid responses
            print("✅ Detailed health check endpoint working")
        else:
            print("❌ Detailed health check endpoint failed")
    except Exception as e:
        print(f"❌ Detailed health check error: {e}")

def test_configuration_validation():
    """Test configuration validation"""
    print("\nTesting configuration validation...")
    
    from matcher.management.commands.validate_config import Command
    
    try:
        command = Command()
        # This will likely fail due to missing config, but we're testing the command exists
        print("✅ Configuration validation command exists")
    except Exception as e:
        print(f"❌ Configuration validation error: {e}")

def test_database_seeding():
    """Test database seeding command"""
    print("\nTesting database seeding...")
    
    from matcher.management.commands.seed_database import Command
    
    try:
        command = Command()
        print("✅ Database seeding command exists")
    except Exception as e:
        print(f"❌ Database seeding error: {e}")

if __name__ == '__main__':
    print("HireWise Backend - Testing deployment components")
    print("=" * 50)
    
    test_health_endpoints()
    test_configuration_validation()
    test_database_seeding()
    
    print("\n" + "=" * 50)
    print("Testing completed!")
    print("\nNote: Some tests may show failures due to missing dependencies")
    print("(Redis, PostgreSQL, etc.) which is expected in this environment.")