"""
Management command to clean up expired notifications.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from matcher.notification_service import notification_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up expired notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS('Starting expired notifications cleanup')
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        try:
            from matcher.models import Notification
            
            # Get count of expired notifications
            now = timezone.now()
            expired_notifications = Notification.objects.filter(
                expires_at__lt=now
            )
            
            expired_count = expired_notifications.count()
            
            if verbose and expired_count > 0:
                self.stdout.write(f'Found {expired_count} expired notifications:')
                for notification in expired_notifications[:10]:  # Show first 10
                    self.stdout.write(
                        f'  - {notification.notification_type} for {notification.recipient.username} '
                        f'(expired: {notification.expires_at})'
                    )
                if expired_count > 10:
                    self.stdout.write(f'  ... and {expired_count - 10} more')
            
            if not dry_run and expired_count > 0:
                # Perform cleanup using notification service
                cleaned_count = notification_service.cleanup_expired_notifications()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully cleaned up {cleaned_count} expired notifications')
                )
            elif expired_count == 0:
                self.stdout.write('No expired notifications found')
            else:
                self.stdout.write(
                    self.style.WARNING(f'Would clean up {expired_count} expired notifications')
                )
            
            # Show statistics
            if verbose:
                total_notifications = Notification.objects.count()
                unread_notifications = Notification.objects.filter(is_read=False).count()
                
                self.stdout.write(f'\nNotification statistics:')
                self.stdout.write(f'  Total notifications: {total_notifications}')
                self.stdout.write(f'  Unread notifications: {unread_notifications}')
                self.stdout.write(f'  Expired notifications: {expired_count}')
        
        except Exception as e:
            logger.error(f"Error during notification cleanup: {e}")
            self.stdout.write(
                self.style.ERROR(f'Error during cleanup: {e}')
            )
            return
        
        self.stdout.write(self.style.SUCCESS('Notification cleanup completed'))