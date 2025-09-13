#!/bin/bash

# Monitoring script for Asset Management System
set -e

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
LOG_FILE="./logs/monitor.log"
ALERT_EMAIL=""
HEALTH_CHECK_URL="http://localhost/api/health/"
SLACK_WEBHOOK=""

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
        ALERT_EMAIL="${ADMIN_EMAIL:-}"
    fi
}

# Check service health
check_health() {
    log "Checking service health..."
    
    local health_status=0
    
    # Check web service
    if curl -f -s "$HEALTH_CHECK_URL" > /dev/null; then
        log "✓ Web service is healthy"
    else
        error "✗ Web service health check failed"
        health_status=1
    fi
    
    # Check database container
    if docker-compose -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
        log "✓ Database container is running"
    else
        error "✗ Database container is not running"
        health_status=1
    fi
    
    # Check Redis container
    if docker-compose -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
        log "✓ Redis container is running"
    else
        error "✗ Redis container is not running"
        health_status=1
    fi
    
    # Check Nginx container
    if docker-compose -f "$COMPOSE_FILE" ps nginx | grep -q "Up"; then
        log "✓ Nginx container is running"
    else
        error "✗ Nginx container is not running"
        health_status=1
    fi
    
    return $health_status
}

# Check disk space
check_disk_space() {
    log "Checking disk space..."
    
    local threshold=80
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt "$threshold" ]; then
        warning "Disk usage is ${usage}% (threshold: ${threshold}%)"
        return 1
    else
        log "✓ Disk usage is ${usage}%"
        return 0
    fi
}

# Check memory usage
check_memory() {
    log "Checking memory usage..."
    
    local threshold=80
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$usage" -gt "$threshold" ]; then
        warning "Memory usage is ${usage}% (threshold: ${threshold}%)"
        return 1
    else
        log "✓ Memory usage is ${usage}%"
        return 0
    fi
}

# Check container resource usage
check_container_resources() {
    log "Checking container resource usage..."
    
    # Get container stats
    docker-compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}" | tee -a "$LOG_FILE"
    
    # Check for any containers using too much CPU or memory
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | tee -a "$LOG_FILE"
}

# Check log file sizes
check_log_sizes() {
    log "Checking log file sizes..."
    
    local max_size_mb=100
    
    find ./logs -name "*.log" -type f | while read logfile; do
        local size_mb=$(du -m "$logfile" | cut -f1)
        if [ "$size_mb" -gt "$max_size_mb" ]; then
            warning "Log file $logfile is ${size_mb}MB (threshold: ${max_size_mb}MB)"
        else
            log "✓ Log file $logfile is ${size_mb}MB"
        fi
    done
}

# Check SSL certificate expiry
check_ssl_certificate() {
    log "Checking SSL certificate..."
    
    local cert_file="./ssl/cert.pem"
    
    if [ -f "$cert_file" ]; then
        local expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
        local expiry_timestamp=$(date -d "$expiry_date" +%s)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [ "$days_until_expiry" -lt 30 ]; then
            warning "SSL certificate expires in $days_until_expiry days"
            return 1
        else
            log "✓ SSL certificate expires in $days_until_expiry days"
            return 0
        fi
    else
        warning "SSL certificate file not found: $cert_file"
        return 1
    fi
}

# Send alert notification
send_alert() {
    local subject="$1"
    local message="$2"
    
    # Send email alert
    if [ -n "$ALERT_EMAIL" ] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
        log "Alert email sent to $ALERT_EMAIL"
    fi
    
    # Send Slack notification
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$subject\n$message\"}" \
            "$SLACK_WEBHOOK" > /dev/null 2>&1
        log "Slack notification sent"
    fi
}

# Generate system report
generate_report() {
    log "Generating system report..."
    
    local report_file="./logs/system_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "=== ASSET MANAGEMENT SYSTEM REPORT ==="
        echo "Generated: $(date)"
        echo ""
        
        echo "=== SYSTEM INFO ==="
        uname -a
        echo ""
        
        echo "=== DISK USAGE ==="
        df -h
        echo ""
        
        echo "=== MEMORY USAGE ==="
        free -h
        echo ""
        
        echo "=== DOCKER CONTAINERS ==="
        docker-compose -f "$COMPOSE_FILE" ps
        echo ""
        
        echo "=== CONTAINER STATS ==="
        docker stats --no-stream
        echo ""
        
        echo "=== RECENT LOGS ==="
        echo "--- Web Service ---"
        docker-compose -f "$COMPOSE_FILE" logs --tail=20 web
        echo ""
        
        echo "--- Database ---"
        docker-compose -f "$COMPOSE_FILE" logs --tail=20 db
        echo ""
        
        echo "--- Nginx ---"
        docker-compose -f "$COMPOSE_FILE" logs --tail=20 nginx
        echo ""
        
    } > "$report_file"
    
    log "System report generated: $report_file"
}

# Auto-restart unhealthy services
auto_restart() {
    log "Checking for services that need restart..."
    
    # Check if any containers are unhealthy
    local unhealthy_containers=$(docker-compose -f "$COMPOSE_FILE" ps --filter "health=unhealthy" -q)
    
    if [ -n "$unhealthy_containers" ]; then
        warning "Found unhealthy containers, attempting restart..."
        docker-compose -f "$COMPOSE_FILE" restart
        
        # Wait and check again
        sleep 30
        if check_health; then
            log "Services restarted successfully"
            send_alert "Asset Management: Services Restarted" "Unhealthy services were detected and restarted successfully."
        else
            error "Services restart failed"
            send_alert "Asset Management: Restart Failed" "Attempted to restart unhealthy services but health check still failing."
        fi
    else
        log "All containers are healthy"
    fi
}

# Main monitoring function
main() {
    log "Starting Asset Management System monitoring"
    
    load_env
    
    local issues=0
    local warnings=0
    
    # Run all checks
    if ! check_health; then
        ((issues++))
    fi
    
    if ! check_disk_space; then
        ((warnings++))
    fi
    
    if ! check_memory; then
        ((warnings++))
    fi
    
    check_container_resources
    check_log_sizes
    
    if ! check_ssl_certificate; then
        ((warnings++))
    fi
    
    # Summary
    if [ $issues -gt 0 ]; then
        error "Monitoring completed with $issues critical issues and $warnings warnings"
        send_alert "Asset Management: Critical Issues Detected" "Found $issues critical issues and $warnings warnings. Check logs for details."
        exit 1
    elif [ $warnings -gt 0 ]; then
        warning "Monitoring completed with $warnings warnings"
        log "System is operational but has some warnings"
    else
        log "Monitoring completed successfully - all systems healthy"
    fi
}

# Handle script arguments
case "${1:-check}" in
    "check")
        main
        ;;
    "health")
        load_env
        check_health
        ;;
    "restart")
        load_env
        auto_restart
        ;;
    "report")
        load_env
        generate_report
        ;;
    "disk")
        check_disk_space
        ;;
    "memory")
        check_memory
        ;;
    "ssl")
        check_ssl_certificate
        ;;
    *)
        echo "Usage: $0 {check|health|restart|report|disk|memory|ssl}"
        echo ""
        echo "Commands:"
        echo "  check   - Run all monitoring checks"
        echo "  health  - Check service health only"
        echo "  restart - Auto-restart unhealthy services"
        echo "  report  - Generate detailed system report"
        echo "  disk    - Check disk space only"
        echo "  memory  - Check memory usage only"
        echo "  ssl     - Check SSL certificate only"
        exit 1
        ;;
esac