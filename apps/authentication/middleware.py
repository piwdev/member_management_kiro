"""
Authentication middleware for enhanced security.
"""

import logging
import json
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from rest_framework import status
from asset_management.security import SecurityUtils, get_client_ip

logger = logging.getLogger('apps.authentication')
security_logger = logging.getLogger('django.security')
User = get_user_model()


class SecurityLoggingMiddleware:
    """
    Enhanced middleware to log security-related events and suspicious activities.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.suspicious_agents = [
            'bot', 'crawler', 'spider', 'scraper', 'scanner',
            'sqlmap', 'nikto', 'nmap', 'masscan', 'burp', 'zap'
        ]
        self.sensitive_paths = [
            '/admin/', '/api/auth/', '/api/users/', '/api/employees/',
            '/api/devices/', '/api/licenses/', '/api/permissions/'
        ]
    
    def __call__(self, request):
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Log suspicious activities before processing
        self._log_suspicious_activity(request, ip_address, user_agent)
        
        # Check for blocked IPs
        if self._is_blocked_ip(ip_address):
            SecurityUtils.log_security_event(
                'blocked_ip_access_attempt',
                ip_address=ip_address,
                details={'path': request.path, 'user_agent': user_agent}
            )
            return JsonResponse(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response = self.get_response(request)
        
        # Log authentication events after processing
        self._log_authentication_events(request, response, ip_address)
        
        # Track failed attempts for potential blocking
        self._track_failed_attempts(request, response, ip_address)
        
        return response
    
    def _log_suspicious_activity(self, request, ip_address, user_agent):
        """Log potentially suspicious activities."""
        # Log requests with suspicious user agents
        if any(agent in user_agent.lower() for agent in self.suspicious_agents):
            SecurityUtils.log_security_event(
                'suspicious_user_agent',
                ip_address=ip_address,
                details={
                    'user_agent': user_agent,
                    'path': request.path,
                    'method': request.method
                }
            )
        
        # Log unusual request patterns
        if self._is_unusual_request(request):
            SecurityUtils.log_security_event(
                'unusual_request_pattern',
                ip_address=ip_address,
                details={
                    'path': request.path,
                    'method': request.method,
                    'query_params': dict(request.GET),
                    'content_type': request.content_type
                }
            )
        
        # Log access to sensitive endpoints
        if any(path in request.path for path in self.sensitive_paths):
            logger.info(
                f"Access to sensitive endpoint: {request.path} "
                f"from IP: {ip_address} "
                f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}"
            )
    
    def _log_authentication_events(self, request, response, ip_address):
        """Log authentication-related events."""
        if request.path.startswith('/api/auth/'):
            user = request.user if request.user.is_authenticated else None
            
            if response.status_code == 401:
                SecurityUtils.log_security_event(
                    'authentication_failed',
                    user=user,
                    ip_address=ip_address,
                    details={
                        'path': request.path,
                        'method': request.method,
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
                    }
                )
            elif response.status_code == 200 and 'login' in request.path:
                SecurityUtils.log_security_event(
                    'authentication_success',
                    user=user,
                    ip_address=ip_address,
                    details={
                        'path': request.path,
                        'method': request.method
                    }
                )
            elif response.status_code == 200 and 'logout' in request.path:
                SecurityUtils.log_security_event(
                    'logout',
                    user=user,
                    ip_address=ip_address,
                    details={'path': request.path}
                )
    
    def _is_unusual_request(self, request):
        """Detect unusual request patterns."""
        # Check for SQL injection patterns
        sql_patterns = ['union', 'select', 'drop', 'insert', 'update', 'delete', '--', ';']
        query_string = request.META.get('QUERY_STRING', '').lower()
        
        if any(pattern in query_string for pattern in sql_patterns):
            return True
        
        # Check for XSS patterns
        xss_patterns = ['<script', 'javascript:', 'onerror=', 'onload=']
        if any(pattern in query_string for pattern in xss_patterns):
            return True
        
        # Check for path traversal
        if '../' in request.path or '..\\' in request.path:
            return True
        
        return False
    
    def _is_blocked_ip(self, ip_address):
        """Check if IP is in blocked list."""
        blocked_ips = cache.get('blocked_ips', set())
        return ip_address in blocked_ips
    
    def _track_failed_attempts(self, request, response, ip_address):
        """Track failed attempts and block IPs if necessary."""
        if response.status_code in [401, 403, 429]:
            cache_key = f"failed_attempts:{ip_address}"
            attempts = cache.get(cache_key, 0) + 1
            cache.set(cache_key, attempts, 3600)  # 1 hour
            
            # Block IP after 20 failed attempts
            if attempts >= 20:
                blocked_ips = cache.get('blocked_ips', set())
                blocked_ips.add(ip_address)
                cache.set('blocked_ips', blocked_ips, 86400)  # 24 hours
                
                SecurityUtils.log_security_event(
                    'ip_blocked',
                    ip_address=ip_address,
                    details={'failed_attempts': attempts}
                )


class RateLimitMiddleware:
    """
    Enhanced rate limiting middleware using Redis cache.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            '/api/auth/login': {'max_attempts': 5, 'window': 300},  # 5 attempts per 5 minutes
            '/api/auth/': {'max_attempts': 20, 'window': 300},      # 20 attempts per 5 minutes
            '/api/': {'max_attempts': 100, 'window': 60},           # 100 requests per minute
        }
    
    def __call__(self, request):
        ip_address = get_client_ip(request)
        
        # Check rate limits
        for path_prefix, limits in self.rate_limits.items():
            if request.path.startswith(path_prefix):
                if self._is_rate_limited(ip_address, path_prefix, limits):
                    SecurityUtils.log_security_event(
                        'rate_limit_exceeded',
                        ip_address=ip_address,
                        details={
                            'path': request.path,
                            'limit': limits['max_attempts'],
                            'window': limits['window']
                        }
                    )
                    return JsonResponse(
                        {
                            'error': 'レート制限に達しました。しばらく時間をおいてから再試行してください。',
                            'retry_after': limits['window']
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                break
        
        response = self.get_response(request)
        
        # Record request for rate limiting
        for path_prefix, limits in self.rate_limits.items():
            if request.path.startswith(path_prefix):
                self._record_request(ip_address, path_prefix, limits)
                break
        
        return response
    
    def _is_rate_limited(self, ip_address, path_prefix, limits):
        """Check if IP is currently rate limited for specific path."""
        cache_key = f"rate_limit:{ip_address}:{path_prefix}"
        current_requests = cache.get(cache_key, 0)
        return current_requests >= limits['max_attempts']
    
    def _record_request(self, ip_address, path_prefix, limits):
        """Record a request for rate limiting."""
        cache_key = f"rate_limit:{ip_address}:{path_prefix}"
        current_requests = cache.get(cache_key, 0)
        cache.set(cache_key, current_requests + 1, limits['window'])


class SessionSecurityMiddleware:
    """
    Enhanced middleware for session security and monitoring.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        ip_address = get_client_ip(request)
        
        # Check session security for authenticated users
        if request.user.is_authenticated:
            if not self._check_session_security(request, ip_address):
                # Session security check failed, log out user
                from django.contrib.auth import logout
                logout(request)
                return JsonResponse(
                    {'error': 'セッションセキュリティエラーが発生しました。再度ログインしてください。'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            self._update_user_activity(request, ip_address)
        
        response = self.get_response(request)
        
        # Add comprehensive security headers
        self._add_security_headers(response)
        
        return response
    
    def _check_session_security(self, request, ip_address):
        """Enhanced session security checks."""
        session = request.session
        user = request.user
        
        # Check IP consistency (with some flexibility for mobile users)
        session_ip = session.get('_session_ip')
        if session_ip and session_ip != ip_address:
            # Allow IP changes for the same user but log them
            SecurityUtils.log_security_event(
                'session_ip_change',
                user=user,
                ip_address=ip_address,
                details={
                    'previous_ip': session_ip,
                    'new_ip': ip_address,
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
                }
            )
        
        # Store current IP
        session['_session_ip'] = ip_address
        
        # Check user agent consistency
        current_ua = request.META.get('HTTP_USER_AGENT', '')
        session_ua = session.get('_session_user_agent')
        
        if session_ua and session_ua != current_ua:
            SecurityUtils.log_security_event(
                'session_user_agent_change',
                user=user,
                ip_address=ip_address,
                details={
                    'previous_ua': session_ua[:100],
                    'new_ua': current_ua[:100]
                }
            )
            # User agent changes are more suspicious, but don't auto-logout
            # Just log for monitoring
        
        # Store current user agent
        session['_session_user_agent'] = current_ua
        
        # Check session age
        session_start = session.get('_session_start')
        if not session_start:
            session['_session_start'] = timezone.now().timestamp()
        else:
            session_age = timezone.now().timestamp() - session_start
            max_session_age = getattr(settings, 'MAX_SESSION_AGE', 28800)  # 8 hours
            
            if session_age > max_session_age:
                SecurityUtils.log_security_event(
                    'session_expired',
                    user=user,
                    ip_address=ip_address,
                    details={'session_age': session_age}
                )
                return False
        
        return True
    
    def _update_user_activity(self, request, ip_address):
        """Update user activity information."""
        user = request.user
        
        # Update last activity
        cache_key = f"user_activity:{user.id}"
        activity_data = {
            'last_activity': timezone.now().isoformat(),
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            'path': request.path
        }
        cache.set(cache_key, activity_data, 3600)  # 1 hour
        
        # Update user's last login IP if it has changed
        if hasattr(user, 'last_login_ip') and user.last_login_ip != ip_address:
            user.last_login_ip = ip_address
            user.last_login = timezone.now()
            user.save(update_fields=['last_login_ip', 'last_login'])
    
    def _add_security_headers(self, response):
        """Add comprehensive security headers to response."""
        from asset_management.security import SecurityHeaders
        
        headers = SecurityHeaders.get_security_headers()
        for header, value in headers.items():
            response[header] = value
        
        # Add HSTS header for HTTPS
        if getattr(settings, 'SECURE_SSL_REDIRECT', False):
            response['Strict-Transport-Security'] = (
                f"max-age={getattr(settings, 'SECURE_HSTS_SECONDS', 31536000)}; "
                f"includeSubDomains; preload"
            )
        
        return response