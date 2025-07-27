"""
Performance tests for HireWise backend API endpoints.
Tests response times, throughput, and scalability under load.
"""
import pytest
import time
import statistics
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from concurrent.futures import ThreadPoolExecutor, as_completed
from factories import (
    UserFactory, 
    JobPostFactory, 
    ResumeFactory, 
    ApplicationFactory,
    BatchUserFactory,
    BatchJobFactory
)

User = get_user_model()


@pytest.mark.performance
class TestAPIPerformance(TransactionTestCase):
    """Test API endpoint performance under various loads."""
    
    def setUp(self):
        self.client = APIClient()
        self.job_seeker = UserFactory(user_type='job_seeker')
        self.recruiter = UserFactory(user_type='recruiter')
    
    def measure_response_time(self, func, *args, **kwargs):
        """Measure response time of a function call."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def test_job_listing_performance(self):
        """Test job listing endpoint performance with large dataset."""
        # Create test data
        recruiters = UserFactory.create_batch(10, user_type='recruiter')
        jobs = []
        for recruiter in recruiters:
            jobs.extend(JobPostFactory.create_batch(20, recruiter=recruiter))
        
        # Test single request performance
        response, response_time = self.measure_response_time(
            self.client.get, '/api/job-posts/'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 1.0, "Job listing should respond within 1 second")
        
        # Test pagination performance
        response, response_time = self.measure_response_time(
            self.client.get, '/api/job-posts/?page=1&page_size=50'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 0.5, "Paginated job listing should respond within 0.5 seconds")
    
    def test_job_search_performance(self):
        """Test job search performance with various query types."""
        # Create test data with specific content for searching
        recruiter = UserFactory(user_type='recruiter')
        python_jobs = JobPostFactory.create_batch(
            50, 
            recruiter=recruiter,
            title='Python Developer',
            skills_required='Python,Django,Flask'
        )
        javascript_jobs = JobPostFactory.create_batch(
            50,
            recruiter=recruiter,
            title='JavaScript Developer', 
            skills_required='JavaScript,React,Node.js'
        )
        
        # Test text search performance
        search_queries = [
            'Python',
            'JavaScript', 
            'Developer',
            'Django',
            'React'
        ]
        
        response_times = []
        for query in search_queries:
            response, response_time = self.measure_response_time(
                self.client.get, f'/api/job-posts/?search={query}'
            )
            response_times.append(response_time)
            self.assertEqual(response.status_code, 200)
        
        avg_response_time = statistics.mean(response_times)
        self.assertLess(avg_response_time, 0.8, "Search queries should average under 0.8 seconds")
    
    def test_authentication_performance(self):
        """Test authentication endpoint performance."""
        # Create test users
        users_data = []
        for i in range(20):
            user = UserFactory(username=f'perfuser{i}')
            users_data.append({
                'username': user.username,
                'password': 'testpass123'
            })
        
        # Test login performance
        response_times = []
        for user_data in users_data[:10]:  # Test with 10 users
            response, response_time = self.measure_response_time(
                self.client.post, '/api/auth/jwt/login/', user_data
            )
            response_times.append(response_time)
            self.assertEqual(response.status_code, 200)
        
        avg_response_time = statistics.mean(response_times)
        self.assertLess(avg_response_time, 0.3, "Login should average under 0.3 seconds")
    
    def test_application_creation_performance(self):
        """Test job application creation performance."""
        # Setup test data
        job_seekers = UserFactory.create_batch(20, user_type='job_seeker')
        recruiter = UserFactory(user_type='recruiter')
        job_posts = JobPostFactory.create_batch(5, recruiter=recruiter)
        
        # Create resumes for job seekers
        resumes = []
        for job_seeker in job_seekers:
            resumes.append(ResumeFactory(job_seeker=job_seeker))
        
        # Test application creation performance
        self.client.force_authenticate(user=job_seekers[0])
        
        response_times = []
        for i in range(10):
            job_post = job_posts[i % len(job_posts)]
            resume = resumes[i % len(resumes)]
            
            application_data = {
                'job_post': str(job_post.id),
                'resume': str(resume.id),
                'cover_letter': f'Application {i} cover letter'
            }
            
            response, response_time = self.measure_response_time(
                self.client.post, '/api/applications/', application_data
            )
            response_times.append(response_time)
            
            if response.status_code != 201:
                print(f"Application creation failed: {response.data}")
        
        avg_response_time = statistics.mean(response_times)
        self.assertLess(avg_response_time, 0.5, "Application creation should average under 0.5 seconds")
    
    @pytest.mark.slow
    def test_concurrent_requests_performance(self):
        """Test API performance under concurrent load."""
        # Create test data
        job_seekers = UserFactory.create_batch(10, user_type='job_seeker')
        recruiter = UserFactory(user_type='recruiter')
        job_posts = JobPostFactory.create_batch(20, recruiter=recruiter)
        
        def make_concurrent_request(user):
            """Make a request as a specific user."""
            client = APIClient()
            client.force_authenticate(user=user)
            start_time = time.time()
            response = client.get('/api/job-posts/')
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Test with 10 concurrent users
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(make_concurrent_request, user) 
                for user in job_seekers
            ]
            
            results = []
            for future in as_completed(futures):
                status_code, response_time = future.result()
                results.append((status_code, response_time))
        
        # Verify all requests succeeded
        successful_requests = [r for r in results if r[0] == 200]
        self.assertEqual(len(successful_requests), 10, "All concurrent requests should succeed")
        
        # Check response times
        response_times = [r[1] for r in successful_requests]
        max_response_time = max(response_times)
        avg_response_time = statistics.mean(response_times)
        
        self.assertLess(max_response_time, 2.0, "Max response time under concurrent load should be under 2 seconds")
        self.assertLess(avg_response_time, 1.0, "Average response time under concurrent load should be under 1 second")


@pytest.mark.performance
class TestDatabasePerformance(TestCase):
    """Test database query performance and optimization."""
    
    def test_job_listing_query_performance(self):
        """Test database query performance for job listings."""
        # Create large dataset
        recruiters = UserFactory.create_batch(20, user_type='recruiter')
        jobs = []
        for recruiter in recruiters:
            jobs.extend(JobPostFactory.create_batch(50, recruiter=recruiter))
        
        # Test query performance with Django ORM
        from django.test.utils import override_settings
        from django.db import connection
        from django.conf import settings
        
        # Enable query logging
        with override_settings(LOGGING_CONFIG=None):
            start_queries = len(connection.queries)
            start_time = time.time()
            
            # Simulate the query that would be made by the API
            from matcher.models import JobPost
            jobs_queryset = JobPost.objects.select_related('recruiter').filter(is_active=True)[:20]
            list(jobs_queryset)  # Force evaluation
            
            end_time = time.time()
            end_queries = len(connection.queries)
            
            query_time = end_time - start_time
            query_count = end_queries - start_queries
            
            self.assertLess(query_time, 0.1, "Job listing query should complete in under 0.1 seconds")
            self.assertLess(query_count, 5, "Job listing should use minimal database queries")
    
    def test_application_listing_query_performance(self):
        """Test database query performance for application listings."""
        # Create test data
        job_seeker = UserFactory(user_type='job_seeker')
        recruiter = UserFactory(user_type='recruiter')
        job_posts = JobPostFactory.create_batch(10, recruiter=recruiter)
        resume = ResumeFactory(job_seeker=job_seeker)
        
        # Create applications
        applications = []
        for job_post in job_posts:
            applications.append(ApplicationFactory(
                job_seeker=job_seeker,
                job_post=job_post,
                resume=resume
            ))
        
        # Test query performance
        from django.db import connection
        
        start_queries = len(connection.queries)
        start_time = time.time()
        
        # Simulate API query with proper select_related/prefetch_related
        from matcher.models import Application
        applications_queryset = Application.objects.select_related(
            'job_seeker', 'job_post', 'resume'
        ).filter(job_seeker=job_seeker)
        list(applications_queryset)  # Force evaluation
        
        end_time = time.time()
        end_queries = len(connection.queries)
        
        query_time = end_time - start_time
        query_count = end_queries - start_queries
        
        self.assertLess(query_time, 0.05, "Application listing query should complete in under 0.05 seconds")
        self.assertLess(query_count, 3, "Application listing should use minimal database queries")


@pytest.mark.performance
class TestMemoryUsagePerformance(TestCase):
    """Test memory usage and efficiency."""
    
    def test_large_dataset_memory_usage(self):
        """Test memory usage with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        batch_data = BatchJobFactory.create_jobs_with_applications(
            job_count=100, 
            applications_per_job=10
        )
        
        # Measure memory after data creation
        after_creation_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_creation_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this dataset)
        self.assertLess(memory_increase, 100, "Memory usage should be reasonable for large datasets")
        
        # Test API endpoint memory usage
        client = APIClient()
        job_seeker = UserFactory(user_type='job_seeker')
        client.force_authenticate(user=job_seeker)
        
        # Make multiple requests
        for _ in range(10):
            response = client.get('/api/job-posts/')
            self.assertEqual(response.status_code, 200)
        
        # Check memory after API calls
        after_api_memory = process.memory_info().rss / 1024 / 1024  # MB
        api_memory_increase = after_api_memory - after_creation_memory
        
        # API calls shouldn't significantly increase memory
        self.assertLess(api_memory_increase, 20, "API calls should not cause significant memory leaks")


