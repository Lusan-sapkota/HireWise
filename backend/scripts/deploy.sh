#!/bin/bash

# =============================================================================
# HireWise Backend Deployment Script
# =============================================================================
# This script automates the deployment process for the HireWise backend
# Usage: ./scripts/deploy.sh [environment] [options]
# =============================================================================

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-development}"
SKIP_TESTS="${2:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command_exists python3; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check pip
    if ! command_exists pip; then
        log_error "pip is not installed"
        exit 1
    fi
    
    # Check environment-specific prerequisites
    if [ "$ENVIRONMENT" = "production" ]; then
        if ! command_exists postgresql; then
            log_warning "PostgreSQL is not installed"
        fi
        
        if ! command_exists redis-server; then
            log_warning "Redis is not installed"
        fi
        
        if ! command_exists nginx; then
            log_warning "Nginx is not installed"
        fi
    fi
    
    log_success "Prerequisites check completed"
}

# Function to setup virtual environment
setup_virtualenv() {
    log_info "Setting up virtual environment..."
    
    cd "$PROJECT_DIR"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    log_success "Virtual environment setup completed"
}

# Function to install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Install Python dependencies
    pip install -r requirements.txt
    
    # Install production-specific dependencies
    if [ "$ENVIRONMENT" = "production" ]; then
        pip install gunicorn whitenoise
    fi
    
    log_success "Dependencies installed"
}

# Function to setup environment configuration
setup_environment() {
    log_info "Setting up environment configuration..."
    
    cd "$PROJECT_DIR"
    
    # Copy environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        cp .env.sample .env
        log_warning "Created .env file from sample. Please update with your values."
    fi
    
    # Validate configuration
    source venv/bin/activate
    python manage.py validate_config
    
    log_success "Environment configuration completed"
}

# Function to setup database
setup_database() {
    log_info "Setting up database..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Run migrations
    python manage.py migrate
    
    # Create superuser if in development
    if [ "$ENVIRONMENT" = "development" ]; then
        if ! python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())" | grep -q "True"; then
            log_info "Creating superuser..."
            python manage.py createsuperuser --noinput --username admin --email admin@hirewise.com || true
        fi
    fi
    
    log_success "Database setup completed"
}

# Function to collect static files
collect_static() {
    log_info "Collecting static files..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    python manage.py collectstatic --noinput
    
    log_success "Static files collected"
}

# Function to run tests
run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        log_warning "Skipping tests"
        return
    fi
    
    log_info "Running tests..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Run tests
    python manage.py test --verbosity=2
    
    log_success "Tests completed"
}

# Function to setup services (production only)
setup_services() {
    if [ "$ENVIRONMENT" != "production" ]; then
        return
    fi
    
    log_info "Setting up production services..."
    
    # Create log directories
    sudo mkdir -p /var/log/hirewise
    sudo chown www-data:www-data /var/log/hirewise
    
    # Setup supervisor configuration
    if command_exists supervisorctl; then
        sudo cp "$SCRIPT_DIR/supervisor/hirewise.conf" /etc/supervisor/conf.d/
        sudo supervisorctl reread
        sudo supervisorctl update
    fi
    
    # Setup nginx configuration
    if command_exists nginx; then
        sudo cp "$SCRIPT_DIR/nginx/hirewise.conf" /etc/nginx/sites-available/
        sudo ln -sf /etc/nginx/sites-available/hirewise.conf /etc/nginx/sites-enabled/
        sudo nginx -t
        sudo systemctl reload nginx
    fi
    
    log_success "Production services setup completed"
}

# Function to start services
start_services() {
    log_info "Starting services..."
    
    cd "$PROJECT_DIR"
    
    if [ "$ENVIRONMENT" = "development" ]; then
        # Development services
        log_info "Starting development server..."
        source venv/bin/activate
        
        # Start Celery in background
        celery -A hirewise worker --loglevel=info --detach
        celery -A hirewise beat --loglevel=info --detach
        
        # Start Django development server
        python manage.py runserver 0.0.0.0:8000
        
    else
        # Production services
        if command_exists supervisorctl; then
            sudo supervisorctl start hirewise:*
        fi
        
        log_success "Production services started"
    fi
}

# Function to perform health check
health_check() {
    log_info "Performing health check..."
    
    # Wait for services to start
    sleep 5
    
    # Check health endpoint
    if curl -f http://localhost:8000/health/ >/dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
}

# Function to create backup
create_backup() {
    if [ "$ENVIRONMENT" != "production" ]; then
        return
    fi
    
    log_info "Creating backup..."
    
    BACKUP_DIR="/var/backups/hirewise"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    sudo mkdir -p "$BACKUP_DIR"
    
    # Database backup
    if command_exists pg_dump; then
        sudo -u postgres pg_dump hirewise_db > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    fi
    
    # Media files backup
    sudo tar -czf "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" "$PROJECT_DIR/media/"
    
    log_success "Backup created"
}

# Function to cleanup old backups
cleanup_backups() {
    if [ "$ENVIRONMENT" != "production" ]; then
        return
    fi
    
    log_info "Cleaning up old backups..."
    
    BACKUP_DIR="/var/backups/hirewise"
    
    # Keep only last 7 days of backups
    find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
    
    log_success "Backup cleanup completed"
}

# Function to display usage
usage() {
    echo "Usage: $0 [environment] [skip_tests]"
    echo ""
    echo "Arguments:"
    echo "  environment    Deployment environment (development|production) [default: development]"
    echo "  skip_tests     Skip running tests (true|false) [default: false]"
    echo ""
    echo "Examples:"
    echo "  $0 development"
    echo "  $0 production true"
    echo ""
}

# Main deployment function
main() {
    log_info "Starting HireWise Backend deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Skip tests: $SKIP_TESTS"
    echo ""
    
    # Validate arguments
    if [ "$ENVIRONMENT" != "development" ] && [ "$ENVIRONMENT" != "production" ]; then
        log_error "Invalid environment: $ENVIRONMENT"
        usage
        exit 1
    fi
    
    # Run deployment steps
    check_prerequisites
    setup_virtualenv
    install_dependencies
    setup_environment
    run_tests
    setup_database
    collect_static
    
    if [ "$ENVIRONMENT" = "production" ]; then
        create_backup
        setup_services
        cleanup_backups
    fi
    
    start_services
    health_check
    
    log_success "Deployment completed successfully!"
    echo ""
    log_info "Next steps:"
    if [ "$ENVIRONMENT" = "development" ]; then
        echo "  - Visit http://localhost:8000/api/docs/ for API documentation"
        echo "  - Visit http://localhost:8000/admin/ for admin interface"
        echo "  - Check http://localhost:8000/health/ for health status"
    else
        echo "  - Configure your domain DNS to point to this server"
        echo "  - Update SSL certificates if needed"
        echo "  - Monitor logs in /var/log/hirewise/"
        echo "  - Set up monitoring and alerting"
    fi
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac