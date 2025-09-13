"""
Security utilities and configurations for production environment.
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils import timezone

logger = logging.getLogger('django.security')


class SecurityUtils:
    """Utility class for security-related functions."""
    
    @staticmethod
    def generate_secure_token(length=32):
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_sensitive_data(data):
        """Hash sensitive data for logging purposes."""
        if not data:
            return None
        return hashlib.sha256(str(data).encode()).hexdigest()[:16]
    
    @staticmethod
    def is_safe_redirect_url(url):
        """Check if a redirect URL is safe."""
        if not url:
            return False
        
        # Only allow relative URLs or URLs from allowed hosts
        if url.startswith('/'):
            return True
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        if not parsed.netloc:
            return True
        
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        return parsed.netloc in allowed_hosts
    
    @staticmethod
    def log_security_event(event_type, user=None, ip_address=None, details=None):
        """Log security events with structured data."""
        log_data = {
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'username': user.username if user else None,
            'ip_address': ip_address,
            'details': details or {}
        }
        
        logger.warning(f"Security Event: {event_type}", extra=log_data)


class RateLimiter:
    """Rate limiting utility for API endpoints."""
    
    def __init__(self, key_prefix='rate_limit', window=60, max_requests=100):
        self.key_prefix = key_prefix
        self.window = window
        self.max_requests = max_requests
    
    def is_allowed(self, identifier):
        """Check if request is allowed based on rate limit."""
        cache_key = f"{self.key_prefix}:{identifier}"
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= self.max_requests:
            return False
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, self.window)
        return True
    
    def get_remaining_requests(self, identifier):
        """Get remaining requests for identifier."""
        cache_key = f"{self.key_prefix}:{identifier}"
        current_requests = cache.get(cache_key, 0)
        return max(0, self.max_requests - current_requests)


class SecurityHeaders:
    """Security headers middleware helper."""
    
    @staticmethod
    def get_security_headers():
        """Get security headers for responses."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Permissions-Policy': (
                'geolocation=(), microphone=(), camera=(), '
                'payment=(), usb=(), magnetometer=(), gyroscope=()'
            ),
        }


class IPWhitelist:
    """IP whitelist utility for admin access."""
    
    def __init__(self):
        self.whitelist = getattr(settings, 'ADMIN_IP_WHITELIST', [])
    
    def is_allowed(self, ip_address):
        """Check if IP address is in whitelist."""
        if not self.whitelist:
            return True  # No whitelist configured
        
        from ipaddress import ip_address as parse_ip, ip_network
        
        try:
            client_ip = parse_ip(ip_address)
            for allowed in self.whitelist:
                if '/' in allowed:
                    # CIDR notation
                    if client_ip in ip_network(allowed, strict=False):
                        return True
                else:
                    # Single IP
                    if client_ip == parse_ip(allowed):
                        return True
        except ValueError:
            # Invalid IP address
            return False
        
        return False


class SessionSecurity:
    """Session security utilities."""
    
    @staticmethod
    def invalidate_user_sessions(user):
        """Invalidate all sessions for a user."""
        from django.contrib.sessions.models import Session
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Get all sessions
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        
        for session in sessions:
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(user.id):
                session.delete()
    
    @staticmethod
    def check_session_security(request):
        """Check session security (IP, user agent, etc.)."""
        session = request.session
        
        # Check IP address consistency
        current_ip = request.META.get('REMOTE_ADDR')
        session_ip = session.get('_session_ip')
        
        if session_ip and session_ip != current_ip:
            SecurityUtils.log_security_event(
                'session_ip_mismatch',
                user=request.user if request.user.is_authenticated else None,
                ip_address=current_ip,
                details={'session_ip': session_ip, 'current_ip': current_ip}
            )
            return False
        
        # Store IP for future checks
        session['_session_ip'] = current_ip
        
        # Check user agent consistency
        current_ua = request.META.get('HTTP_USER_AGENT', '')
        session_ua = session.get('_session_user_agent')
        
        if session_ua and session_ua != current_ua:
            SecurityUtils.log_security_event(
                'session_user_agent_mismatch',
                user=request.user if request.user.is_authenticated else None,
                ip_address=current_ip,
                details={'session_ua': session_ua[:100], 'current_ua': current_ua[:100]}
            )
            return False
        
        # Store user agent for future checks
        session['_session_user_agent'] = current_ua
        
        return True


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def require_https(view_func):
    """Decorator to require HTTPS for a view."""
    def wrapper(request, *args, **kwargs):
        if not request.is_secure() and not settings.DEBUG:
            return HttpResponseForbidden("HTTPS required")
        return view_func(request, *args, **kwargs)
    return wrapper