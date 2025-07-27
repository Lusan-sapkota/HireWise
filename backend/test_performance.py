"""
Performance tests and benchmarks for HireWise backend optimization.
Tests caching, database queries, file operations, and API response times.
"""

import time
import statistics
import logging
from typing import Dict, List, Any, Callable
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from django.test import TestCase, TransactionTestCase, override_settings
from django.core.cache import cache
from django.db import connection, transaction
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from matcher.models import (
    JobPost, Application, Resume, JobSeekerProfile, RecruiterProfile,
    Skill, UserSkill, AIAnalysisResult
)
from matcher.cache_utils import (
    cache_manager, JobCacheManager, UserCacheManager, AICacheManager
)
from matcher.query_optimization import OptimizedQueryManager, DatabaseOptimizer
from matcher.api_cache import APICacheManager, api_cache
from matcher.file_optimization import FileOptimizer, FileUploadManager
from matcher.pagination_optimization import (
    OptimizedPageNumberPagination, OptimizedPaginator, InfiniteScrollPagination
)

User = get_user_model()
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """
    Base class for performance benchmarking utilities.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.results = []
    
    def time_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Time function execution and return results.
        """
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        execution_time = end_time - start_time
        self.results.append(execution_time)
        
        return {
            'result': result,
            'execution_time': execution_time,
            'timestamp': datetime.now()
        }
    
    def run_benchmark(self, func: Callable, iterations: int = 10, *args, **kwargs) -> Dict[str, Any]:
        """
        Run benchmark multiple times and return statistics.
        """
        self.results = []
        
        for i in range(iterations):
            self.time_function(func, *args, **kwargs)
        
        return self.get_statistics()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate statistics from benchmark results.
        """
        if not self.results:
            return {}
        
        return {
            'name': self.name,
            'iterations': len(self.results),
            'min_time': min(self.results),
            'max_time': max(self.results),
            'avg_time': statistics.mean(self.results),
            'median_time': statistics.median(self.results),
            'std_dev': statistics.stdev(self.results) if len(self.results) > 1 else 0,
            'total_time': sum(self.results),
        }


class CachePerformanceTests(TestCase):
    """
    Test cache performance and functionality.
    """
    
    def setUp(self):
        cache.clear()
        self.benchmark = PerformanceBenchmark("Cache Performance")
    
    def test_cache_set_performance(self):
        """
        Test cache set operation performance.
        """
        def cache_set_operation():
            for i in range(100):
                cache.set(f'test_key_{i}', f'test_value_{i}', 300)
        
        stats = self.benchmark.run_benchmark(cache_set_operation, iterations=5)
        
        # Assert performance requirements
        self.assertLess(stats['avg_time'], 0.1, "Cache set operations too slow")
        logger.info(f"Cache Set Performance: {stats}")
    
    def test_cache_get_performance(self):
        """
        Test cache get operation performance.
        """
        # Pre-populate cache
        for i in range(100):
            cache.set(f'test_key_{i}', f'test_value_{i}', 300)
        
        def cache_get_operation():
            for i in range(100):
                cache.get(f'test_key_{i}')
        
        stats = self.benchmark.run_benchmark(cache_get_operation, iterations=10)
        
        self.assertLess(stats['avg_time'], 0.05, "Cache get operations too slow")
        logger.info(f"Cache Get Performance: {stats}")
    
    def test_cache_manager_performance(self):
        """
        Test cache manager performance.
        """
        def cache_manager_operations():
            for i in range(50):
                cache_manager.set('test_prefix', f'value_{i}', 300, f'key_{i}')
                cache_manager.get('test_prefix', f'key_{i}')
        
        stats = self.benchmark.run_benchmark(cache_manager_operations, iterations=5)
        
        self.assertLess(stats['avg_time'], 0.2, "Cache manager operations too slow")
        logger.info(f"Cache Manager Performance: {stats}")
    
    def test_job_cache_manager_performance(self):
        """
        Test job-specific cache manager performance.
        """
        filters = {'location': 'remote', 'job_type': 'full_time'}
        test_data = [{'id': i, 'title': f'Job {i}'} for i in range(20)]
        
        def job_cache_operations():
            JobCacheManager.cache_job_list(filters, 1, test_data)
            JobCacheManager.get_cached_job_list(filters, 1)
        
        stats = self.benchmark.run_benchmark(job_cache_operations, iterations=10)
        
        self.assertLess(stats['avg_time'], 0.01, "Job cache operations too slow")
        logger.info(f"Job Cache Manager Performance: {stats}")
    
    def test_cache_invalidation_performance(self):
        """
        Test cache invalidation performance.
        """
        # Pre-populate cache with many keys
        for i in range(100):
            cache.set(f'jobs:list:{i}', f'data_{i}', 300)
            cache.set(f'jobs:detail:{i}', f'detail_{i}', 300)
        
        def cache_invalidation():
            JobCacheManager.invalidate_job_caches()
        
        stats = self.benchmark.run_benchmark(cache_invalidation, iterations=5)
        
        self.assertLess(stats['avg_time'], 0.5, "Cache invalidation too slow")
        logger.info(f"Cache Invalidation Performance: {stats}")


class DatabasePerformanceTests(TransactionTestCase):
    """
    Test database query performance and optimization.
    """
    
    def setUp(self):
        self.benchmark = PerformanceBenchmark("Database Performance")
        self.create_test_data()
    
    def create_test_data(self):
        """
        Create test data for performance testing.
        """
        # Create users
        self.job_seekers = []
        self.recruiters = []
        
        for i in range(50):
            # Job seekers
            job_seeker = User.objects.create_user(
                username=f'jobseeker_{i}',
                email=f'jobseeker_{i}@test.com',
                user_type='job_seeker'
            )
            JobSeekerProfile.objects.create(
                user=job_seeker,
                location=f'City {i % 10}',
                experience_level='mid'
            )
            self.job_seekers.append(job_seeker)
            
            # Recruiters (fewer than job seekers)
            if i < 10:
                recruiter = User.objects.create_user(
                    username=f'recruiter_{i}',
                    email=f'recruiter_{i}@test.com',
                    user_type='recruiter'
                )
                RecruiterProfile.objects.create(
                    user=recruiter,
                    company_name=f'Company {i}'
                )
                self.recruiters.append(recruiter)
        
        # Create job posts
        self.job_posts = []
        for i in range(100):
            recruiter = self.recruiters[i % len(self.recruiters)]
            job_post = JobPost.objects.create(
                recruiter=recruiter,
                title=f'Job Title {i}',
                description=f'Job description {i}',
                location=f'Location {i % 20}',
                job_type='full_time',
                experience_level='mid',
                skills_required='Python,Django,React'
            )
            self.job_posts.append(job_post)
        
        # Create applications
        for i in range(200):
            job_seeker = self.job_seekers[i % len(self.job_seekers)]
            job_post = self.job_posts[i % len(self.job_posts)]
            
            # Create resume first
            resume = Resume.objects.create(
                job_seeker=job_seeker,
                file='test_resume.pdf',
                original_filename='test_resume.pdf'
            )
            
            Application.objects.create(
                job_seeker=job_seeker,
                job_post=job_post,
                resume=resume,
                status='pending'
            )
    
    def test_optimized_job_list_performance(self):
        """
        Test optimized job list query performance.
        """
        def get_optimized_job_list():
            return OptimizedQueryManager.get_optimized_job_list(
                filters={'location': 'Location 1'},
                page=1,
                page_size=20
            )
        
        stats = self.benchmark.run_benchmark(get_optimized_job_list, iterations=10)
        
        self.assertLess(stats['avg_time'], 0.1, "Optimized job list query too slow")
        logger.info(f"Optimized Job List Performance: {stats}")
    
    def test_user_applications_performance(self):
        """
        Test user applications query performance.
        """
        user_id = str(self.job_seekers[0].id)
        
        def get_user_applications():
            return OptimizedQueryManager.get_optimized_user_applications(
                user_id=user_id,
                page=1,
                page_size=20
            )
        
        stats = self.benchmark.run_benchmark(get_user_applications, iterations=10)
        
        self.assertLess(stats['avg_time'], 0.05, "User applications query too slow")
        logger.info(f"User Applications Performance: {stats}")
    
    def test_dashboard_data_performance(self):
        """
        Test dashboard data query performance.
        """
        user_id = str(self.job_seekers[0].id)
        
        def get_dashboard_data():
            return OptimizedQueryManager.get_user_dashboard_data(user_id, 'job_seeker')
        
        stats = self.benchmark.run_benchmark(get_dashboard_data, iterations=10)
        
        self.assertLess(stats['avg_time'], 0.1, "Dashboard data query too slow")
        logger.info(f"Dashboard Data Performance: {stats}")
    
    def test_query_count_optimization(self):
        """
        Test that optimized queries use minimal database queries.
        """
        initial_query_count = len(connection.queries)
        
        # Test optimized job list
        OptimizedQueryManager.get_optimized_job_list(page_size=20)
        
        query_count = len(connection.queries) - initial_query_count
        
        # Should use minimal queries (ideally 1-2)
        self.assertLessEqual(query_count, 3, f"Too many queries used: {query_count}")
        logger.info(f"Query count for optimized job list: {query_count}")
    
    def test_bulk_operations_performance(self):
        """
        Test bulk database operations performance.
        """
        # Test bulk create
        def bulk_create_skills():
            skills = [
                Skill(name=f'Skill {i}', category='technical')
                for i in range(100)
            ]
            return DatabaseOptimizer.bulk_create_optimized(Skill, skills)
        
        stats = self.benchmark.run_benchmark(bulk_create_skills, iterations=3)
        
        self.assertLess(stats['avg_time'], 0.1, "Bulk create too slow")
        logger.info(f"Bulk Create Performance: {stats}")


class APIPerformanceTests(APITestCase):
    """
    Test API endpoint performance with caching.
    """
    
    def setUp(self):
        self.client = APIClient()
        self.benchmark = PerformanceBenchmark("API Performance")
        self.create_test_user()
        cache.clear()
    
    def create_test_user(self):
        """
        Create test user and authenticate.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='job_seeker'
        )
        JobSeekerProfile.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)
    
    def test_job_list_api_performance(self):
        """
        Test job list API performance with and without caching.
        """
        # Create test jobs
        recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@test.com',
            user_type='recruiter'
        )
        RecruiterProfile.objects.create(user=recruiter, company_name='Test Company')
        
        for i in range(50):
            JobPost.objects.create(
                recruiter=recruiter,
                title=f'Job {i}',
                description='Test description',
                location='Test Location',
                job_type='full_time',
                experience_level='mid'
            )
        
        def api_request():
            return self.client.get('/api/jobs/')
        
        # Test without cache
        stats_no_cache = self.benchmark.run_benchmark(api_request, iterations=5)
        
        # Clear results and test with cache
        self.benchmark.results = []
        
        # First request to populate cache
        self.client.get('/api/jobs/')
        
        # Test with cache
        stats_with_cache = self.benchmark.run_benchmark(api_request, iterations=10)
        
        # Cache should improve performance
        self.assertLess(
            stats_with_cache['avg_time'],
            stats_no_cache['avg_time'],
            "Caching should improve performance"
        )
        
        logger.info(f"API Performance without cache: {stats_no_cache}")
        logger.info(f"API Performance with cache: {stats_with_cache}")
    
    def test_concurrent_api_requests(self):
        """
        Test API performance under concurrent load.
        """
        def make_request():
            return self.client.get('/api/jobs/')
        
        # Test concurrent requests
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # All requests should succeed
        self.assertEqual(len(results), 50)
        for response in results:
            self.assertEqual(response.status_code, 200)
        
        # Should handle concurrent requests efficiently
        self.assertLess(total_time, 5.0, "Concurrent requests too slow")
        
        logger.info(f"Concurrent API Performance: {total_time:.3f}s for 50 requests")


