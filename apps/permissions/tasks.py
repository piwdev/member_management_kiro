"""
Background tasks for permission management.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.employees.models import Employee
from .models import PermissionAuditLog
from .services import PermissionService

User = get_user_model()


@shared_task
def send_permission_change_notification(employee_id, old_department=None, old_position=None, 
                                      new_department=None, new_position=None):
    """
    Send notification about permission changes to the employee and administrators.
    """
    try:
        employee = Employee.objects.get(id=employee_id)
        
        # Get permission summary after changes
        permission_summary = PermissionService.get_employee_permission_summary(employee)
        
        # Prepare context for email template
        context = {
            'employee': employee,
            'old_department': old_department,
            'old_position': old_position,
            'new_department': new_department,
            'new_position': new_position,
            'permission_summary': permission_summary,
        }
        
        # Send notification to employee
        if employee.email:
            subject = f"権限変更のお知らせ - {employee.name}"
            message = render_to_string('permissions/permission_change_notification.txt', context)
            html_message = render_to_string('permissions/permission_change_notification.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[employee.email],
                html_message=html_message,
                fail_silently=False
            )
        
        # Send notification to administrators
        admin_emails = User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True)
        if admin_emails:
            admin_subject = f"社員権限変更通知 - {employee.name} ({employee.employee_id})"
            admin_message = render_to_string('permissions/admin_permission_change_notification.txt', context)
            admin_html_message = render_to_string('permissions/admin_permission_change_notification.html', context)
            
            send_mail(
                subject=admin_subject,
                message=admin_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(admin_emails),
                html_message=admin_html_message,
                fail_silently=False
            )
        
        return f"Permission change notification sent for employee {employee.employee_id}"
        
    except Employee.DoesNotExist:
        return f"Employee with id {employee_id} not found"
    except Exception as e:
        return f"Error sending permission change notification: {str(e)}"


@shared_task
def send_access_denied_notification(employee_id, resource_type, resource_identifier, reason, performed_by_id=None):
    """
    Send notification when access is denied to a resource.
    """
    try:
        employee = Employee.objects.get(id=employee_id)
        performed_by = None
        
        if performed_by_id:
            try:
                performed_by = User.objects.get(id=performed_by_id)
            except User.DoesNotExist:
                pass
        
        context = {
            'employee': employee,
            'resource_type': resource_type,
            'resource_identifier': resource_identifier,
            'reason': reason,
            'performed_by': performed_by,
        }
        
        # Send notification to employee
        if employee.email:
            subject = f"リソースアクセス拒否通知 - {resource_identifier}"
            message = render_to_string('permissions/access_denied_notification.txt', context)
            html_message = render_to_string('permissions/access_denied_notification.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[employee.email],
                html_message=html_message,
                fail_silently=False
            )
        
        # Send notification to administrators for security monitoring
        admin_emails = User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True)
        if admin_emails:
            admin_subject = f"アクセス拒否アラート - {employee.name} ({employee.employee_id})"
            admin_message = render_to_string('permissions/admin_access_denied_notification.txt', context)
            admin_html_message = render_to_string('permissions/admin_access_denied_notification.html', context)
            
            send_mail(
                subject=admin_subject,
                message=admin_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(admin_emails),
                html_message=admin_html_message,
                fail_silently=False
            )
        
        return f"Access denied notification sent for employee {employee.employee_id}"
        
    except Employee.DoesNotExist:
        return f"Employee with id {employee_id} not found"
    except Exception as e:
        return f"Error sending access denied notification: {str(e)}"


@shared_task
def cleanup_expired_overrides():
    """
    Clean up expired permission overrides and audit logs.
    """
    from django.utils import timezone
    from .models import PermissionOverride
    
    try:
        today = timezone.now().date()
        
        # Deactivate expired overrides
        expired_overrides = PermissionOverride.objects.filter(
            is_active=True,
            effective_until__lt=today
        )
        
        count = expired_overrides.count()
        expired_overrides.update(is_active=False)
        
        # Log the cleanup
        PermissionAuditLog.objects.create(
            action='AUTO_UPDATE',
            details={
                'action': 'cleanup_expired_overrides',
                'expired_count': count,
                'cleanup_date': today.isoformat()
            }
        )
        
        return f"Cleaned up {count} expired permission overrides"
        
    except Exception as e:
        return f"Error cleaning up expired overrides: {str(e)}"


@shared_task
def generate_permission_report():
    """
    Generate periodic permission usage report.
    """
    try:
        from django.utils import timezone
        from collections import defaultdict
        
        # Get all active employees
        employees = Employee.objects.filter(status='ACTIVE')
        
        # Generate statistics
        stats = {
            'total_employees': employees.count(),
            'department_breakdown': defaultdict(int),
            'position_breakdown': defaultdict(int),
            'policy_usage': defaultdict(int),
            'override_usage': defaultdict(int),
        }
        
        for employee in employees:
            stats['department_breakdown'][employee.department] += 1
            stats['position_breakdown'][employee.position] += 1
            
            # Get applicable policies
            policies = PermissionService.get_applicable_policies(employee)
            for policy in policies:
                stats['policy_usage'][policy.name] += 1
            
            # Get active overrides
            overrides = PermissionService.get_active_overrides(employee)
            for override in overrides:
                stats['override_usage'][f"{override.resource_type}:{override.resource_identifier}"] += 1
        
        # Convert defaultdict to regular dict for JSON serialization
        stats = {
            'total_employees': stats['total_employees'],
            'department_breakdown': dict(stats['department_breakdown']),
            'position_breakdown': dict(stats['position_breakdown']),
            'policy_usage': dict(stats['policy_usage']),
            'override_usage': dict(stats['override_usage']),
            'generated_at': timezone.now().isoformat()
        }
        
        # Log the report generation
        PermissionAuditLog.objects.create(
            action='AUTO_UPDATE',
            details={
                'action': 'generate_permission_report',
                'stats': stats
            }
        )
        
        return f"Permission report generated successfully"
        
    except Exception as e:
        return f"Error generating permission report: {str(e)}"