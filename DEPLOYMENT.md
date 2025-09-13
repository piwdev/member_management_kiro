# Asset Management System - Production Deployment Guide

This guide covers the production deployment of the Asset Management System using Docker Compose with comprehensive security, monitoring, and backup configurations.

## Prerequisites

### System Requirements
- Ubuntu 20.04 LTS or newer (recommended)
- Docker 20.10+ and Docker Compose 2.0+
- Minimum 4GB RAM, 20GB disk space
- SSL certificate for HTTPS
- SMTP server for email notifications (optional)

### Required Software
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt install -y nginx-utils htop curl wget git
```

## Installation

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url> /opt/asset-management
cd /opt/asset-management

# Create necessary directories
sudo mkdir -p /opt/asset-management/{logs,backups,ssl}
sudo chown -R $USER:$USER /opt/asset-management
```

### 2. Environment Configuration
```bash
# Copy and configure environment file
cp .env.production.example .env.production
nano .env.production
```

**Required Environment Variables:**
```bash
# Django Core Settings
SECRET_KEY=your-super-secret-key-here-minimum-50-characters-long
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration
DB_NAME=asset_management_prod
DB_USER=asset_management_user
DB_PASSWORD=your-secure-database-password
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://:your-redis-password@redis:6379/1
REDIS_PASSWORD=your-redis-password

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@company.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@company.com
ADMIN_EMAIL=admin@company.com

# CORS and Security
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# Frontend Configuration
REACT_APP_API_URL=https://yourdomain.com/api
```

### 3. SSL Certificate Setup
```bash
# Option 1: Let's Encrypt (recommended)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/asset-management/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/asset-management/ssl/key.pem
sudo chown $USER:$USER /opt/asset-management/ssl/*

# Option 2: Self-signed certificate (development only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem -out ssl/cert.pem \
    -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Company/CN=yourdomain.com"
```

### 4. Update Nginx Configuration
```bash
# Update domain name in nginx configuration
sed -i 's/your-domain.com/yourdomain.com/g' nginx/default.conf
```

## Deployment

### 1. Initial Deployment
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run initial deployment
./scripts/deploy.sh
```

### 2. Verify Deployment
```bash
# Check service health
./scripts/monitor.sh health

# Check all containers are running
docker-compose -f docker-compose.prod.yml ps

# Test endpoints
curl -k https://yourdomain.com/api/health/
curl -k https://yourdomain.com/health/
```

### 3. Create Admin User
```bash
# Create Django superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Load initial data (optional)
docker-compose -f docker-compose.prod.yml exec web python manage.py loaddata fixtures/test_data.json
```

## Security Configuration

### 1. Firewall Setup
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct access to Django
sudo ufw deny 5432/tcp  # Block direct access to PostgreSQL
sudo ufw deny 6379/tcp  # Block direct access to Redis
```

### 2. System Security
```bash
# Install fail2ban
sudo apt install fail2ban

# Configure fail2ban for nginx
sudo tee /etc/fail2ban/jail.local << EOF
[nginx-http-auth]
enabled = true
port = http,https
logpath = /opt/asset-management/logs/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /opt/asset-management/logs/nginx/error.log
maxretry = 10
EOF

sudo systemctl restart fail2ban
```

### 3. Regular Security Updates
```bash
# Setup automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Monitoring and Maintenance

### 1. Setup Automated Monitoring
```bash
# Install monitoring cron jobs
crontab -e
# Add contents from scripts/crontab.example
```

### 2. Log Management
```bash
# Setup log rotation
sudo tee /etc/logrotate.d/asset-management << EOF
/opt/asset-management/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose -f /opt/asset-management/docker-compose.prod.yml restart nginx
    endscript
}
EOF
```

### 3. Backup Configuration
```bash
# Test backup system
./scripts/backup.sh full

# Verify backup
./scripts/backup.sh verify backups/db_backup_*.sql.gz
```

## Systemd Service (Optional)

### 1. Install Service
```bash
# Copy service file
sudo cp scripts/asset-management.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable asset-management
sudo systemctl start asset-management
```

### 2. Service Management
```bash
# Check service status
sudo systemctl status asset-management

# View logs
sudo journalctl -u asset-management -f

# Restart service
sudo systemctl restart asset-management
```

## Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs web

# Check environment variables
docker-compose -f docker-compose.prod.yml config

# Rebuild containers
docker-compose -f docker-compose.prod.yml build --no-cache
```

#### 2. Database Connection Issues
```bash
# Check database container
docker-compose -f docker-compose.prod.yml logs db

# Test database connection
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell
```

#### 3. SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Test SSL configuration
curl -vI https://yourdomain.com
```

#### 4. Performance Issues
```bash
# Monitor resource usage
./scripts/monitor.sh check

# Check container stats
docker stats

# Analyze slow queries
docker-compose -f docker-compose.prod.yml exec db psql -U $DB_USER -d $DB_NAME -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Log Locations
- Application logs: `./logs/asset_management.log`
- Security logs: `./logs/security.log`
- Error logs: `./logs/errors.log`
- Nginx logs: `./logs/nginx/`
- Backup logs: `./logs/backup.log`
- Monitor logs: `./logs/monitor.log`

## Maintenance Tasks

### Daily
- Monitor system health
- Check backup completion
- Review security logs

### Weekly
- Update system packages
- Clean old log files
- Review performance metrics

### Monthly
- Update SSL certificates (if needed)
- Review and clean old backups
- Security audit
- Performance optimization review

## Scaling Considerations

### Horizontal Scaling
```bash
# Scale web containers
docker-compose -f docker-compose.prod.yml up -d --scale web=3

# Use external load balancer
# Configure nginx upstream with multiple web containers
```

### Database Scaling
```bash
# Setup read replicas
# Configure connection pooling
# Implement database sharding (if needed)
```

### Monitoring at Scale
- Implement centralized logging (ELK stack)
- Use monitoring tools (Prometheus + Grafana)
- Setup alerting (PagerDuty, Slack)

## Support

For issues and support:
1. Check logs in `./logs/` directory
2. Run health checks: `./scripts/monitor.sh check`
3. Review this deployment guide
4. Contact system administrator

## Security Checklist

- [ ] Environment variables configured securely
- [ ] SSL certificates installed and valid
- [ ] Firewall configured properly
- [ ] Database passwords are strong
- [ ] Admin accounts use strong passwords
- [ ] Backup system is working
- [ ] Monitoring is active
- [ ] Log rotation is configured
- [ ] Security updates are automated
- [ ] Access logs are being monitored