#!/bin/bash

# =============================================================================
# HireWise Backend Backup Script
# =============================================================================
# This script creates backups of the database and media files
# Usage: ./scripts/backup.sh [backup_type] [retention_days]
# =============================================================================

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_TYPE="${1:-full}"
RETENTION_DAYS="${2:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/hirewise"

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

# Function to create backup directory
create_backup_dir() {
    log_info "Creating backup directory..."
    
    if [ ! -d "$BACKUP_DIR" ]; then
        sudo mkdir -p "$BACKUP_DIR"
        sudo chown $USER:$USER "$BACKUP_DIR"
    fi
    
    log_success "Backup directory ready: $BACKUP_DIR"
}

# Function to backup database
backup_database() {
    log_info "Backing up database..."
    
    # Load environment variables
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
    else
        log_error ".env file not found"
        exit 1
    fi
    
    # Database backup filename
    DB_BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    
    # Create database backup
    if [ "$DB_ENGINE" = "django.db.backends.postgresql" ]; then
        if command_exists pg_dump; then
            PGPASSWORD="$DB_PASSWORD" pg_dump \
                -h "$DB_HOST" \
                -p "$DB_PORT" \
                -U "$DB_USER" \
                -d "$DB_NAME" \
                --no-password \
                --verbose \
                > "$DB_BACKUP_FILE"
            
            # Compress the backup
            gzip "$DB_BACKUP_FILE"
            DB_BACKUP_FILE="$DB_BACKUP_FILE.gz"
            
            log_success "Database backup created: $DB_BACKUP_FILE"
        else
            log_error "pg_dump not found. Please install PostgreSQL client tools."
            exit 1
        fi
    elif [ "$DB_ENGINE" = "django.db.backends.sqlite3" ]; then
        # SQLite backup
        if [ -f "$PROJECT_DIR/$DB_NAME" ]; then
            cp "$PROJECT_DIR/$DB_NAME" "$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"
            gzip "$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"
            log_success "SQLite database backup created"
        else
            log_error "SQLite database file not found: $PROJECT_DIR/$DB_NAME"
            exit 1
        fi
    else
        log_warning "Unsupported database engine: $DB_ENGINE"
    fi
}

# Function to backup media files
backup_media() {
    log_info "Backing up media files..."
    
    MEDIA_DIR="$PROJECT_DIR/media"
    MEDIA_BACKUP_FILE="$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz"
    
    if [ -d "$MEDIA_DIR" ]; then
        tar -czf "$MEDIA_BACKUP_FILE" -C "$PROJECT_DIR" media/
        log_success "Media files backup created: $MEDIA_BACKUP_FILE"
    else
        log_warning "Media directory not found: $MEDIA_DIR"
    fi
}

# Function to backup configuration files
backup_config() {
    log_info "Backing up configuration files..."
    
    CONFIG_BACKUP_FILE="$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz"
    
    # Create temporary directory for config files
    TEMP_CONFIG_DIR=$(mktemp -d)
    
    # Copy configuration files (excluding sensitive data)
    cp "$PROJECT_DIR/.env.sample" "$TEMP_CONFIG_DIR/"
    
    if [ -d "$PROJECT_DIR/nginx" ]; then
        cp -r "$PROJECT_DIR/nginx" "$TEMP_CONFIG_DIR/"
    fi
    
    if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
        cp "$PROJECT_DIR/docker-compose.yml" "$TEMP_CONFIG_DIR/"
    fi
    
    if [ -f "$PROJECT_DIR/docker-compose.prod.yml" ]; then
        cp "$PROJECT_DIR/docker-compose.prod.yml" "$TEMP_CONFIG_DIR/"
    fi
    
    # Create backup archive
    tar -czf "$CONFIG_BACKUP_FILE" -C "$TEMP_CONFIG_DIR" .
    
    # Cleanup
    rm -rf "$TEMP_CONFIG_DIR"
    
    log_success "Configuration backup created: $CONFIG_BACKUP_FILE"
}

# Function to backup logs
backup_logs() {
    log_info "Backing up logs..."
    
    LOGS_DIR="$PROJECT_DIR/logs"
    LOGS_BACKUP_FILE="$BACKUP_DIR/logs_backup_$TIMESTAMP.tar.gz"
    
    if [ -d "$LOGS_DIR" ]; then
        tar -czf "$LOGS_BACKUP_FILE" -C "$PROJECT_DIR" logs/
        log_success "Logs backup created: $LOGS_BACKUP_FILE"
    else
        log_warning "Logs directory not found: $LOGS_DIR"
    fi
}

