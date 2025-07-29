from django.core.management.base import BaseCommand
from django.http import JsonResponse
from matcher.health_views import DetailedHealthCheckView
from django.test import RequestFactory
import json

class Command(BaseCommand):
    help = 'Run comprehensive health checks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            help='Output format (json, text)'
        )
    
    def handle(self, *args, **options):
        factory = RequestFactory()
        request = factory.get('/health/')
        
        health_view = DetailedHealthCheckView()
        response = health_view.get(request)
        
        if options['format'] == 'json':
            self.stdout.write(response.content.decode())
        else:
            data = json.loads(response.content.decode())
            self.stdout.write(f"Status: {data['status']}")
            self.stdout.write(f"Response Time: {data['response_time_ms']}ms")
            
            for check_name, check_data in data['checks'].items():
                status_icon = "✅" if check_data['status'] == 'healthy' else "❌"
                self.stdout.write(f"{status_icon} {check_name}: {check_data['status']}")
                if 'response_time_ms' in check_data:
                    self.stdout.write(f"   Response time: {check_data['response_time_ms']}ms")