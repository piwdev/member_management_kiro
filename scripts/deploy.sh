#!/bin/bash

# Production deployment script for Asset Management System
set -e

echo "Starting deployment process..."

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"
LOG_FILE="./logs/deploy.log"

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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        error "Environment file $ENV_FILE not found"
        error "Please copy .env.production.example to $ENV_FILE and configure it"
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p logs backups ssl
    
    log "Prerequisites check completed"
}

# Backup database
backup_database() {
    log "Creating database backup..."
    
    if docker-compose -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
        BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
        docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "${DB_USER}" -d "${DB_NAME}" > "$BACKUP_FILE"
        
        if [ $? -eq 0 ]; then
            log "Database backup created: $BACKUP_FILE"
        else
            error "Database backup failed"
            exit 1
        fi
    else
        warning "Database container not running, skipping backup"
    fi
}

# Build and deploy
deploy() {
    log "Building and deploying containers..."
    
    # Pull latest images
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Build custom images
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    # Stop existing containers
    docker-compose -f "$COMPOSE_FILE" down
    
    # Start new containers
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log "Containers started"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Wait for database to be ready
    sleep 10
    
    docker-compose -f "$COMPOSE_FILE" exec -T web python manage.py migrate --noinput
    
    if [ $? -eq 0 ]; then
        log "Database migrations completed"
    else
        error "Database migrations failed"
        exit 1
    fi
}

# Collect static files
collect_static() {
    log "Collecting static files..."
    
    docker-compose -f "$COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput
    
    if [ $? -eq 0 ]; then
        log "Static files collected"
    else
        error "Static files collection failed"
        exit 1
    fi
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Wait for services to start
    sleep 30
    
    # Check web service
    if curl -f http://localhost/health/ > /dev/null 2>&1; then
        log "Web service health check passed"
    else
        error "Web service health check failed"
        exit 1
    fi
    
    # Check API
    if curl -f http://localhost/api/health/ > /dev/null 2>&1; then
        log "API health check passed"
    else
        error "API health check failed"
        exit 1
    fi
}

# Cleanup old images and containers
cleanup() {
    log "Cleaning up old Docker images and containers..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused volumes (be careful with this)
    # docker volume prune -f
    
    log "Cleanup completed"
}

# Main deployment process
main() {
    log "Starting Asset Management System deployment"
    
    # Load environment variables
    source "$ENV_FILE"
    
    check_prerequisites
    backup_database
    deploy
    run_migrations
    collect_static
    health_check
    cleanup
    
    log "Deployment completed successfully!"
    log "Application is available at: https://$(hostname)"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "backup")
        source "$ENV_FILE"
        backup_database
        ;;
    "health")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f "${2:-web}"
        ;;
    *)
        echo "Usage: $0 {deploy|backup|health|cleanup|logs [service]}"
        exit 1
        ;;
esac