class FileOptimizationPerformanceTests(TestCase):
    """
    Test file optimization performance.
    """
    
    def setUp(self):
        self.benchmark = PerformanceBenchmark("File Optimization Performance")
        self.optimizer = FileOptimizer()
        self.upload_manager = FileUploadManager()
    
    def create_test_file(self, size_kb: int = 100) -> SimpleUploadedFile:
        """
        Create test file for performance testing.
        """
        content = b'x' * (size_kb * 1024)  # Create file of specified size
        return SimpleUploadedFile(
            name='test_file.txt',
            content=content,
            content_type='text/plain'
        )
    
    def test_file_optimization_performance(self):
        """
        Test file optimization performance for different file sizes.
        """
        file_sizes = [10, 50, 100, 500]  # KB
        
        for size_kb in file_sizes:
            test_file = self.create_test_file(size_kb)
            
            def optimize_file():
                return self.optimizer.optimize_file(test_file)
            
            stats = self.benchmark.run_benchmark(optimize_file, iterations=3)
            
            # Performance should scale reasonably with file size
            expected_max_time = size_kb * 0.001  # 1ms per KB
            self.assertLess(
                stats['avg_time'],
                max(expected_max_time, 0.1),
                f"File optimization too slow for {size_kb}KB file"
            )
            
            logger.info(f"File Optimization Performance ({size_kb}KB): {stats}")
    
    def test_file_upload_processing_performance(self):
        """
        Test complete file upload processing performance.
        """
        test_file = self.create_test_file(100)
        
        def process_upload():
            return self.upload_manager.process_upload(
                test_file, 'test_user_id', 'resume'
            )
        
        stats = self.benchmark.run_benchmark(process_upload, iterations=5)
        
        self.assertLess(stats['avg_time'], 0.5, "File upload processing too slow")
        logger.info(f"File Upload Processing Performance: {stats}")


