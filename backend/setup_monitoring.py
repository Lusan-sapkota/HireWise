#!/usr/bin/env python3
"""
HireWise Monitoring and Logging Infrastructure Setup
This script sets up comprehensive monitoring, logging, and health check infrastructure
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirewise.settings')

import django
django.setup()

from django.conf import settings
from django.core.management import execute_from_command_line

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoringSetup:
    """Monitoring and logging infrastructure setup manager"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.success_count = 0
        self.total_steps = 6
    
    def run_setup(self):
        """Run complete monitoring setup"""
        logger.info("🔍 Starting HireWise Monitoring Infrastructure Setup")
        logger.info("=" * 60)
        
        try:
            self.setup_log_rotation()
            self.create_monitoring_config()
            self.setup_health_check_endpoints()
            self.create_performance_monitoring()
            self.setup_error_tracking()
            self.create_monitoring_dashboard()
            
            logger.info("=" * 60)
            logger.info(f"✅ Monitoring setup completed! ({self.success_count}/{self.total_steps} steps)")
            logger.info("🎉 Your HireWise monitoring infrastructure is ready!")
            
        except Exception as e:
            logger.error(f"❌ Monitoring setup failed: {str(e)}")
            sys.exit(1)
    
    def setup_log_rotation(self):
        """Setup log rotation configuration"""
        logger.info("📋 Setting up log rotation...")
        
        # Create logrotate configuration
        logrotate_config = """
# HireWise Log Rotation Configuration
/home/*/Documents/HireWise/backend/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        # Restart Django if running
        if [ -f /var/run/hirewise.pid ]; then
            kill -USR1 `cat /var/run/hirewise.pid`
        fi
    endscript
}
"""
        
        # Create monitoring directory
        monitoring_dir = self.base_dir / 'monitoring'
        monitoring_dir.mkdir(exist_ok=True)
        
        # Write logrotate config
        logrotate_file = monitoring_dir / 'hirewise-logrotate'
        logrotate_file.write_text(logrotate_config.strip())
        
        logger.info("   ✓ Created logrotate configuration")
        
        # Create log analysis script
        log_analysis_script = """#!/bin/bash
# HireWise Log Analysis Script

LOG_DIR="/home/*/Documents/HireWise/backend/logs"
REPORT_FILE="/tmp/hirewise-log-report.txt"

echo "HireWise Log Analysis Report - $(date)" > $REPORT_FILE
echo "=========================================" >> $REPORT_FILE

# Error count in last 24 hours
echo "Errors in last 24 hours:" >> $REPORT_FILE
find $LOG_DIR -name "*.log" -mtime -1 -exec grep -c "ERROR" {} + | awk '{sum+=$1} END {print "Total errors: " sum}' >> $REPORT_FILE

# Warning count in last 24 hours
echo "Warnings in last 24 hours:" >> $REPORT_FILE
find $LOG_DIR -name "*.log" -mtime -1 -exec grep -c "WARNING" {} + | awk '{sum+=$1} END {print "Total warnings: " sum}' >> $REPORT_FILE

# Top error messages
echo "Top error messages:" >> $REPORT_FILE
find $LOG_DIR -name "*.log" -mtime -1 -exec grep "ERROR" {} + | sort | uniq -c | sort -nr | head -10 >> $REPORT_FILE

# Security events
echo "Security events:" >> $REPORT_FILE
find $LOG_DIR -name "security.log" -mtime -1 -exec wc -l {} + >> $REPORT_FILE

echo "Report generated at: $(date)" >> $REPORT_FILE
cat $REPORT_FILE
"""
        
        analysis_script = monitoring_dir / 'analyze_logs.sh'
        analysis_script.write_text(log_analysis_script.strip())
        analysis_script.chmod(0o755)
        
        logger.info("   ✓ Created log analysis script")
        
        self.success_count += 1
        logger.info("✅ Log rotation setup completed")
    
    def create_monitoring_config(self):
        """Create monitoring configuration files"""
        logger.info("⚙️  Creating monitoring configuration...")
        
        monitoring_dir = self.base_dir / 'monitoring'
        
        # Prometheus configuration
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "rule_files": [],
            "scrape_configs": [
                {
                    "job_name": "hirewise-django",
                    "static_configs": [
                        {
                            "targets": ["localhost:8000"]
                        }
                    ],
                    "metrics_path": "/api/metrics/",
                    "scrape_interval": "30s"
                },
                {
                    "job_name": "hirewise-celery",
                    "static_configs": [
                        {
                            "targets": ["localhost:5555"]
                        }
                    ],
                    "scrape_interval": "30s"
                },
                {
                    "job_name": "redis",
                    "static_configs": [
                        {
                            "targets": ["localhost:6379"]
                        }
                    ],
                    "scrape_interval": "30s"
                }
            ]
        }
        
        prometheus_file = monitoring_dir / 'prometheus.yml'
        with open(prometheus_file, 'w') as f:
            import yaml
            yaml.dump(prometheus_config, f, default_flow_style=False)
        
        logger.info("   ✓ Created Prometheus configuration")
        
        # Grafana dashboard configuration
        grafana_dashboard = {
            "dashboard": {
                "id": None,
                "title": "HireWise Monitoring Dashboard",
                "tags": ["hirewise", "django", "celery"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Request Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(django_http_requests_total[5m])",
                                "legendFormat": "{{method}} {{status}}"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "Response Time",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(django_http_request_duration_seconds_bucket[5m]))",
                                "legendFormat": "95th percentile"
                            }
                        ]
                    },
                    {
                        "id": 3,
                        "title": "Celery Tasks",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "celery_tasks_total",
                                "legendFormat": "{{state}}"
                            }
                        ]
                    }
                ],
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "refresh": "30s"
            }
        }
        
        grafana_file = monitoring_dir / 'hirewise-dashboard.json'
        with open(grafana_file, 'w') as f:
            json.dump(grafana_dashboard, f, indent=2)
        
        logger.info("   ✓ Created Grafana dashboard configuration")
        
        self.success_count += 1
        logger.info("✅ Monitoring configuration created")
    
    def setup_health_check_endpoints(self):
        """Setup comprehensive health check endpoints"""
        logger.info("🏥 Setting up health check endpoints...")
        
        # Create health check management command
        management_dir = self.base_dir / 'matcher' / 'management' / 'commands'
        
        health_check_command = '''
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
'''
        
        health_command_file = management_dir / 'health_check.py'
        health_command_file.write_text(health_check_command.strip())
        
        logger.info("   ✓ Created health check management command")
        
        # Create health check monitoring script
        monitoring_dir = self.base_dir / 'monitoring'
        
        health_monitor_script = """#!/bin/bash
# HireWise Health Check Monitor

HEALTH_URL="http://localhost:8000/api/health/"
LOG_FILE="/tmp/hirewise-health.log"
ALERT_THRESHOLD=3

check_health() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local response=$(curl -s -w "%{http_code}" -o /tmp/health_response.json "$HEALTH_URL")
    local http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        echo "[$timestamp] HEALTHY - HTTP $http_code" >> "$LOG_FILE"
        return 0
    else
        echo "[$timestamp] UNHEALTHY - HTTP $http_code" >> "$LOG_FILE"
        return 1
    fi
}

# Main monitoring loop
failure_count=0
while true; do
    if check_health; then
        failure_count=0
    else
        failure_count=$((failure_count + 1))
        
        if [ $failure_count -ge $ALERT_THRESHOLD ]; then
            echo "ALERT: HireWise health check failed $failure_count times"
            # Add notification logic here (email, Slack, etc.)
        fi
    fi
    
    sleep 60  # Check every minute
done
"""
        
        health_monitor_file = monitoring_dir / 'health_monitor.sh'
        health_monitor_file.write_text(health_monitor_script.strip())
        health_monitor_file.chmod(0o755)
        
        logger.info("   ✓ Created health monitoring script")
        
        self.success_count += 1
        logger.info("✅ Health check endpoints setup completed")
    
    def create_performance_monitoring(self):
        """Create performance monitoring tools"""
        logger.info("⚡ Setting up performance monitoring...")
        
        monitoring_dir = self.base_dir / 'monitoring'
        
        # Performance monitoring script
        perf_monitor_script = """#!/usr/bin/env python3
import psutil
import time
import json
import requests
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.metrics = []
    
    def collect_system_metrics(self):
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': dict(psutil.net_io_counters()._asdict()),
            'process_count': len(psutil.pids())
        }
    
    def collect_django_metrics(self):
        try:
            response = requests.get('http://localhost:8000/api/health/', timeout=5)
            return {
                'django_status': response.status_code,
                'response_time': response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            return {
                'django_status': 'error',
                'error': str(e)
            }
    
    def collect_redis_metrics(self):
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            info = r.info()
            return {
                'redis_connected_clients': info.get('connected_clients', 0),
                'redis_used_memory': info.get('used_memory', 0),
                'redis_keyspace_hits': info.get('keyspace_hits', 0),
                'redis_keyspace_misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            return {
                'redis_status': 'error',
                'error': str(e)
            }
    
    def run_monitoring(self, duration_minutes=60):
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            metrics = {}
            metrics.update(self.collect_system_metrics())
            metrics.update(self.collect_django_metrics())
            metrics.update(self.collect_redis_metrics())
            
            self.metrics.append(metrics)
            
            # Log metrics
            print(f"[{metrics['timestamp']}] CPU: {metrics['cpu_percent']}% | "
                  f"Memory: {metrics['memory_percent']}% | "
                  f"Django: {metrics.get('django_status', 'unknown')}")
            
            time.sleep(30)  # Collect every 30 seconds
        
        # Save metrics to file
        with open('/tmp/hirewise-performance.json', 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"Performance monitoring completed. Metrics saved to /tmp/hirewise-performance.json")

if __name__ == '__main__':
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    monitor = PerformanceMonitor()
    monitor.run_monitoring(duration)
"""
        
        perf_monitor_file = monitoring_dir / 'performance_monitor.py'
        perf_monitor_file.write_text(perf_monitor_script.strip())
        perf_monitor_file.chmod(0o755)
        
        logger.info("   ✓ Created performance monitoring script")
        
        self.success_count += 1
        logger.info("✅ Performance monitoring setup completed")
    
    def setup_error_tracking(self):
        """Setup error tracking and alerting"""
        logger.info("🚨 Setting up error tracking...")
        
        monitoring_dir = self.base_dir / 'monitoring'
        
        # Error tracking script
        error_tracker_script = """#!/usr/bin/env python3
import re
import json
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class ErrorTracker:
    def __init__(self, log_dir='/home/*/Documents/HireWise/backend/logs'):
        self.log_dir = Path(log_dir).expanduser()
        self.error_patterns = [
            r'ERROR.*',
            r'CRITICAL.*',
            r'Exception.*',
            r'Traceback.*'
        ]
    
    def scan_logs(self, hours_back=1):
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        errors = []
        
        for log_file in self.log_dir.glob('*.log'):
            try:
                with open(log_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern in self.error_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                errors.append({
                                    'file': log_file.name,
                                    'line': line_num,
                                    'content': line.strip(),
                                    'timestamp': datetime.now().isoformat()
                                })
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
        
        return errors
    
    def generate_report(self, errors):
        if not errors:
            return "No errors found in the specified time period."
        
        report = f"HireWise Error Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n"
        report += "=" * 60 + "\\n\\n"
        report += f"Total errors found: {len(errors)}\\n\\n"
        
        # Group by file
        by_file = {}
        for error in errors:
            file_name = error['file']
            if file_name not in by_file:
                by_file[file_name] = []
            by_file[file_name].append(error)
        
        for file_name, file_errors in by_file.items():
            report += f"File: {file_name} ({len(file_errors)} errors)\\n"
            report += "-" * 40 + "\\n"
            for error in file_errors[:5]:  # Show first 5 errors per file
                report += f"Line {error['line']}: {error['content']}\\n"
            if len(file_errors) > 5:
                report += f"... and {len(file_errors) - 5} more errors\\n"
            report += "\\n"
        
        return report
    
    def send_alert(self, report, email_config=None):
        if not email_config:
            print("Email configuration not provided. Printing report:")
            print(report)
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from']
            msg['To'] = email_config['to']
            msg['Subject'] = "HireWise Error Alert"
            
            msg.attach(MIMEText(report, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            print("Error alert sent successfully")
        except Exception as e:
            print(f"Failed to send alert: {e}")
    
    def run_check(self, hours_back=1, email_config=None):
        errors = self.scan_logs(hours_back)
        report = self.generate_report(errors)
        
        if errors:
            self.send_alert(report, email_config)
        
        return len(errors)

if __name__ == '__main__':
    import sys
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    tracker = ErrorTracker()
    error_count = tracker.run_check(hours)
    
    print(f"Error tracking completed. Found {error_count} errors in the last {hours} hour(s).")
"""
        
        error_tracker_file = monitoring_dir / 'error_tracker.py'
        error_tracker_file.write_text(error_tracker_script.strip())
        error_tracker_file.chmod(0o755)
        
        logger.info("   ✓ Created error tracking script")
        
        self.success_count += 1
        logger.info("✅ Error tracking setup completed")
    
    def create_monitoring_dashboard(self):
        """Create monitoring dashboard and summary scripts"""
        logger.info("📊 Creating monitoring dashboard...")
        
        monitoring_dir = self.base_dir / 'monitoring'
        
        # Dashboard script
        dashboard_script = """#!/usr/bin/env python3
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
"""
        
        dashboard_file = monitoring_dir / 'dashboard.py'
        dashboard_file.write_text(dashboard_script.strip())
        dashboard_file.chmod(0o755)
        
        logger.info("   ✓ Created monitoring dashboard")
        
        # Create master monitoring script
        master_script = """#!/bin/bash
# HireWise Master Monitoring Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔍 HireWise Monitoring Suite"
echo "============================"

case "${1:-dashboard}" in
    "dashboard")
        echo "📊 Running monitoring dashboard..."
        python3 "$SCRIPT_DIR/dashboard.py"
        ;;
    "health")
        echo "🏥 Running health checks..."
        cd "$BASE_DIR" && python3 manage.py health_check
        ;;
    "performance")
        echo "⚡ Running performance monitoring..."
        duration=${2:-10}
        python3 "$SCRIPT_DIR/performance_monitor.py" $duration
        ;;
    "errors")
        echo "🚨 Running error tracking..."
        hours=${2:-1}
        python3 "$SCRIPT_DIR/error_tracker.py" $hours
        ;;
    "logs")
        echo "📋 Running log analysis..."
        bash "$SCRIPT_DIR/analyze_logs.sh"
        ;;
    "all")
        echo "🔄 Running all monitoring checks..."
        echo
        python3 "$SCRIPT_DIR/dashboard.py"
        echo
        cd "$BASE_DIR" && python3 manage.py health_check --format=text
        echo
        python3 "$SCRIPT_DIR/error_tracker.py" 1
        ;;
    *)
        echo "Usage: $0 {dashboard|health|performance|errors|logs|all}"
        echo
        echo "Commands:"
        echo "  dashboard    - Show monitoring dashboard (default)"
        echo "  health       - Run health checks"
        echo "  performance  - Run performance monitoring [duration_minutes]"
        echo "  errors       - Run error tracking [hours_back]"
        echo "  logs         - Analyze logs"
        echo "  all          - Run all monitoring checks"
        exit 1
        ;;
esac
"""
        
        master_file = monitoring_dir / 'monitor.sh'
        master_file.write_text(master_script.strip())
        master_file.chmod(0o755)
        
        logger.info("   ✓ Created master monitoring script")
        
        self.success_count += 1
        logger.info("✅ Monitoring dashboard created")


def main():
    """Main setup function"""
    setup = MonitoringSetup()
    setup.run_setup()


if __name__ == '__main__':
    main()