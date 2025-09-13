"""
Middleware for permission-based access control.
"""

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.urls import resolve
from .services import PermissionService
from .models import PermissionAuditLog

User = get_user_model()


class PermissionControlMiddleware(MiddlewareMixin):
    """
    Middleware to enforce permission-based access control on API endpoints.
    """
    
    # URL patterns that require permission checks
    PROTECTED_PATTERNS = {
        'devices': {
            'resource_type': 'DEVICE',
            'methods': ['POST', 'PUT', 'PATCH', 'DELETE']
        },
        'licenses': {
            'resource_type': 'SOFTWARE',
            'methods': ['POST', 'PUT', 'PATCH', 'DELETE']
        }
    }
    
    def process_request(self, request):
        """Process incoming requests for permission checks."""
        # Skip permission checks for certain conditions
        if not self._should_check_permissions(request):
            return None
        
        # Get the URL pattern
        try:
            resolver_match = resolve(request.path_info)
        except:
            return None
        
        # Check if this URL requires permission validation
        app_name = getattr(resolver_match, 'app_name', None)
        url_name = getattr(resolver_match, 'url_name', None)
        
        if not app_name or app_name not in self.PROTECTED_PATTERNS:
            return None
        
        pattern_config = self.PROTECTED_PATTERNS[app_name]
        
        # Check if method requires permission check
        if request.method not in pattern_config['methods']:
            return None
        
        # Get user's employee profile
        if not hasattr(request.user, 'employee_profile'):
            return self._access_denied_response(
                "ユーザーに社員プロファイルが関連付けられていません",
                request
            )
        
        employee = request.user.employee_profile
        resource_type = pattern_config['resource_type']
        
        # Extract resource identifier from request
        resource_identifier = self._extract_resource_identifier(request, app_name)
        
        if not resource_identifier:
            return None  # Cannot determine resource, allow request to proceed
        
        # Check permissions
        can_access = PermissionService.check_resource_access_and_log(
            employee=employee,
            resource_type=resource_type,
            resource_identifier=resource_identifier,
            performed_by=request.user
        )
        
        if not can_access:
            # Send notification about access denial
            from .tasks import send_access_denied_notification
            send_access_denied_notification.delay(
                employee_id=str(employee.id),
                resource_type=resource_type,
                resource_identifier=resource_identifier,
                reason="権限不足",
                performed_by_id=str(request.user.id)
            )
            
            return self._access_denied_response(
                f"{resource_identifier}へのアクセス権限がありません",
                request,
                employee,
                resource_type,
                resource_identifier
            )
        
        return None
    
    def _should_check_permissions(self, request):
        """Determine if permission checks should be performed."""
        # Skip for non-authenticated users
        if not request.user.is_authenticated:
            return False
        
        # Skip for superusers
        if request.user.is_superuser:
            return False
        
        # Skip for safe methods (GET, HEAD, OPTIONS)
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return False
        
        # Skip for admin URLs
        if request.path_info.startswith('/admin/'):
            return False
        
        return True
    
    def _extract_resource_identifier(self, request, app_name):
        """Extract resource identifier from request."""
        if app_name == 'devices':
            # For device operations, extract device type from request data
            if hasattr(request, 'data') and 'type' in request.data:
                return request.data['type']
            elif request.content_type == 'application/json':
                import json
                try:
                    data = json.loads(request.body)
                    return data.get('type')
                except:
                    pass
        
        elif app_name == 'licenses':
            # For license operations, extract software name from request data
            if hasattr(request, 'data') and 'software_name' in request.data:
                return request.data['software_name']
            elif request.content_type == 'application/json':
                import json
                try:
                    data = json.loads(request.body)
                    return data.get('software_name')
                except:
                    pass
        
        return None
    
    def _access_denied_response(self, message, request, employee=None, resource_type=None, resource_identifier=None):
        """Return access denied response."""
        response_data = {
            'error': 'アクセス拒否',
            'message': message,
            'code': 'PERMISSION_DENIED'
        }
        
        # Log the access denial
        if employee:
            PermissionAuditLog.objects.create(
                action='ACCESS_DENIED',
                employee=employee,
                resource_type=resource_type or 'UNKNOWN',
                resource_identifier=resource_identifier or 'UNKNOWN',
                result='DENIED',
                details={
                    'reason': message,
                    'path': request.path_info,
                    'method': request.method
                },
                performed_by=request.user,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        return JsonResponse(response_data, status=403)
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PermissionAuditMiddleware(MiddlewareMixin):
    """
    Middleware to audit all permission-related activities.
    """
    
    def process_response(self, request, response):
        """Log successful operations for audit purposes."""
        # Only log for authenticated users
        if not request.user.is_authenticated:
            return response
        
        # Only log for API endpoints
        if not request.path_info.startswith('/api/'):
            return response
        
        # Only log for successful operations
        if response.status_code not in [200, 201, 204]:
            return response
        
        # Only log for modification operations
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return response
        
        # Get employee profile if available
        employee = None
        if hasattr(request.user, 'employee_profile'):
            employee = request.user.employee_profile
        
        # Log the successful operation
        try:
            resolver_match = resolve(request.path_info)
            app_name = getattr(resolver_match, 'app_name', None)
            url_name = getattr(resolver_match, 'url_name', None)
            
            PermissionAuditLog.objects.create(
                action='PERMISSION_CHECK',
                employee=employee,
                resource_type=app_name.upper() if app_name else 'UNKNOWN',
                resource_identifier=url_name or 'UNKNOWN',
                result='SUCCESS',
                details={
                    'path': request.path_info,
                    'method': request.method,
                    'status_code': response.status_code
                },
                performed_by=request.user,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception:
            # Don't let audit logging break the response
            pass
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip