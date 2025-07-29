#!/usr/bin/env python3
import json
import subprocess
import requests
from datetime import datetime
from pathlib import Path

class MonitoringDashboard:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
    
    def get_system_status(self):
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'status': 'healthy'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_django_status(self):
        try:
            response = requests.get('http://localhost:8000/api/health/', timeout=5)
            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'http_status': response.status_code
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_redis_status(self):
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            return {'status': 'healthy'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_celery_status(self):
        try:
            result = subprocess.run(
                ['celery', '-A', 'hirewise', 'inspect', 'ping'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.base_dir
            )
            return {
                'status': 'healthy' if result.returncode == 0 else 'unhealthy',
                'workers': 'active' if 'pong' in result.stdout.lower() else 'inactive'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_log_summary(self):
        log_dir = self.base_dir / 'logs'
        summary = {'errors': 0, 'warnings': 0, 'info': 0}
        
        try:
            for log_file in log_dir.glob('*.log'):
                with open(log_file, 'r') as f:
                    content = f.read()
                    summary['errors'] += content.count('ERROR')
                    summary['warnings'] += content.count('WARNING')
                    summary['info'] += content.count('INFO')
        except Exception as e:
            summary['error'] = str(e)
        
        return summary
    
    def generate_dashboard(self):
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'system': self.get_system_status(),
            'django': self.get_django_status(),
            'redis': self.get_redis_status(),
            'celery': self.get_celery_status(),
            'logs': self.get_log_summary()
        }
        
        return dashboard
    
    def print_dashboard(self):
        dashboard = self.generate_dashboard()
        
        print("🔍 HireWise Monitoring Dashboard")
        print("=" * 50)
        print(f"📅 Generated: {dashboard['timestamp']}")
        print()
        
        # System status
        system = dashboard['system']
        status_icon = "✅" if system['status'] == 'healthy' else "❌"
        print(f"{status_icon} System Status: {system['status']}")
        if 'cpu_percent' in system:
            print(f"   💻 CPU: {system['cpu_percent']:.1f}%")
            print(f"   🧠 Memory: {system['memory_percent']:.1f}%")
            print(f"   💾 Disk: {system['disk_percent']:.1f}%")
        print()
        
        # Django status
        django = dashboard['django']
        status_icon = "✅" if django['status'] == 'healthy' else "❌"
        print(f"{status_icon} Django Status: {django['status']}")
        if 'response_time_ms' in django:
            print(f"   ⚡ Response Time: {django['response_time_ms']:.1f}ms")
        print()
        
        # Redis status
        redis = dashboard['redis']
        status_icon = "✅" if redis['status'] == 'healthy' else "❌"
        print(f"{status_icon} Redis Status: {redis['status']}")
        print()
        
        # Celery status
        celery = dashboard['celery']
        status_icon = "✅" if celery['status'] == 'healthy' else "❌"
        print(f"{status_icon} Celery Status: {celery['status']}")
        if 'workers' in celery:
            print(f"   👷 Workers: {celery['workers']}")
        print()
        
        # Log summary
        logs = dashboard['logs']
        print("📋 Log Summary (recent):")
        print(f"   🔴 Errors: {logs.get('errors', 0)}")
        print(f"   🟡 Warnings: {logs.get('warnings', 0)}")
        print(f"   ℹ️  Info: {logs.get('info', 0)}")
        print()
        
        # Overall health
        all_healthy = all([
            dashboard['system']['status'] == 'healthy',
            dashboard['django']['status'] == 'healthy',
            dashboard['redis']['status'] == 'healthy',
            dashboard['celery']['status'] == 'healthy'
        ])
        
        overall_icon = "✅" if all_healthy else "⚠️"
        overall_status = "HEALTHY" if all_healthy else "NEEDS ATTENTION"
        print(f"{overall_icon} Overall Status: {overall_status}")

if __name__ == '__main__':
    dashboard = MonitoringDashboard()
    dashboard.print_dashboard()