class PaginationPerformanceTests(TestCase):
    """
    Test pagination performance and optimization.
    """
    
    def setUp(self):
        self.benchmark = PerformanceBenchmark("Pagination Performance")
        self.create_large_dataset()
    
    def create_large_dataset(self):
        """
        Create large dataset for pagination testing.
        """
        # Create users and job posts
        recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@test.com',
            user_type='recruiter'
        )
        RecruiterProfile.objects.create(user=recruiter, company_name='Test Company')
        
        # Create many job posts
        job_posts = []
        for i in range(1000):
            job_post = JobPost(
                recruiter=recruiter,
                title=f'Job {i}',
                description=f'Description {i}',
                location=f'Location {i % 50}',
                job_type='full_time',
                experience_level='mid'
            )
            job_posts.append(job_post)
        
        JobPost.objects.bulk_create(job_posts)
    
    def test_optimized_pagination_performance(self):
        """
        Test optimized pagination performance.
        """
        queryset = JobPost.objects.filter(is_active=True)
        
        def paginate_with_optimization():
            paginator = OptimizedPaginator(queryset, 20)
            return paginator.page(1)
        
        stats = self.benchmark.run_benchmark(paginate_with_optimization, iterations=10)
        
        self.assertLess(stats['avg_time'], 0.1, "Optimized pagination too slow")
        logger.info(f"Optimized Pagination Performance: {stats}")
    
    def test_infinite_scroll_performance(self):
        """
        Test infinite scroll pagination performance.
        """
        queryset = JobPost.objects.filter(is_active=True)
        paginator = InfiniteScrollPagination(page_size=20)
        
        def infinite_scroll_pagination():
            return paginator.paginate_for_infinite_scroll(queryset)
        
        stats = self.benchmark.run_benchmark(infinite_scroll_pagination, iterations=10)
        
        self.assertLess(stats['avg_time'], 0.05, "Infinite scroll pagination too slow")
        logger.info(f"Infinite Scroll Performance: {stats}")
    
    def test_pagination_with_different_page_sizes(self):
        """
        Test pagination performance with different page sizes.
        """
        queryset = JobPost.objects.filter(is_active=True)
        page_sizes = [10, 20, 50, 100]
        
        for page_size in page_sizes:
            def paginate_with_size():
                paginator = OptimizedPaginator(queryset, page_size)
                return paginator.page(1)
            
            stats = self.benchmark.run_benchmark(paginate_with_size, iterations=5)
            
            # Performance should not degrade significantly with larger page sizes
            self.assertLess(
                stats['avg_time'],
                0.2,
                f"Pagination too slow for page size {page_size}"
            )
            
            logger.info(f"Pagination Performance (page_size={page_size}): {stats}")


