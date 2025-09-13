"""
Authentication middleware for enhanced security.
"""

import logging
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework import status

logger = logging.getLogger(__name__)
User = get_user_model()


class SecurityLoggingMiddleware:
    """
    Middleware to log security-related events and suspicious activities.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log suspicious activities
        self._log_suspicious_activity(request)
        
        response = self.get_response(request)
        
        # Log authentication events
        self._log_authentication_events(request, response)
        
        return response
    
    def _log_suspicious_activity(self, request):
        """Log potentially suspicious activities."""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = self._get_client_ip(request)
        
        # Log requests with suspicious user agents
        suspicious_agents = [
            'bot', 'crawler', 'spider', 'scraper', 'scanner',
            'sqlmap', 'nikto', 'nmap', 'masscan'
        ]
        
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            logger.warning(
                f"Suspicious user agent detected: {user_agent} from IP: {ip_address}"
            )
        
        # Log requests to sensitive endpoints from unusual IPs
        sensitive_paths = ['/admin/', '/api/auth/', '/api/users/']
        if any(path in request.path for path in sensitive_paths):
            # You could implement IP whitelist checking here
            pass
    
    def _log_authentication_events(self, request, response):
        """Log authentication-related events."""
        if request.path.startswith('/api/auth/'):
            ip_address = self._get_client_ip(request)
            
            if response.status_code == 401:
                logger.warning(
                    f"Authentication failed for path: {request.path} "
                    f"from IP: {ip_address}"
                )
            elif response.status_code == 200 and 'login' in request.path:
                logger.info(
                    f"Successful authentication for path: {request.path} "
                    f"from IP: {ip_address}"
                )
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


class RateLimitMiddleware:
    """
    Simple rate limiting middleware for authentication endpoints.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_cache = {}  # In production, use Redis
        self.max_attempts = 10  # Max attempts per IP per minute
        self.window_size = 60  # 1 minute window
    
    def __call__(self, request):
        # Apply rate limiting to authentication endpoints
        if self._should_rate_limit(request):
            if self._is_rate_limited(request):
                return JsonResponse(
                    {'error': 'レート制限に達しました。しばらく時間をおいてから再試行してください。'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
        
        response = self.get_response(request)
        
        # Track failed authentication attempts
        if self._should_rate_limit(request) and response.status_code == 401:
            self._record_attempt(request)
        
        return response
    
    def _should_rate_limit(self, request):
        """Check if request should be rate limited."""
        return request.path.startswith('/api/auth/login')
    
    def _is_rate_limited(self, request):
        """Check if IP is currently rate limited."""
        ip_address = self._get_client_ip(request)
        current_time = timezone.now().timestamp()
        
        if ip_address not in self.rate_limit_cache:
            return False
        
        attempts = self.rate_limit_cache[ip_address]
        
        # Clean old attempts
        attempts = [
            attempt_time for attempt_time in attempts
            if current_time - attempt_time < self.window_size
        ]
        
        self.rate_limit_cache[ip_address] = attempts
        
        return len(attempts) >= self.max_attempts
    
    def _record_attempt(self, request):
        """Record a failed attempt."""
        ip_address = self._get_client_ip(request)
        current_time = timezone.now().timestamp()
        
        if ip_address not in self.rate_limit_cache:
            self.rate_limit_cache[ip_address] = []
        
        self.rate_limit_cache[ip_address].append(current_time)
        
        # Clean old attempts
        self.rate_limit_cache[ip_address] = [
            attempt_time for attempt_time in self.rate_limit_cache[ip_address]
            if current_time - attempt_time < self.window_size
        ]
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


class SessionSecurityMiddleware:
    """
    Middleware to enhance session security.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Update last login IP for authenticated users
        if request.user.is_authenticated:
            self._update_user_login_info(request)
        
        response = self.get_response(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _update_user_login_info(self, request):
        """Update user's last login IP if it has changed."""
        current_ip = self._get_client_ip(request)
        
        if hasattr(request.user, 'last_login_ip'):
            if request.user.last_login_ip != current_ip:
                request.user.last_login_ip = current_ip
                request.user.save(update_fields=['last_login_ip'])
    
    def _add_security_headers(self, response):
        """Add security headers to response."""
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip