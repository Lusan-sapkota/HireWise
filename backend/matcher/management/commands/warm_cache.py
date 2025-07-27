"""
Management command to warm up application caches.
"""

import logging
from django.core.management.base import BaseCommand
from django.conf import settings

from matcher.cache_utils import warm_cache, clear_all_caches
from matcher.api_cache import APICacheWarmer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Warm up application caches with frequently accessed data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-first',
            action='store_true',
            help='Clear all caches before warming up',
        )
        parser.add_argument(
            '--skip-jobs',
            action='store_true',
            help='Skip job list cache warming',
        )
        parser.add_argument(
            '--skip-skills',
            action='store_true',
            help='Skip skills cache warming',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )
    
    def handle(self, *args, **options):
        if options['verbose']:
            logger.setLevel(logging.DEBUG)
        
        self.stdout.write(
            self.style.SUCCESS('Starting cache warm-up process...')
        )
        
        try:
            # Clear caches if requested
            if options['clear_first']:
                self.stdout.write('Clearing existing caches...')
                clear_all_caches()
                self.stdout.write(
                    self.style.SUCCESS('Caches cleared successfully')
                )
            
            # Warm up general caches
            self.stdout.write('Warming up general caches...')
            warm_cache()
            
            # Warm up job list cache
            if not options['skip_jobs']:
                self.stdout.write('Warming up job list cache...')
                APICacheWarmer.warm_job_list_cache()
            
            # Warm up skills cache
            if not options['skip_skills']:
                self.stdout.write('Warming up skills cache...')
                APICacheWarmer.warm_skills_cache()
            
            self.stdout.write(
                self.style.SUCCESS('Cache warm-up completed successfully!')
            )
            
        except Exception as e:
            logger.error(f"Cache warm-up failed: {e}")
            self.stdout.write(
                self.style.ERROR(f'Cache warm-up failed: {e}')
            )
            raise