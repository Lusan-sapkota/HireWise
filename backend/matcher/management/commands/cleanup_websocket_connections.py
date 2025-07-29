"""
Management command to clean up stale WebSocket connections.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from matcher.middleware import websocket_connection_manager
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up stale WebSocket connections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-age',
            type=int,
            default=30,
            help='Maximum age in minutes for connections to be considered stale (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it'
        )

    def handle(self, *args, **options):
        max_age_minutes = options['max_age']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting WebSocket connection cleanup (max age: {max_age_minutes} minutes)'
            )
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get current connection stats
        total_connections = len(websocket_connection_manager.connection_metadata)
        online_users = len(websocket_connection_manager.active_connections)
        
        self.stdout.write(f'Current stats:')
        self.stdout.write(f'  Total connections: {total_connections}')
        self.stdout.write(f'  Online users: {online_users}')
        
        if not dry_run:
            # Perform cleanup
            cleaned_count = websocket_connection_manager.cleanup_stale_connections(max_age_minutes)
            
            self.stdout.write(
                self.style.SUCCESS(f'Cleaned up {cleaned_count} stale connections')
            )
        else:
            # Simulate cleanup to show what would be cleaned
            cutoff_time = timezone.now() - timezone.timedelta(minutes=max_age_minutes)
            stale_count = 0
            
            for channel_name, metadata in websocket_connection_manager.connection_metadata.items():
                if metadata.get('last_activity', timezone.now()) < cutoff_time:
                    stale_count += 1
                    user_id = metadata.get('user_id', 'unknown')
                    consumer_type = metadata.get('connection_info', {}).get('consumer_type', 'unknown')
                    last_activity = metadata.get('last_activity', 'unknown')
                    
                    self.stdout.write(
                        f'  Would clean: User {user_id}, Type {consumer_type}, Last activity: {last_activity}'
                    )
            
            self.stdout.write(
                self.style.WARNING(f'Would clean up {stale_count} stale connections')
            )
        
        # Show final stats
        if not dry_run:
            final_connections = len(websocket_connection_manager.connection_metadata)
            final_users = len(websocket_connection_manager.active_connections)
            
            self.stdout.write(f'Final stats:')
            self.stdout.write(f'  Total connections: {final_connections}')
            self.stdout.write(f'  Online users: {final_users}')
        
        self.stdout.write(self.style.SUCCESS('WebSocket cleanup completed'))