# Function to create full backup
create_full_backup() {
    log_info "Creating full backup..."
    
    backup_database
    backup_media
    backup_config
    backup_logs
    
    # Create manifest file
    MANIFEST_FILE="$BACKUP_DIR/backup_manifest_$TIMESTAMP.txt"
    cat > "$MANIFEST_FILE" << EOF
HireWise Backend Backup Manifest
================================
Backup Date: $(date)
Backup Type: Full
Timestamp: $TIMESTAMP

Files included:
- Database backup: db_backup_$TIMESTAMP.sql.gz
- Media files: media_backup_$TIMESTAMP.tar.gz
- Configuration: config_backup_$TIMESTAMP.tar.gz
- Logs: logs_backup_$TIMESTAMP.tar.gz

Restore Instructions:
1. Restore database: gunzip -c db_backup_$TIMESTAMP.sql.gz | psql -U username -d database_name
2. Extract media files: tar -xzf media_backup_$TIMESTAMP.tar.gz
3. Extract configuration: tar -xzf config_backup_$TIMESTAMP.tar.gz
4. Extract logs: tar -xzf logs_backup_$TIMESTAMP.tar.gz
EOF
    
    log_success "Full backup completed. Manifest: $MANIFEST_FILE"
}

# Function to cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    # Find and delete old backup files
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.sqlite3.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.txt" -mtime +$RETENTION_DAYS -delete
    
    log_success "Old backups cleaned up"
}

# Function to list backups
list_backups() {
    log_info "Available backups:"
    
    if [ -d "$BACKUP_DIR" ]; then
        ls -lah "$BACKUP_DIR" | grep -E "\.(sql\.gz|tar\.gz|sqlite3\.gz|txt)$" | sort -k9
    else
        log_warning "Backup directory does not exist: $BACKUP_DIR"
    fi
}

# Function to verify backup integrity
verify_backup() {
    log_info "Verifying backup integrity..."
    
    # Check if backup files exist and are not empty
    BACKUP_VALID=true
    
    # Check database backup
    DB_BACKUP=$(find "$BACKUP_DIR" -name "db_backup_$TIMESTAMP.sql.gz" -o -name "db_backup_$TIMESTAMP.sqlite3.gz" | head -1)
    if [ -f "$DB_BACKUP" ] && [ -s "$DB_BACKUP" ]; then
        log_success "Database backup is valid"
    else
        log_error "Database backup is missing or empty"
        BACKUP_VALID=false
    fi
    
    # Check media backup
    MEDIA_BACKUP="$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz"
    if [ -f "$MEDIA_BACKUP" ]; then
        if tar -tzf "$MEDIA_BACKUP" >/dev/null 2>&1; then
            log_success "Media backup is valid"
        else
            log_error "Media backup is corrupted"
            BACKUP_VALID=false
        fi
    fi
    
    # Check config backup
    CONFIG_BACKUP="$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz"
    if [ -f "$CONFIG_BACKUP" ]; then
        if tar -tzf "$CONFIG_BACKUP" >/dev/null 2>&1; then
            log_success "Configuration backup is valid"
        else
            log_error "Configuration backup is corrupted"
            BACKUP_VALID=false
        fi
    fi
    
    if [ "$BACKUP_VALID" = true ]; then
        log_success "All backups are valid"
    else
        log_error "Some backups are invalid"
        exit 1
    fi
}

# Function to display usage
usage() {
    echo "Usage: $0 [backup_type] [retention_days]"
    echo ""
    echo "Arguments:"
    echo "  backup_type      Type of backup (full|database|media|config|logs|list) [default: full]"
    echo "  retention_days   Number of days to keep backups [default: 7]"
    echo ""
    echo "Examples:"
    echo "  $0 full 7        # Create full backup, keep 7 days"
    echo "  $0 database      # Backup only database"
    echo "  $0 media         # Backup only media files"
    echo "  $0 list          # List available backups"
    echo ""
}

# Main function
main() {
    log_info "Starting HireWise Backend backup..."
    log_info "Backup type: $BACKUP_TYPE"
    log_info "Retention: $RETENTION_DAYS days"
    echo ""
    
    # Create backup directory
    create_backup_dir
    
    # Perform backup based on type
    case "$BACKUP_TYPE" in
        "full")
            create_full_backup
            verify_backup
            cleanup_old_backups
            ;;
        "database")
            backup_database
            cleanup_old_backups
            ;;
        "media")
            backup_media
            cleanup_old_backups
            ;;
        "config")
            backup_config
            cleanup_old_backups
            ;;
        "logs")
            backup_logs
            cleanup_old_backups
            ;;
        "list")
            list_backups
            exit 0
            ;;
        *)
            log_error "Invalid backup type: $BACKUP_TYPE"
            usage
            exit 1
            ;;
    esac
    
    log_success "Backup completed successfully!"
    echo ""
    log_info "Backup location: $BACKUP_DIR"
    log_info "To list all backups: $0 list"
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