# HireWise Backend Deployment Guide

This guide provides comprehensive instructions for deploying the HireWise backend in different environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Development Deployment](#development-deployment)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Health Checks](#health-checks)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **PostgreSQL**: 13 or higher (for production)
- **Redis**: 6 or higher
- **Docker**: 20.10 or higher (for containerized deployment)
- **Docker Compose**: 2.0 or higher

### External Services

- **Google Gemini API**: API key required for resume parsing
- **Email Service**: SMTP credentials for notifications
- **SSL Certificate**: Required for production HTTPS

## Environment Configuration

### 1. Copy Environment File

```bash
cp .env.sample .env
```

### 2. Configure Environment Variables

Edit the `.env` file with your specific values:

#### Core Settings
```bash
SECRET_KEY=your-unique-secret-key-minimum-50-characters-long
DEBUG=False  # Set to False for production
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
ENVIRONMENT=production
```

#### Database Configuration
```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=hirewise_db
DB_USER=hirewise_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

#### Redis Configuration
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
```

#### External Services
```bash
GEMINI_API_KEY=your_google_gemini_api_key
EMAIL_HOST_USER=your_email@domain.com
EMAIL_HOST_PASSWORD=your_app_password
```

### 3. Validate Configuration

```bash
python manage.py validate_config --strict
```

## Development Deployment

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed database (optional)
python manage.py seed_database --users 20 --jobs 50
```

### 3. Start Services

```bash
# Start Redis (if not using Docker)
redis-server

# Start Celery worker (in separate terminal)
celery -A hirewise worker --loglevel=info

# Start Celery beat (in separate terminal)
celery -A hirewise beat --loglevel=info

# Start Django development server
python manage.py runserver
```

### 4. Verify Installation

- Visit `http://localhost:8000/api/health/` for health check
- Visit `http://localhost:8000/api/docs/` for API documentation
- Visit `http://localhost:8000/admin/` for admin interface

## Production Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib redis-server nginx supervisor

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Database Setup

```bash
# Create PostgreSQL user and database
sudo -u postgres psql
CREATE DATABASE hirewise_db;
CREATE USER hirewise_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE hirewise_db TO hirewise_user;
ALTER USER hirewise_user CREATEDB;
\q
```

### 3. Application Setup

```bash
# Create application directory
sudo mkdir -p /var/www/hirewise
sudo chown $USER:$USER /var/www/hirewise
cd /var/www/hirewise

# Clone repository
git clone https://github.com/your-org/hirewise-backend.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Configure environment
cp .env.sample .env
# Edit .env with production values

# Validate configuration
python manage.py validate_config --strict

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

### 4. Configure Gunicorn

Create `/var/www/hirewise/gunicorn.conf.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 5
preload_app = True
user = "www-data"
group = "www-data"
tmp_upload_dir = None
errorlog = "/var/www/hirewise/logs/gunicorn_error.log"
accesslog = "/var/www/hirewise/logs/gunicorn_access.log"
loglevel = "info"
```

### 5. Configure Supervisor

Create `/etc/supervisor/conf.d/hirewise.conf`:

```ini
[program:hirewise_web]
command=/var/www/hirewise/venv/bin/gunicorn --config /var/www/hirewise/gunicorn.conf.py hirewise.wsgi:application
directory=/var/www/hirewise
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/www/hirewise/logs/supervisor_web.log

[program:hirewise_celery]
command=/var/www/hirewise/venv/bin/celery -A hirewise worker --loglevel=info --concurrency=4
directory=/var/www/hirewise
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/www/hirewise/logs/supervisor_celery.log

[program:hirewise_celery_beat]
command=/var/www/hirewise/venv/bin/celery -A hirewise beat --loglevel=info
directory=/var/www/hirewise
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/www/hirewise/logs/supervisor_beat.log
```

### 6. Configure Nginx

Create `/etc/nginx/sites-available/hirewise`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/hirewise/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/hirewise/media/;
        expires 1M;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/hirewise /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Start Services

```bash
# Create log directories
sudo mkdir -p /var/www/hirewise/logs
sudo chown www-data:www-data /var/www/hirewise/logs

# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all

# Enable services
sudo systemctl enable supervisor
sudo systemctl enable nginx
sudo systemctl enable postgresql
sudo systemctl enable redis-server
```

## Docker Deployment

### Development with Docker

```bash
# Start development environment
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Seed database
docker-compose exec web python manage.py seed_database
```

### Production with Docker

```bash
# Copy production environment file
cp .env.sample .env
# Edit .env with production values

# Start production environment
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Health Checks

The application provides several health check endpoints:

- **Basic Health**: `GET /health/` - Simple alive check
- **Detailed Health**: `GET /api/health/` - Comprehensive system check
- **Readiness**: `GET /ready/` - Service ready for traffic
- **Liveness**: `GET /live/` - Service is alive

### Monitoring Integration

Configure your monitoring system to check these endpoints:

```bash
# Basic health check
curl -f http://localhost:8000/health/

# Detailed health check with JSON response
curl -f http://localhost:8000/api/health/ | jq .
```

## Monitoring

### Log Files

- **Application**: `/var/www/hirewise/logs/django.log`
- **Errors**: `/var/www/hirewise/logs/errors.log`
- **Security**: `/var/www/hirewise/logs/security.log`
- **Gunicorn**: `/var/www/hirewise/logs/gunicorn_*.log`
- **Supervisor**: `/var/www/hirewise/logs/supervisor_*.log`

### Performance Monitoring

Monitor these metrics:

- **Response Time**: API endpoint response times
- **Error Rate**: 4xx/5xx error rates
- **Database Performance**: Query times and connection pool
- **Redis Performance**: Cache hit rates and memory usage
- **Celery Tasks**: Task completion rates and queue lengths

### Alerts

Set up alerts for:

- **High Error Rate**: >5% error rate over 5 minutes
- **Slow Response Time**: >2 seconds average response time
- **Database Issues**: Connection failures or slow queries
- **Disk Space**: <10% free space
- **Memory Usage**: >90% memory utilization

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connectivity
python manage.py dbshell

# Validate database configuration
python manage.py validate_config
```

#### 2. Redis Connection Errors

```bash
# Check Redis status
sudo systemctl status redis-server

# Test Redis connection
redis-cli ping

# Check Redis configuration
redis-cli config get "*"
```

#### 3. Celery Issues

```bash
# Check Celery worker status
celery -A hirewise inspect active

# Check Celery beat status
celery -A hirewise inspect scheduled

# Restart Celery services
sudo supervisorctl restart hirewise_celery
sudo supervisorctl restart hirewise_celery_beat
```

#### 4. Static Files Issues

```bash
# Collect static files
python manage.py collectstatic --noinput

# Check static file permissions
ls -la /var/www/hirewise/staticfiles/

# Test static file serving
curl -I http://your-domain.com/static/admin/css/base.css
```

#### 5. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /path/to/cert.pem -text -noout

# Test SSL configuration
curl -I https://your-domain.com

# Check Nginx SSL configuration
sudo nginx -t
```

### Performance Optimization

#### 1. Database Optimization

```sql
-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_jobpost_title_trgm ON matcher_jobpost USING gin (title gin_trgm_ops);
CREATE INDEX CONCURRENTLY idx_jobpost_skills_trgm ON matcher_jobpost USING gin (skills_required gin_trgm_ops);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM matcher_jobpost WHERE title ILIKE '%python%';
```

#### 2. Redis Optimization

```bash
# Monitor Redis memory usage
redis-cli info memory

# Configure Redis memory policy
redis-cli config set maxmemory-policy allkeys-lru
```

#### 3. Application Optimization

```bash
# Profile application performance
python manage.py runserver --settings=hirewise.settings_profiling

# Monitor slow queries
tail -f /var/www/hirewise/logs/django.log | grep "slow query"
```

### Backup and Recovery

#### Database Backup

```bash
# Create backup
pg_dump -h localhost -U hirewise_user hirewise_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql -h localhost -U hirewise_user hirewise_db < backup_20240115_120000.sql
```

#### Media Files Backup

```bash
# Backup media files
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz /var/www/hirewise/media/

# Restore media files
tar -xzf media_backup_20240115_120000.tar.gz -C /var/www/hirewise/
```

## Security Considerations

### 1. Environment Variables

- Never commit `.env` files to version control
- Use strong, unique passwords for all services
- Rotate API keys and passwords regularly

### 2. Network Security

- Use HTTPS in production
- Configure firewall to restrict access
- Use VPN for administrative access

### 3. Application Security

- Keep dependencies updated
- Monitor security advisories
- Implement rate limiting
- Use secure headers

### 4. Data Protection

- Encrypt sensitive data at rest
- Use secure file upload validation
- Implement proper access controls
- Regular security audits

## Support

For deployment issues or questions:

1. Check the logs for error messages
2. Validate configuration with `python manage.py validate_config`
3. Test health endpoints
4. Review this documentation
5. Contact the development team

## Version History

- **v1.0.0**: Initial deployment guide
- **v1.1.0**: Added Docker deployment instructions
- **v1.2.0**: Enhanced monitoring and troubleshooting sections