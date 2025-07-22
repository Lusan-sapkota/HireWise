"""
Django management command for cleaning up old files.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

from matcher.file_utils import SecureFileStorage
from matcher.models import Resume

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up old files and orphaned file records'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete files older than this many days (default: 30)'
        )
        
        parser.add_argument(
            '--file-type',
            type=str,
            help='Only clean up specific file type (e.g., resume, image)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        
        parser.add_argument(
            '--cleanup-orphaned',
            action='store_true',
            help='Also clean up orphaned database records'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup without confirmation'
        )
    
    def handle(self, *args, **options):
        days_old = options['days']
        file_type = options.get('file_type')
        dry_run = options['dry_run']
        cleanup_orphaned = options['cleanup_orphaned']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting file cleanup (older than {days_old} days)')
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No files will be deleted'))
        
        if not force and not dry_run:
            confirm = input('Are you sure you want to delete old files? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Cleanup cancelled'))
                return
        
        try:
            # Clean up files from storage
            storage_manager = SecureFileStorage()
            cleanup_stats = storage_manager.cleanup_old_files(days_old, file_type)
            
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Would delete {cleanup_stats["files_deleted"]} files '
                        f'({cleanup_stats["space_freed"]} bytes)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Deleted {cleanup_stats["files_deleted"]} files '
                        f'({cleanup_stats["space_freed"]} bytes freed)'
                    )
                )
            
            # Clean up orphaned database records
            if cleanup_orphaned:
                orphaned_stats = self._cleanup_orphaned_records(days_old, dry_run)
                
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Would delete {orphaned_stats["records_deleted"]} orphaned records'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Deleted {orphaned_stats["records_deleted"]} orphaned records'
                        )
                    )
            
            # Report errors if any
            if cleanup_stats['errors']:
                self.stdout.write(
                    self.style.ERROR(f'Errors encountered: {len(cleanup_stats["errors"])}')
                )
                for error in cleanup_stats['errors']:
                    self.stdout.write(self.style.ERROR(f'  - {error}'))
            
            self.stdout.write(self.style.SUCCESS('File cleanup completed'))
            
        except Exception as e:
            logger.error(f'Error during file cleanup: {str(e)}')
            raise CommandError(f'File cleanup failed: {str(e)}')
    
    def _cleanup_orphaned_records(self, days_old: int, dry_run: bool = False) -> dict:
        """Clean up orphaned database records for files that no longer exist"""
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        stats = {
            'records_scanned': 0,
            'records_deleted': 0,
            'errors': []
        }
        
        try:
            # Check Resume records
            old_resumes = Resume.objects.filter(uploaded_at__lt=cutoff_date)
            stats['records_scanned'] = old_resumes.count()
            
            for resume in old_resumes:
                try:
                    # Check if file exists in storage
                    from django.core.files.storage import default_storage
                    
                    if not default_storage.exists(resume.file.name):
                        if not dry_run:
                            resume.delete()
                        stats['records_deleted'] += 1
                        logger.info(f'Deleted orphaned resume record: {resume.id}')
                
                except Exception as e:
                    error_msg = f'Error processing resume {resume.id}: {str(e)}'
                    stats['errors'].append(error_msg)
                    logger.error(error_msg)
            
            return stats
            
        except Exception as e:
            error_msg = f'Error during orphaned record cleanup: {str(e)}'
            stats['errors'].append(error_msg)
            logger.error(error_msg)
            return stats