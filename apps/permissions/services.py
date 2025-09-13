"""
Permission service for handling permission checks and policy evaluation.
"""

from typing import List, Dict, Optional, Tuple
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import PermissionPolicy, PermissionOverride, PermissionAuditLog
from apps.employees.models import Employee

User = get_user_model()


class PermissionService:
    """
    Service class for handling permission checks and policy evaluation.
    """
    
    @staticmethod
    def get_applicable_policies(employee: Employee) -> List[PermissionPolicy]:
        """
        Get all applicable permission policies for an employee, ordered by priority.
        """
        policies = PermissionPolicy.objects.filter(
            is_active=True,
            effective_from__lte=timezone.now().date()
        ).filter(
            Q(effective_until__isnull=True) | Q(effective_until__gte=timezone.now().date())
        ).filter(
            Q(policy_type='GLOBAL') |
            Q(policy_type='DEPARTMENT', target_department=employee.department) |
            Q(policy_type='POSITION', target_position=employee.position) |
            Q(policy_type='INDIVIDUAL', target_employee=employee)
        ).order_by('priority', 'created_at')
        
        return list(policies)
    
    @staticmethod
    def get_active_overrides(employee: Employee) -> List[PermissionOverride]:
        """
        Get all active permission overrides for an employee.
        """
        today = timezone.now().date()
        overrides = PermissionOverride.objects.filter(
            employee=employee,
            is_active=True,
            effective_from__lte=today,
            effective_until__gte=today
        ).order_by('-effective_from')
        
        return list(overrides)
    
    @staticmethod
    def can_access_device_type(employee: Employee, device_type: str, 
                              log_check: bool = True, performed_by: Optional[User] = None) -> Tuple[bool, str]:
        """
        Check if an employee can access a specific device type.
        
        Returns:
            Tuple of (can_access: bool, reason: str)
        """
        # Check overrides first (they have highest priority)
        overrides = PermissionService.get_active_overrides(employee)
        
        for override in overrides:
            if override.resource_type == 'DEVICE' and override.resource_identifier == device_type:
                result = override.override_type == 'GRANT'
                reason = f"オーバーライド: {override.get_override_type_display()}"
                
                if log_check:
                    PermissionAuditLog.objects.create(
                        action='ACCESS_GRANTED' if result else 'ACCESS_DENIED',
                        employee=employee,
                        resource_type='DEVICE',
                        resource_identifier=device_type,
                        result='GRANTED' if result else 'DENIED',
                        details={'reason': reason, 'override_id': str(override.id)},
                        performed_by=performed_by
                    )
                
                return result, reason
        
        # Check policies in priority order
        policies = PermissionService.get_applicable_policies(employee)
        
        for policy in policies:
            # If policy has allowed_device_types defined, check if device_type is in it
            if policy.allowed_device_types:
                if device_type in policy.allowed_device_types:
                    if log_check:
                        PermissionAuditLog.objects.create(
                            action='ACCESS_GRANTED',
                            employee=employee,
                            resource_type='DEVICE',
                            resource_identifier=device_type,
                            result='GRANTED',
                            details={'reason': f'ポリシー: {policy.name}', 'policy_id': str(policy.id)},
                            performed_by=performed_by
                        )
                    return True, f"ポリシー: {policy.name}"
                else:
                    # Device type not in allowed list - deny
                    reason = f"ポリシー制限: {policy.name}"
                    if log_check:
                        PermissionAuditLog.objects.create(
                            action='ACCESS_DENIED',
                            employee=employee,
                            resource_type='DEVICE',
                            resource_identifier=device_type,
                            result='DENIED',
                            details={'reason': reason, 'policy_id': str(policy.id)},
                            performed_by=performed_by
                        )
                    return False, reason
            # If no allowed_device_types defined, allow by default (continue to next policy)
        
        # Default: deny access if no policy explicitly allows
        reason = "該当するポリシーがありません"
        if log_check:
            PermissionAuditLog.objects.create(
                action='ACCESS_DENIED',
                employee=employee,
                resource_type='DEVICE',
                resource_identifier=device_type,
                result='DENIED',
                details={'reason': reason},
                performed_by=performed_by
            )
        
        return False, reason
    
    @staticmethod
    def can_access_software(employee: Employee, software_name: str,
                           log_check: bool = True, performed_by: Optional[User] = None) -> Tuple[bool, str]:
        """
        Check if an employee can access a specific software.
        
        Returns:
            Tuple of (can_access: bool, reason: str)
        """
        # Check overrides first (they have highest priority)
        overrides = PermissionService.get_active_overrides(employee)
        
        for override in overrides:
            if override.resource_type == 'SOFTWARE' and override.resource_identifier == software_name:
                result = override.override_type == 'GRANT'
                reason = f"オーバーライド: {override.get_override_type_display()}"
                
                if log_check:
                    PermissionAuditLog.objects.create(
                        action='ACCESS_GRANTED' if result else 'ACCESS_DENIED',
                        employee=employee,
                        resource_type='SOFTWARE',
                        resource_identifier=software_name,
                        result='GRANTED' if result else 'DENIED',
                        details={'reason': reason, 'override_id': str(override.id)},
                        performed_by=performed_by
                    )
                
                return result, reason
        
        # Check policies in priority order
        policies = PermissionService.get_applicable_policies(employee)
        
        for policy in policies:
            if not policy.can_access_software(software_name):
                # Explicitly restricted by this policy
                reason = f"ポリシー制限: {policy.name}"
                if log_check:
                    PermissionAuditLog.objects.create(
                        action='ACCESS_DENIED',
                        employee=employee,
                        resource_type='SOFTWARE',
                        resource_identifier=software_name,
                        result='DENIED',
                        details={'reason': reason, 'policy_id': str(policy.id)},
                        performed_by=performed_by
                    )
                return False, reason
        
        # If no policy restricts it, check if any policy explicitly allows it
        for policy in policies:
            if policy.can_access_software(software_name):
                reason = f"ポリシー: {policy.name}"
                if log_check:
                    PermissionAuditLog.objects.create(
                        action='ACCESS_GRANTED',
                        employee=employee,
                        resource_type='SOFTWARE',
                        resource_identifier=software_name,
                        result='GRANTED',
                        details={'reason': reason, 'policy_id': str(policy.id)},
                        performed_by=performed_by
                    )
                return True, reason
        
        # Default: allow access if no policy explicitly restricts
        reason = "デフォルト許可"
        if log_check:
            PermissionAuditLog.objects.create(
                action='ACCESS_GRANTED',
                employee=employee,
                resource_type='SOFTWARE',
                resource_identifier=software_name,
                result='GRANTED',
                details={'reason': reason},
                performed_by=performed_by
            )
        
        return True, reason
    
    @staticmethod
    def get_max_devices_for_type(employee: Employee, device_type: str) -> Optional[int]:
        """
        Get the maximum number of devices of a specific type an employee can have.
        """
        policies = PermissionService.get_applicable_policies(employee)
        
        for policy in policies:
            max_devices = policy.get_max_devices_for_type(device_type)
            if max_devices is not None:
                return max_devices
        
        return None  # No limit
    
    @staticmethod
    def get_max_licenses_for_software(employee: Employee, software_name: str) -> Optional[int]:
        """
        Get the maximum number of licenses for a specific software an employee can have.
        """
        policies = PermissionService.get_applicable_policies(employee)
        
        for policy in policies:
            max_licenses = policy.get_max_licenses_for_software(software_name)
            if max_licenses is not None:
                return max_licenses
        
        return None  # No limit
    
    @staticmethod
    def get_employee_permission_summary(employee: Employee) -> Dict:
        """
        Get a comprehensive permission summary for an employee.
        """
        policies = PermissionService.get_applicable_policies(employee)
        overrides = PermissionService.get_active_overrides(employee)
        
        # Collect all allowed and restricted resources
        allowed_device_types = set()
        restricted_device_types = set()
        allowed_software = set()
        restricted_software = set()
        max_devices_per_type = {}
        max_licenses_per_software = {}
        
        # Process policies
        auto_approve = False
        require_manager_approval = True
        
        for policy in policies:
            # Device types
            if policy.allowed_device_types:
                allowed_device_types.update(policy.allowed_device_types)
            
            # Software
            if policy.allowed_software:
                allowed_software.update(policy.allowed_software)
            
            if policy.restricted_software:
                restricted_software.update(policy.restricted_software)
            
            # Limits
            max_devices_per_type.update(policy.max_devices_per_type)
            max_licenses_per_software.update(policy.max_licenses_per_software)
            
            # Approval settings (use the most permissive settings)
            if policy.auto_approve_requests:
                auto_approve = True
            if not policy.require_manager_approval:
                require_manager_approval = False
        
        # Process overrides
        for override in overrides:
            if override.resource_type == 'DEVICE':
                if override.override_type == 'GRANT':
                    allowed_device_types.add(override.resource_identifier)
                    restricted_device_types.discard(override.resource_identifier)
                else:  # RESTRICT
                    restricted_device_types.add(override.resource_identifier)
                    allowed_device_types.discard(override.resource_identifier)
            
            elif override.resource_type == 'SOFTWARE':
                if override.override_type == 'GRANT':
                    allowed_software.add(override.resource_identifier)
                    restricted_software.discard(override.resource_identifier)
                else:  # RESTRICT
                    restricted_software.add(override.resource_identifier)
                    allowed_software.discard(override.resource_identifier)
        
        return {
            'employee_id': employee.employee_id,
            'employee_name': employee.name,
            'department': employee.department,
            'position': employee.position,
            'applicable_policies': policies,
            'active_overrides': overrides,
            'allowed_device_types': list(allowed_device_types),
            'restricted_device_types': list(restricted_device_types),
            'allowed_software': list(allowed_software),
            'restricted_software': list(restricted_software),
            'max_devices_per_type': max_devices_per_type,
            'max_licenses_per_software': max_licenses_per_software,
            'auto_approve_requests': auto_approve,
            'require_manager_approval': require_manager_approval
        }
    
    @staticmethod
    def update_employee_permissions(employee: Employee, old_department: str = None, 
                                  old_position: str = None, updated_by: Optional[User] = None):
        """
        Update employee permissions when their department or position changes.
        This method handles automatic permission updates based on role changes.
        """
        changes = []
        
        if old_department and old_department != employee.department:
            changes.append(f"部署変更: {old_department} → {employee.department}")
        
        if old_position and old_position != employee.position:
            changes.append(f"役職変更: {old_position} → {employee.position}")
        
        if changes:
            # Log the permission update
            PermissionAuditLog.objects.create(
                action='AUTO_UPDATE',
                employee=employee,
                details={
                    'changes': changes,
                    'old_department': old_department,
                    'old_position': old_position,
                    'new_department': employee.department,
                    'new_position': employee.position
                },
                performed_by=updated_by
            )
            
            # Here you could add logic to automatically adjust permissions
            # based on the new role, such as:
            # - Revoking licenses that are no longer allowed
            # - Returning devices that are no longer permitted
            # - Sending notifications about permission changes
            
            return True
        
        return False
    
    @staticmethod
    def check_resource_access_and_log(employee: Employee, resource_type: str, 
                                    resource_identifier: str, performed_by: Optional[User] = None) -> bool:
        """
        Check resource access and log the attempt.
        """
        if resource_type.upper() == 'DEVICE':
            can_access, reason = PermissionService.can_access_device_type(
                employee, resource_identifier, log_check=True, performed_by=performed_by
            )
        elif resource_type.upper() == 'SOFTWARE':
            can_access, reason = PermissionService.can_access_software(
                employee, resource_identifier, log_check=True, performed_by=performed_by
            )
        else:
            # Unknown resource type
            PermissionAuditLog.objects.create(
                action='ACCESS_DENIED',
                employee=employee,
                resource_type=resource_type,
                resource_identifier=resource_identifier,
                result='DENIED',
                details={'reason': '不明なリソース種別'},
                performed_by=performed_by
            )
            return False
        
        return can_access