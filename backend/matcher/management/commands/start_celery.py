"""
Django management command to start Celery workers and beat scheduler.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import subprocess
import sys
import os
import signal
import time
from multiprocessing import Process


class Command(BaseCommand):
    """
    Management command to start Celery workers and beat scheduler.
    """
    
    help = 'Start Celery workers and beat scheduler for background task processing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--workers',
            type=int,
            default=2,
            help='Number of worker processes to start (default: 2)'
        )
        parser.add_argument(
            '--concurrency',
            type=int,
            default=4,
            help='Number of concurrent tasks per worker (default: 4)'
        )
        parser.add_argument(
            '--loglevel',
            type=str,
            default='info',
            choices=['debug', 'info', 'warning', 'error', 'critical'],
            help='Log level for Celery workers (default: info)'
        )
        parser.add_argument(
            '--queues',
            type=str,
            default='celery,ai_processing,notifications,maintenance',
            help='Comma-separated list of queues to process (default: celery,ai_processing,notifications,maintenance)'
        )
        parser.add_argument(
            '--beat',
            action='store_true',
            help='Start Celery beat scheduler for periodic tasks'
        )
        parser.add_argument(
            '--flower',
            action='store_true',
            help='Start Flower monitoring tool'
        )
        parser.add_argument(
            '--flower-port',
            type=int,
            default=5555,
            help='Port for Flower monitoring tool (default: 5555)'
        )
        parser.add_argument(
            '--dev',
            action='store_true',
            help='Development mode with auto-reload'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        self.stdout.write(
            self.style.SUCCESS('Starting Celery workers and services...')
        )
        
        # Validate Redis connection
        if not self._check_redis_connection():
            raise CommandError('Redis connection failed. Please ensure Redis is running.')
        
        # Store process references for cleanup
        self.processes = []
        
        try:
            # Start Celery workers
            self._start_workers(options)
            
            # Start Celery beat scheduler if requested
            if options['beat']:
                self._start_beat(options)
            
            # Start Flower monitoring if requested
            if options['flower']:
                self._start_flower(options)
            
            # Keep the command running
            self._wait_for_shutdown()
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nShutting down Celery services...')
            )
        finally:
            self._cleanup_processes()
    
    def _check_redis_connection(self):
        """Check if Redis is available."""
        try:
            import redis
            redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
            redis_client.ping()
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Redis connection error: {e}')
            )
            return False
    
    def _start_workers(self, options):
        """Start Celery worker processes."""
        workers = options['workers']
        concurrency = options['concurrency']
        loglevel = options['loglevel']
        queues = options['queues']
        
        for i in range(workers):
            worker_name = f'worker{i+1}@%h'
            
            cmd = [
                'celery',
                '-A', 'hirewise',
                'worker',
                '--loglevel', loglevel,
                '--concurrency', str(concurrency),
                '--queues', queues,
                '--hostname', worker_name,
                '--without-gossip',
                '--without-mingle',
                '--without-heartbeat'
            ]
            
            if options['dev']:
                cmd.extend(['--pool', 'solo'])
            
            self.stdout.write(f'Starting worker {i+1}/{workers}...')
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append(('worker', process))
            
            # Give worker time to start
            time.sleep(1)
    
    def _start_beat(self, options):
        """Start Celery beat scheduler."""
        loglevel = options['loglevel']
        
        cmd = [
            'celery',
            '-A', 'hirewise',
            'beat',
            '--loglevel', loglevel,
            '--scheduler', 'django_celery_beat.schedulers:DatabaseScheduler'
        ]
        
        self.stdout.write('Starting Celery beat scheduler...')
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        self.processes.append(('beat', process))
    
    def _start_flower(self, options):
        """Start Flower monitoring tool."""
        port = options['flower_port']
        
        cmd = [
            'celery',
            '-A', 'hirewise',
            'flower',
            '--port', str(port),
            '--broker', settings.CELERY_BROKER_URL
        ]
        
        self.stdout.write(f'Starting Flower monitoring on port {port}...')
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        self.processes.append(('flower', process))
        
        self.stdout.write(
            self.style.SUCCESS(f'Flower monitoring available at http://localhost:{port}')
        )
    
    def _wait_for_shutdown(self):
        """Wait for shutdown signal."""
        self.stdout.write(
            self.style.SUCCESS('Celery services started successfully!')
        )
        self.stdout.write('Press Ctrl+C to stop all services.')
        
        try:
            # Monitor processes and restart if they die
            while True:
                time.sleep(5)
                
                for service_type, process in self.processes:
                    if process.poll() is not None:
                        self.stdout.write(
                            self.style.ERROR(f'{service_type} process died, exit code: {process.returncode}')
                        )
                        # In production, you might want to restart the process here
                
        except KeyboardInterrupt:
            pass
    
    def _cleanup_processes(self):
        """Clean up all started processes."""
        for service_type, process in self.processes:
            if process.poll() is None:
                self.stdout.write(f'Stopping {service_type}...')
                
                try:
                    # Send SIGTERM first
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        # Force kill if not responding
                        self.stdout.write(f'Force killing {service_type}...')
                        process.kill()
                        process.wait()
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error stopping {service_type}: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS('All Celery services stopped.')
        )