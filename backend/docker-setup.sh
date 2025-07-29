#!/bin/bash

# =============================================================================
# HireWise Docker Development Environment Setup
# =============================================================================
# This script sets up the complete Docker development environment
# =============================================================================

set -e  # Exit on any error

echo "🐳 HireWise Docker Development Environment Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is installed
check_docker() {
    print_info "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed"
}

# Create environment file if it doesn't exist
setup_environment() {
    print_info "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        print_info "Creating .env file from .env.sample..."
        cp .env.sample .env
        
        # Generate a random secret key
        SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
        sed -i "s/your-secret-key-here-change-in-production-minimum-50-chars/$SECRET_KEY/" .env
        
        # Set Docker-specific configurations
        sed -i 's/DB_HOST=localhost/DB_HOST=db/' .env
        sed -i 's/REDIS_HOST=localhost/REDIS_HOST=redis/' .env
        sed -i 's/CELERY_BROKER_URL=redis:\/\/localhost:6379\/1/CELERY_BROKER_URL=redis:\/\/redis:6379\/1/' .env
        sed -i 's/CELERY_RESULT_BACKEND=redis:\/\/localhost:6379\/2/CELERY_RESULT_BACKEND=redis:\/\/redis:6379\/2/' .env
        
        print_status "Environment file created and configured for Docker"
    else
        print_status "Environment file already exists"
    fi
}

# Build Docker images
build_images() {
    print_info "Building Docker images..."
    
    docker-compose build --no-cache
    
    print_status "Docker images built successfully"
}

# Start services
start_services() {
    print_info "Starting Docker services..."
    
    # Start database and Redis first
    print_info "Starting database and Redis..."
    docker-compose up -d db redis
    
    # Wait for services to be ready
    print_info "Waiting for services to be ready..."
    sleep 10
    
    # Check if database is ready
    print_info "Checking database readiness..."
    for i in {1..30}; do
        if docker-compose exec -T db pg_isready -U hirewise_user -d hirewise_db; then
            print_status "Database is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Database failed to start within timeout"
            exit 1
        fi
        sleep 2
    done
    
    # Check if Redis is ready
    print_info "Checking Redis readiness..."
    for i in {1..30}; do
        if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
            print_status "Redis is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Redis failed to start within timeout"
            exit 1
        fi
        sleep 2
    done
    
    print_status "Core services are ready"
}

# Run database migrations
run_migrations() {
    print_info "Running database migrations..."
    
    # Build web service if not already built
    docker-compose build web
    
    # Run migrations
    docker-compose run --rm web python manage.py migrate
    
    print_status "Database migrations completed"
}

# Create superuser
create_superuser() {
    print_info "Creating development superuser..."
    
    # Check if superuser already exists
    if docker-compose run --rm web python manage.py shell -c "
from matcher.models import User
if User.objects.filter(is_superuser=True).exists():
    print('EXISTS')
else:
    print('NOT_EXISTS')
" | grep -q "EXISTS"; then
        print_status "Superuser already exists"
    else
        # Create superuser non-interactively
        docker-compose run --rm web python manage.py shell -c "
from matcher.models import User
User.objects.create_superuser(
    username='admin',
    email='admin@hirewise.dev',
    password='admin123',
    user_type='admin'
)
print('Superuser created successfully')
"
        print_status "Development superuser created (admin/admin123)"
    fi
}

# Start all services
start_all_services() {
    print_info "Starting all services..."
    
    docker-compose up -d
    
    print_status "All services started"
}

# Show service status
show_status() {
    print_info "Service Status:"
    docker-compose ps
    
    echo ""
    print_info "Service URLs:"
    echo "  🌐 Django API: http://localhost:8000"
    echo "  📊 Django Admin: http://localhost:8000/admin"
    echo "  📚 API Documentation: http://localhost:8000/api/schema/swagger-ui/"
    echo "  🏥 Health Check: http://localhost:8000/api/health/"
    echo "  🔴 Redis: localhost:6379"
    echo "  🗄️  PostgreSQL: localhost:5432"
    
    echo ""
    print_info "Development Credentials:"
    echo "  👤 Admin User: admin / admin123"
    echo "  🗄️  Database: hirewise_user / hirewise_password"
}

# Show logs
show_logs() {
    print_info "Recent logs from all services:"
    docker-compose logs --tail=50
}

# Cleanup function
cleanup() {
    print_info "Cleaning up Docker resources..."
    
    docker-compose down -v
    docker system prune -f
    
    print_status "Cleanup completed"
}

# Health check
health_check() {
    print_info "Running health checks..."
    
    # Check if services are running
    if ! docker-compose ps | grep -q "Up"; then
        print_error "Services are not running. Please start them first."
        return 1
    fi
    
    # Check web service health
    if curl -f http://localhost:8000/api/health/ > /dev/null 2>&1; then
        print_status "Web service is healthy"
    else
        print_warning "Web service health check failed"
    fi
    
    # Check database
    if docker-compose exec -T db pg_isready -U hirewise_user -d hirewise_db > /dev/null 2>&1; then
        print_status "Database is healthy"
    else
        print_warning "Database health check failed"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        print_status "Redis is healthy"
    else
        print_warning "Redis health check failed"
    fi
}

# Main setup function
setup() {
    print_info "Starting complete Docker setup..."
    
    check_docker
    setup_environment
    build_images
    start_services
    run_migrations
    create_superuser
    start_all_services
    
    echo ""
    print_status "🎉 Docker development environment setup completed!"
    echo ""
    show_status
    
    echo ""
    print_info "Next steps:"
    echo "  1. Visit http://localhost:8000/admin to access Django admin"
    echo "  2. Visit http://localhost:8000/api/schema/swagger-ui/ for API docs"
    echo "  3. Use 'docker-compose logs -f' to view live logs"
    echo "  4. Use 'docker-compose down' to stop all services"
}

# Command line interface
case "${1:-setup}" in
    "setup")
        setup
        ;;
    "start")
        print_info "Starting services..."
        docker-compose up -d
        show_status
        ;;
    "stop")
        print_info "Stopping services..."
        docker-compose down
        print_status "Services stopped"
        ;;
    "restart")
        print_info "Restarting services..."
        docker-compose restart
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "health")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    "rebuild")
        print_info "Rebuilding and restarting services..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        show_status
        ;;
    *)
        echo "Usage: $0 {setup|start|stop|restart|logs|status|health|cleanup|rebuild}"
        echo ""
        echo "Commands:"
        echo "  setup    - Complete setup (default)"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - Show recent logs"
        echo "  status   - Show service status"
        echo "  health   - Run health checks"
        echo "  cleanup  - Clean up Docker resources"
        echo "  rebuild  - Rebuild and restart services"
        exit 1
        ;;
esac