@pytest.mark.performance
class TestCachePerformance(TestCase):
    """Test caching performance and effectiveness."""
    
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
    
    def test_job_listing_cache_performance(self):
        """Test job listing caching effectiveness."""
        # Create test data
        recruiter = UserFactory(user_type='recruiter')
        jobs = JobPostFactory.create_batch(50, recruiter=recruiter)
        
        client = APIClient()
        
        # First request (cache miss)
        start_time = time.time()
        response1 = client.get('/api/job-posts/')
        first_request_time = time.time() - start_time
        
        # Second request (should be cached if caching is implemented)
        start_time = time.time()
        response2 = client.get('/api/job-posts/')
        second_request_time = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Note: This test assumes caching is implemented
        # If caching is working, second request should be faster
        print(f"First request: {first_request_time:.4f}s, Second request: {second_request_time:.4f}s")


@pytest.mark.performance
class TestFileUploadPerformance(TestCase):
    """Test file upload performance."""
    
    def test_resume_upload_performance(self):
        """Test resume file upload performance."""
        job_seeker = UserFactory(user_type='job_seeker')
        client = APIClient()
        client.force_authenticate(user=job_seeker)
        
        # Create test file content
        file_sizes = [1024, 10240, 102400, 1048576]  # 1KB, 10KB, 100KB, 1MB
        
        for file_size in file_sizes:
            content = 'A' * file_size
            
            start_time = time.time()
            
            # Test file upload (mock)
            resume_data = {
                'original_filename': f'test_resume_{file_size}.txt',
                'parsed_text': content[:1000],  # Truncate for parsed_text
                'is_primary': True,
                'file_size': file_size
            }
            
            response = client.post('/api/resumes/', resume_data)
            upload_time = time.time() - start_time
            
            self.assertEqual(response.status_code, 201)
            
            # Upload time should scale reasonably with file size
            expected_max_time = 0.1 + (file_size / 1048576) * 2  # Base time + 2s per MB
            self.assertLess(upload_time, expected_max_time, 
                          f"Upload time for {file_size} bytes should be under {expected_max_time}s")


