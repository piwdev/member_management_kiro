"""
Signal handlers for permission management.
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.employees.models import Employee
from .services import PermissionService
from .models import PermissionAuditLog

User = get_user_model()


@receiver(pre_save, sender=Employee)
def store_old_employee_data(sender, instance, **kwargs):
    """Store old employee data before saving to track changes."""
    if instance.pk:
        try:
            old_instance = Employee.objects.get(pk=instance.pk)
            instance._old_department = old_instance.department
            instance._old_position = old_instance.position
        except Employee.DoesNotExist:
            instance._old_department = None
            instance._old_position = None
    else:
        instance._old_department = None
        instance._old_position = None


@receiver(post_save, sender=Employee)
def handle_employee_permission_updates(sender, instance, created, **kwargs):
    """Handle automatic permission updates when employee data changes."""
    if not created and hasattr(instance, '_old_department') and hasattr(instance, '_old_position'):
        # Check if department or position changed
        department_changed = instance._old_department != instance.department
        position_changed = instance._old_position != instance.position
        
        if department_changed or position_changed:
            # Update permissions based on role changes
            updated_by = getattr(instance, 'updated_by', None)
            PermissionService.update_employee_permissions(
                employee=instance,
                old_department=instance._old_department,
                old_position=instance._old_position,
                updated_by=updated_by
            )
            
            # Send notification about permission changes
            from .tasks import send_permission_change_notification
            send_permission_change_notification.delay(
                employee_id=str(instance.id),
                old_department=instance._old_department,
                old_position=instance._old_position,
                new_department=instance.department,
                new_position=instance.position
            )