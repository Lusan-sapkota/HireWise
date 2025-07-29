# HireWise Infrastructure Setup Guide

This document provides comprehensive instructions for setting up the HireWise development and production infrastructure.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Redis Server
- PostgreSQL (for production)
- Docker & Docker Compose (optional)

### Development Setup

1. **Clone and Setup Environment**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Development Setup**
   ```bash
   python3 setup_dev_environment.py
   ```

3. **Start Services**
   ```bash
   # Terminal 1: Start Redis
   redis-server
   
   # Terminal 2: Start Celery Worker
   celery -A hirewise worker --loglevel=info
   
   # Terminal 3: Start Django Server
   python3 manage.py runserver
   ```

### Docker Setup

1. **Quick Docker Setup**
   ```bash
   chmod +x docker-setup.sh
   ./docker-setup.sh setup
   ```

2. **Docker Commands**
   ```bash
   ./docker-setup.sh start     # Start services
   ./docker-setup.sh stop      # Stop services
   ./docker-setup.sh logs      # View logs
   ./docker-setup.sh health    # Health check
   ./docker-setup.sh cleanup   # Clean up resources
   ```

## 📊 Monitoring & Logging

### Monitoring Dashboard

```bash
# View comprehensive dashboard
python3 monitoring/dashboard.py

# Or use the master script
./monitoring/monitor.sh dashboard
```

### Health Checks

```bash
# Run health checks
python3 manage.py health_check

# Continuous health monitoring
./monitoring/health_monitor.sh
```

### Performance Monitoring

```bash
# Monitor performance for 30 minutes
python3 monitoring/performance_monitor.py 30

# Or use the master script
./monitoring/monitor.sh performance 30
```

### Error Tracking

```bash
# Check errors in last 2 hours
python3 monitoring/error_tracker.py 2

# Or use the master script
./monitoring/monitor.sh errors 2
```

### Log Analysis

```bash
# Analyze recent logs
./monitoring/analyze_logs.sh

# Or use the master script
./monitoring/monitor.sh logs
```

### All-in-One Monitoring

```bash
# Run all monitoring checks
./monitoring/monitor.sh all
```

## 🗄️ Database Setup

### SQLite (Development)

SQLite is used by default for development. No additional setup required.

### PostgreSQL (Production)

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   ```

2. **Create Database**
   ```sql
   sudo -u postgres psql
   CREATE DATABASE hirewise_db;
   CREATE USER hirewise_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE hirewise_db TO hirewise_user;
   ```

3. **Update Environment**
   ```bash
   # In .env file
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=hirewise_db
   DB_USER=hirewise_user
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

## 🔴 Redis Setup

### Installation

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

### Configuration

Redis is configured in `settings.py` and can be customized via environment variables:

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## 🌿 Celery Setup

### Worker Management

```bash
# Start worker
celery -A hirewise worker --loglevel=info

# Start with specific concurrency
celery -A hirewise worker --loglevel=info --concurrency=4

# Start beat scheduler (for periodic tasks)
celery -A hirewise beat --loglevel=info

# Monitor tasks
celery -A hirewise flower  # Web interface on http://localhost:5555
```

### Task Queues

The system uses multiple queues:

- `ai_processing` - AI/ML tasks (resume parsing, matching)
- `notifications` - Notification sending
- `maintenance` - Cleanup and maintenance tasks

### Helper Scripts

```bash
# Use the generated scripts
./scripts/start_celery_worker.sh
./scripts/start_celery_beat.sh
```

## 📝 Logging Configuration

### Log Files

- `logs/django.log` - General application logs
- `logs/errors.log` - Error logs only
- `logs/security.log` - Security-related events

### Log Rotation

Logrotate configuration is created automatically:

```bash
# Manual log rotation
sudo logrotate -f monitoring/hirewise-logrotate
```

### Structured Logging

The application uses structured JSON logging in production:

```python
from matcher.logging_config import ai_logger, security_logger

# Log AI operations
ai_logger.log_gemini_request('resume_parse', 1024, 2.5, True)

# Log security events
security_logger.log_authentication_attempt('user@example.com', True, '192.168.1.1', 'Mozilla/5.0...')
```

## 🔒 Security Configuration

### Environment Variables

Create `.env` file from `.env.sample`:

```bash
cp .env.sample .env
# Edit .env with your configuration
```

### Key Security Settings

```bash
# Generate secure secret key
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
JWT_REFRESH_TOKEN_LIFETIME=7  # days

# Rate Limiting
RATE_LIMITING_ENABLED=True
RATE_LIMIT_DEFAULT=100  # requests per minute
```

### HTTPS Configuration (Production)

```bash
# In .env for production
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## 🚀 Deployment

### Production Checklist

1. **Environment Configuration**
   ```bash
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   SECRET_KEY=your-production-secret-key
   ```

2. **Database Migration**
   ```bash
   python3 manage.py migrate
   python3 manage.py collectstatic
   ```

3. **Create Superuser**
   ```bash
   python3 manage.py createsuperuser
   ```

4. **Start Services**
   ```bash
   # Using Gunicorn
   gunicorn --bind 0.0.0.0:8000 --workers 3 hirewise.wsgi:application
   
   # Start Celery
   celery -A hirewise worker --loglevel=info --detach
   celery -A hirewise beat --loglevel=info --detach
   ```

### Docker Production

```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/media/;
    }
}
```

## 🔧 Troubleshooting

### Common Issues

1. **Redis Connection Error**
   ```bash
   # Check if Redis is running
   redis-cli ping
   
   # Start Redis if not running
   redis-server
   ```

2. **Database Migration Issues**
   ```bash
   # Reset migrations (development only)
   python3 manage.py migrate matcher zero
   python3 manage.py migrate
   ```

3. **Celery Worker Not Starting**
   ```bash
   # Check broker connection
   celery -A hirewise inspect ping
   
   # Clear task queue
   celery -A hirewise purge
   ```

4. **Permission Errors**
   ```bash
   # Fix log file permissions
   sudo chown -R $USER:$USER logs/
   chmod 644 logs/*.log
   ```

### Debug Mode

Enable debug logging:

```bash
# In .env
DEBUG=True
DJANGO_LOG_LEVEL=DEBUG
```

### Health Check Endpoints

- `GET /api/health/` - Basic health check
- `GET /api/health/detailed/` - Detailed health check
- `GET /api/health/ready/` - Readiness check
- `GET /api/health/live/` - Liveness check

## 📚 API Documentation

Once the server is running, access API documentation at:

- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python3 manage.py test

# Run with coverage
pytest --cov=matcher --cov-report=html

# Run specific test
python3 manage.py test matcher.tests.test_views
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load_tests.py --host=http://localhost:8000
```

## 📞 Support

For issues and questions:

1. Check the logs: `./monitoring/monitor.sh logs`
2. Run health checks: `./monitoring/monitor.sh health`
3. Check the monitoring dashboard: `./monitoring/monitor.sh dashboard`
4. Review this documentation
5. Check the Django admin interface: `http://localhost:8000/admin/`

## 🔄 Maintenance

### Regular Maintenance Tasks

```bash
# Clean up old files (runs automatically via Celery)
python3 manage.py cleanup_files

# Update search indexes
python3 manage.py update_search_indexes

# Generate analytics reports
python3 manage.py generate_analytics_report
```

### Backup

```bash
# Database backup
python3 manage.py dumpdata > backup_$(date +%Y%m%d).json

# Media files backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
```

This infrastructure setup provides a robust, scalable, and maintainable foundation for the HireWise application with comprehensive monitoring, logging, and deployment capabilities.