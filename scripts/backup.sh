#!/bin/bash

# Database backup script for Asset Management System
set -e

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"
LOG_FILE="./logs/backup.log"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Load environment variables
load_env() {
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
        log "Environment variables loaded from $ENV_FILE"
    else
        error "Environment file $ENV_FILE not found"
        exit 1
    fi
}

# Create backup directory
setup_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"
    log "Backup directory created: $BACKUP_DIR"
}

# Database backup
backup_database() {
    log "Starting database backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/db_backup_$timestamp.sql"
    local compressed_file="$backup_file.gz"
    
    # Check if database container is running
    if ! docker-compose -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
        error "Database container is not running"
        exit 1
    fi
    
    # Create database dump
    log "Creating database dump..."
    docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --no-owner \
        --no-privileges \
        --clean \
        --if-exists > "$backup_file"
    
    if [ $? -eq 0 ]; then
        log "Database dump created: $backup_file"
        
        # Compress the backup
        log "Compressing backup..."
        gzip "$backup_file"
        
        if [ $? -eq 0 ]; then
            log "Backup compressed: $compressed_file"
            
            # Verify backup integrity
            if gunzip -t "$compressed_file" 2>/dev/null; then
                log "Backup integrity verified"
                
                # Get backup size
                local size=$(du -h "$compressed_file" | cut -f1)
                log "Backup size: $size"
                
                return 0
            else
                error "Backup integrity check failed"
                rm -f "$compressed_file"
                exit 1
            fi
        else
            error "Backup compression failed"
            rm -f "$backup_file"
            exit 1
        fi
    else
        error "Database dump failed"
        rm -f "$backup_file"
        exit 1
    fi
}

# Media files backup
backup_media() {
    log "Starting media files backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local media_backup="$BACKUP_DIR/media_backup_$timestamp.tar.gz"
    
    # Check if media directory exists in container
    if docker-compose -f "$COMPOSE_FILE" exec -T web test -d /app/media; then
        log "Creating media files archive..."
        
        docker-compose -f "$COMPOSE_FILE" exec -T web tar -czf - -C /app media > "$media_backup"
        
        if [ $? -eq 0 ] && [ -s "$media_backup" ]; then
            local size=$(du -h "$media_backup" | cut -f1)
            log "Media backup created: $media_backup (Size: $size)"
        else
            warning "Media backup failed or is empty"
            rm -f "$media_backup"
        fi
    else
        warning "Media directory not found, skipping media backup"
    fi
}

# Configuration backup
backup_config() {
    log "Starting configuration backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local config_backup="$BACKUP_DIR/config_backup_$timestamp.tar.gz"
    
    # Backup configuration files (excluding sensitive data)
    tar -czf "$config_backup" \
        --exclude=".env.production" \
        --exclude="*.log" \
        --exclude="backups/*" \
        --exclude="logs/*" \
        --exclude="venv/*" \
        --exclude="node_modules/*" \
        --exclude=".git/*" \
        docker-compose.prod.yml \
        nginx/ \
        scripts/ \
        requirements.txt \
        manage.py \
        asset_management/settings/ \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$config_backup" | cut -f1)
        log "Configuration backup created: $config_backup (Size: $size)"
    else
        warning "Configuration backup failed"
        rm -f "$config_backup"
    fi
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    local deleted_count=0
    
    # Find and delete old backup files
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -type f | while read file; do
        log "Deleting old backup: $file"
        rm -f "$file"
        ((deleted_count++))
    done
    
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -type f | while read file; do
        log "Deleting old backup: $file"
        rm -f "$file"
        ((deleted_count++))
    done
    
    if [ $deleted_count -gt 0 ]; then
        log "Deleted $deleted_count old backup files"
    else
        log "No old backup files to delete"
    fi
}

# Verify backup
verify_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        return 1
    fi
    
    # Check if it's a gzipped SQL file
    if [[ "$backup_file" == *.sql.gz ]]; then
        if gunzip -t "$backup_file" 2>/dev/null; then
            log "Backup verification successful: $backup_file"
            return 0
        else
            error "Backup verification failed: $backup_file"
            return 1
        fi
    fi
    
    # Check if it's a tar.gz file
    if [[ "$backup_file" == *.tar.gz ]]; then
        if tar -tzf "$backup_file" >/dev/null 2>&1; then
            log "Archive verification successful: $backup_file"
            return 0
        else
            error "Archive verification failed: $backup_file"
            return 1
        fi
    fi
    
    warning "Unknown backup file format: $backup_file"
    return 1
}

# Send backup notification (if email is configured)
send_notification() {
    local status="$1"
    local message="$2"
    
    if [ -n "$ADMIN_EMAIL" ] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "Asset Management Backup $status" "$ADMIN_EMAIL"
        log "Notification sent to $ADMIN_EMAIL"
    fi
}

# Main backup process
main() {
    log "Starting Asset Management System backup"
    
    load_env
    setup_backup_dir
    
    local success=true
    local backup_summary=""
    
    # Database backup
    if backup_database; then
        backup_summary+="✓ Database backup completed\n"
    else
        backup_summary+="✗ Database backup failed\n"
        success=false
    fi
    
    # Media backup
    if backup_media; then
        backup_summary+="✓ Media backup completed\n"
    else
        backup_summary+="✗ Media backup failed\n"
    fi
    
    # Configuration backup
    if backup_config; then
        backup_summary+="✓ Configuration backup completed\n"
    else
        backup_summary+="✗ Configuration backup failed\n"
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    backup_summary+="✓ Old backups cleaned up\n"
    
    # Summary
    if [ "$success" = true ]; then
        log "Backup process completed successfully!"
        send_notification "SUCCESS" "Backup completed successfully:\n\n$backup_summary"
    else
        error "Backup process completed with errors!"
        send_notification "FAILED" "Backup completed with errors:\n\n$backup_summary"
        exit 1
    fi
}

# Handle script arguments
case "${1:-full}" in
    "full")
        main
        ;;
    "db")
        load_env
        setup_backup_dir
        backup_database
        ;;
    "media")
        load_env
        setup_backup_dir
        backup_media
        ;;
    "config")
        load_env
        setup_backup_dir
        backup_config
        ;;
    "cleanup")
        load_env
        setup_backup_dir
        cleanup_old_backups
        ;;
    "verify")
        if [ -z "$2" ]; then
            error "Please specify backup file to verify"
            exit 1
        fi
        verify_backup "$2"
        ;;
    *)
        echo "Usage: $0 {full|db|media|config|cleanup|verify <file>}"
        echo ""
        echo "Commands:"
        echo "  full     - Full backup (database, media, config)"
        echo "  db       - Database backup only"
        echo "  media    - Media files backup only"
        echo "  config   - Configuration backup only"
        echo "  cleanup  - Clean up old backups"
        echo "  verify   - Verify backup file integrity"
        exit 1
        ;;
esac