class OverallPerformanceBenchmark(TestCase):
    """
    Overall system performance benchmark.
    """
    
    def setUp(self):
        self.benchmark = PerformanceBenchmark("Overall Performance")
    
    def test_system_performance_benchmark(self):
        """
        Run comprehensive system performance benchmark.
        """
        results = {}
        
        # Cache performance
        cache_benchmark = PerformanceBenchmark("Cache")
        cache_stats = cache_benchmark.run_benchmark(
            lambda: cache.set('test', 'value', 300),
            iterations=100
        )
        results['cache'] = cache_stats
        
        # Database performance
        db_benchmark = PerformanceBenchmark("Database")
        db_stats = db_benchmark.run_benchmark(
            lambda: User.objects.count(),
            iterations=50
        )
        results['database'] = db_stats
        
        # Log overall results
        logger.info("=== PERFORMANCE BENCHMARK RESULTS ===")
        for component, stats in results.items():
            logger.info(f"{component.upper()}: avg={stats['avg_time']:.4f}s, "
                       f"min={stats['min_time']:.4f}s, max={stats['max_time']:.4f}s")
        
        # Assert overall performance requirements
        self.assertLess(cache_stats['avg_time'], 0.001, "Cache performance below threshold")
        self.assertLess(db_stats['avg_time'], 0.01, "Database performance below threshold")


# Utility functions for running benchmarks

def run_performance_tests():
    """
    Run all performance tests and generate report.
    """
    import subprocess
    import sys
    
    # Run performance tests
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'test_performance.py', 
        '-v', 
        '--tb=short'
    ], capture_output=True, text=True)
    
    print("Performance Test Results:")
    print(result.stdout)
    
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    return result.returncode == 0


def generate_performance_report():
    """
    Generate comprehensive performance report.
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'system_info': {
            'python_version': sys.version,
            'django_version': '5.2.4',
        },
        'test_results': {},
        'recommendations': []
    }
    
    # This would be populated by actual test runs
    return report


if __name__ == '__main__':
    # Run performance tests when script is executed directly
    success = run_performance_tests()
    if success:
        print("All performance tests passed!")
    else:
        print("Some performance tests failed!")
        sys.exit(1)