#!/usr/bin/env python3
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