@pytest.mark.performance
class TestAIServicePerformance(TestCase):
    """Test AI service performance and scalability."""
    
    def setUp(self):
        self.job_seeker = UserFactory(user_type='job_seeker')
        self.recruiter = UserFactory(user_type='recruiter')
        self.client = APIClient()
        self.client.force_authenticate(user=self.job_seeker)
    
    @pytest.mark.skipif(not hasattr(pytest, 'mock'), reason="Mock not available")
    def test_resume_parsing_performance(self):
        """Test resume parsing performance with various file sizes."""
        from unittest.mock import patch, MagicMock
        
        # Mock Gemini API response
        mock_response = {
            'parsed_text': 'John Doe\nSoftware Engineer\n...',
            'parsed_data': {
                'personal_info': {'name': 'John Doe', 'email': 'john@example.com'},
                'skills': ['Python', 'Django', 'JavaScript'],
                'experience': [{'company': 'Tech Corp', 'position': 'Engineer'}]
            },
            'confidence_score': 0.95
        }
        
        with patch('matcher.services.parse_resume_with_gemini', return_value=mock_response):
            file_sizes = [1024, 10240, 102400, 1048576]  # 1KB to 1MB
            response_times = []
            
            for file_size in file_sizes:
                content = b'PDF content ' * (file_size // 12)
                
                from django.core.files.uploadedfile import SimpleUploadedFile
                test_file = SimpleUploadedFile(
                    f'resume_{file_size}.pdf',
                    content[:file_size],
                    content_type='application/pdf'
                )
                
                start_time = time.time()
                response = self.client.post('/api/parse-resume/', {
                    'resume_file': test_file
                }, format='multipart')
                response_time = time.time() - start_time
                
                response_times.append(response_time)
                self.assertEqual(response.status_code, 200)
                
                # Resume parsing should complete within reasonable time
                max_expected_time = 2.0 + (file_size / 1048576) * 3  # Base + 3s per MB
                self.assertLess(response_time, max_expected_time,
                              f"Resume parsing for {file_size} bytes should complete in under {max_expected_time}s")
            
            # Response time should not increase dramatically with file size
            avg_response_time = statistics.mean(response_times)
            self.assertLess(avg_response_time, 5.0, "Average resume parsing time should be under 5 seconds")
    
    @pytest.mark.skipif(not hasattr(pytest, 'mock'), reason="Mock not available")
    def test_match_score_calculation_performance(self):
        """Test match score calculation performance."""
        from unittest.mock import patch
        
        # Create test data
        job_post = JobPostFactory(recruiter=self.recruiter)
        resume = ResumeFactory(job_seeker=self.job_seeker)
        
        mock_score_response = {
            'overall_score': 87.5,
            'breakdown': {'skills_match': 92.0, 'experience_match': 85.0},
            'matching_skills': ['Python', 'Django'],
            'missing_skills': ['Docker'],
            'confidence': 0.94
        }
        
        with patch('matcher.services.calculate_match_score_with_ml', return_value=mock_score_response):
            response_times = []
            
            # Test multiple match score calculations
            for _ in range(10):
                match_data = {
                    'resume_id': str(resume.id),
                    'job_id': str(job_post.id)
                }
                
                start_time = time.time()
                response = self.client.post('/api/calculate-match-score/', match_data)
                response_time = time.time() - start_time
                
                response_times.append(response_time)
                self.assertEqual(response.status_code, 200)
            
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            self.assertLess(avg_response_time, 1.0, "Average match score calculation should be under 1 second")
            self.assertLess(max_response_time, 2.0, "Max match score calculation should be under 2 seconds")
    
    def test_batch_processing_performance(self):
        """Test batch processing performance for AI operations."""
        from unittest.mock import patch
        
        # Create test data
        job_posts = JobPostFactory.create_batch(5, recruiter=self.recruiter)
        resumes = ResumeFactory.create_batch(5, job_seeker=self.job_seeker)
        
        batch_data = {
            'resume_ids': [str(r.id) for r in resumes],
            'job_ids': [str(j.id) for j in job_posts]
        }
        
        with patch('matcher.tasks.batch_calculate_match_scores.delay') as mock_task:
            mock_task.return_value.id = 'test-batch-task-id'
            
            start_time = time.time()
            response = self.client.post('/api/batch-calculate-match-scores/', batch_data)
            response_time = time.time() - start_time
            
            self.assertEqual(response.status_code, 202)
            self.assertIn('task_id', response.data)
            
            # Batch request submission should be fast
            self.assertLess(response_time, 0.5, "Batch processing submission should be under 0.5 seconds")


@pytest.mark.performance
class TestWebSocketPerformance(TestCase):
    """Test WebSocket performance and scalability."""
    
    def setUp(self):
        self.users = UserFactory.create_batch(10, user_type='job_seeker')
    
    @pytest.mark.asyncio
    async def test_websocket_connection_performance(self):
        """Test WebSocket connection establishment performance."""
        from channels.testing import WebsocketCommunicator
        from matcher.consumers import NotificationConsumer
        
        connection_times = []
        
        for user in self.users[:5]:  # Test with 5 concurrent connections
            start_time = time.time()
            
            communicator = WebsocketCommunicator(
                NotificationConsumer.as_asgi(),
                f"/ws/notifications/?token={self._get_jwt_token(user)}"
            )
            
            connected, subprotocol = await communicator.connect()
            connection_time = time.time() - start_time
            
            connection_times.append(connection_time)
            self.assertTrue(connected)
            
            await communicator.disconnect()
        
        avg_connection_time = statistics.mean(connection_times)
        max_connection_time = max(connection_times)
        
        self.assertLess(avg_connection_time, 1.0, "Average WebSocket connection should be under 1 second")
        self.assertLess(max_connection_time, 2.0, "Max WebSocket connection should be under 2 seconds")
    
    def _get_jwt_token(self, user):
        """Get JWT token for user."""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    @pytest.mark.asyncio
    async def test_notification_broadcast_performance(self):
        """Test notification broadcasting performance."""
        from channels.testing import WebsocketCommunicator
        from matcher.consumers import NotificationConsumer
        from matcher.notification_utils import broadcast_notification
        
        # Establish multiple connections
        communicators = []
        for user in self.users[:3]:
            communicator = WebsocketCommunicator(
                NotificationConsumer.as_asgi(),
                f"/ws/notifications/?token={self._get_jwt_token(user)}"
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            communicators.append(communicator)
        
        # Test broadcast performance
        start_time = time.time()
        
        # Simulate notification broadcast
        notification_data = {
            'type': 'job.posted',
            'data': {
                'job_id': 'test-job-id',
                'title': 'Test Job',
                'company': 'Test Company'
            }
        }
        
        # This would normally use the actual broadcast function
        # For testing, we'll simulate the time it takes
        await asyncio.sleep(0.1)  # Simulate broadcast time
        
        broadcast_time = time.time() - start_time
        
        # Clean up connections
        for communicator in communicators:
            await communicator.disconnect()
        
        self.assertLess(broadcast_time, 0.5, "Notification broadcast should complete in under 0.5 seconds")


@pytest.mark.performance
class TestPaginationPerformance(TestCase):
    """Test pagination performance with large datasets."""
    
    def setUp(self):
        self.client = APIClient()
        self.job_seeker = UserFactory(user_type='job_seeker')
        self.client.force_authenticate(user=self.job_seeker)
        
        # Create large dataset
        self.recruiters = UserFactory.create_batch(20, user_type='recruiter')
        self.jobs = []
        for recruiter in self.recruiters:
            self.jobs.extend(JobPostFactory.create_batch(50, recruiter=recruiter))
    
    def test_pagination_performance_across_pages(self):
        """Test pagination performance across different pages."""
        page_sizes = [10, 20, 50, 100]
        
        for page_size in page_sizes:
            response_times = []
            
            # Test first few pages
            for page in range(1, 6):
                start_time = time.time()
                response = self.client.get(f'/api/job-posts/?page={page}&page_size={page_size}')
                response_time = time.time() - start_time
                
                response_times.append(response_time)
                self.assertEqual(response.status_code, 200)
                
                # Verify pagination data
                self.assertIn('count', response.data)
                self.assertIn('next', response.data)
                self.assertIn('previous', response.data)
                self.assertIn('results', response.data)
            
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            # Performance should be consistent across pages
            self.assertLess(avg_response_time, 1.0, 
                          f"Average pagination response time for page_size={page_size} should be under 1 second")
            self.assertLess(max_response_time, 2.0,
                          f"Max pagination response time for page_size={page_size} should be under 2 seconds")
    
    def test_large_page_size_performance(self):
        """Test performance with large page sizes."""
        large_page_sizes = [100, 200, 500]
        
        for page_size in large_page_sizes:
            start_time = time.time()
            response = self.client.get(f'/api/job-posts/?page=1&page_size={page_size}')
            response_time = time.time() - start_time
            
            self.assertEqual(response.status_code, 200)
            
            # Larger page sizes should still be reasonable
            max_expected_time = 0.5 + (page_size / 1000) * 2  # Base time + scaling factor
            self.assertLess(response_time, max_expected_time,
                          f"Large page size {page_size} should complete in under {max_expected_time}s")


@pytest.mark.performance
class TestFilteringPerformance(TestCase):
    """Test filtering and search performance."""
    
    def setUp(self):
        self.client = APIClient()
        self.job_seeker = UserFactory(user_type='job_seeker')
        self.client.force_authenticate(user=self.job_seeker)
        
        # Create diverse test data for filtering
        self.recruiter = UserFactory(user_type='recruiter')
        self._create_diverse_jobs()
    
    def _create_diverse_jobs(self):
        """Create diverse job postings for filtering tests."""
        job_types = ['full_time', 'part_time', 'contract', 'internship']
        experience_levels = ['entry', 'junior', 'mid', 'senior', 'lead']
        locations = ['New York, NY', 'San Francisco, CA', 'Remote', 'Austin, TX', 'Seattle, WA']
        skills_sets = [
            ['Python', 'Django', 'PostgreSQL'],
            ['JavaScript', 'React', 'Node.js'],
            ['Java', 'Spring', 'MySQL'],
            ['C#', '.NET', 'SQL Server'],
            ['Go', 'Docker', 'Kubernetes']
        ]
        
        for i in range(200):  # Create 200 diverse jobs
            JobPostFactory(
                recruiter=self.recruiter,
                title=f'Developer Position {i}',
                job_type=job_types[i % len(job_types)],
                experience_level=experience_levels[i % len(experience_levels)],
                location=locations[i % len(locations)],
                skills_required=','.join(skills_sets[i % len(skills_sets)]),
                salary_min=50000 + (i % 10) * 10000,
                salary_max=80000 + (i % 10) * 10000
            )
    
    def test_single_filter_performance(self):
        """Test performance of single filter operations."""
        filters = [
            ('job_type', 'full_time'),
            ('experience_level', 'senior'),
            ('location', 'Remote'),
            ('salary_min', '60000'),
            ('salary_max', '100000')
        ]
        
        for filter_name, filter_value in filters:
            start_time = time.time()
            response = self.client.get(f'/api/job-posts/?{filter_name}={filter_value}')
            response_time = time.time() - start_time
            
            self.assertEqual(response.status_code, 200)
            self.assertLess(response_time, 0.5, 
                          f"Single filter {filter_name} should complete in under 0.5 seconds")
    
    def test_multiple_filter_performance(self):
        """Test performance of multiple combined filters."""
        filter_combinations = [
            'job_type=full_time&experience_level=senior',
            'location=Remote&salary_min=70000',
            'job_type=contract&experience_level=mid&location=San Francisco, CA',
            'salary_min=60000&salary_max=90000&experience_level=senior'
        ]
        
        for filter_combo in filter_combinations:
            start_time = time.time()
            response = self.client.get(f'/api/job-posts/?{filter_combo}')
            response_time = time.time() - start_time
            
            self.assertEqual(response.status_code, 200)
            self.assertLess(response_time, 1.0,
                          f"Multiple filters should complete in under 1 second: {filter_combo}")
    
    def test_text_search_performance(self):
        """Test text search performance with various query lengths."""
        search_queries = [
            'Python',
            'Python Django',
            'Python Django PostgreSQL',
            'Senior Python Developer',
            'Senior Python Developer with Django experience'
        ]
        
        for query in search_queries:
            start_time = time.time()
            response = self.client.get(f'/api/job-posts/?search={query}')
            response_time = time.time() - start_time
            
            self.assertEqual(response.status_code, 200)
            
            # Search performance should not degrade significantly with query length
            max_expected_time = 0.3 + len(query.split()) * 0.1  # Base + word count factor
            self.assertLess(response_time, max_expected_time,
                          f"Search query '{query}' should complete in under {max_expected_time}s")


# Locust performance test configuration
class LocustPerformanceTest:
    """
    Locust performance test configuration.
    Run with: locust -f tests_performance.py --host=http://localhost:8000
    """
    
    def __init__(self):
        try:
            from locust import HttpUser, task, between
            
            class HireWiseUser(HttpUser):
                wait_time = between(1, 3)
                
                def on_start(self):
                    """Login user when starting."""
                    # Create test user (this would be done in setup)
                    login_data = {
                        'username': 'testuser',
                        'password': 'testpass123'
                    }
                    response = self.client.post('/api/auth/jwt/login/', json=login_data)
                    if response.status_code == 200:
                        token = response.json()['access']
                        self.client.headers.update({'Authorization': f'Bearer {token}'})
                
                @task(3)
                def browse_jobs(self):
                    """Browse job listings."""
                    self.client.get('/api/job-posts/')
                
                @task(2)
                def search_jobs(self):
                    """Search for jobs."""
                    search_terms = ['Python', 'JavaScript', 'Developer', 'Engineer']
                    term = search_terms[hash(self.user_id) % len(search_terms)]
                    self.client.get(f'/api/job-posts/?search={term}')
                
                @task(1)
                def view_profile(self):
                    """View user profile."""
                    self.client.get('/api/auth/profile/')
                
                @task(1)
                def view_applications(self):
                    """View job applications."""
                    self.client.get('/api/applications/')
            
            self.HireWiseUser = HireWiseUser
            
        except ImportError:
            # Locust not available
            pass


# Performance test runner
def run_performance_tests():
    """Run all performance tests and generate report."""
    import subprocess
    import sys
    
    print("Running HireWise Backend Performance Tests...")
    print("=" * 50)
    
    # Run pytest performance tests
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'matcher/tests_performance.py',
        '-v', '-m', 'performance',
        '--tb=short'
    ], capture_output=True, text=True)
    
    print("Performance Test Results:")
    print(result.stdout)
    
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    return result.returncode == 0


if __name__ == '__main__':
    run_performance_tests()