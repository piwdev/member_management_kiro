"""
Utility functions for permission management.
"""

from typing import List, Dict, Optional
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.employees.models import Employee
from .models import PermissionPolicy, PermissionOverride
from .services import PermissionService

User = get_user_model()


def create_department_policy(department: str, allowed_devices: List[str], 
                           allowed_software: List[str], restricted_software: List[str] = None,
                           created_by: Optional[User] = None) -> PermissionPolicy:
    """
    Create a standard department-based permission policy.
    
    Args:
        department: Target department name
        allowed_devices: List of allowed device types
        allowed_software: List of allowed software
        restricted_software: List of restricted software (optional)
        created_by: User creating the policy (optional)
    
    Returns:
        Created PermissionPolicy instance
    """
    policy = PermissionPolicy.objects.create(
        name=f"{department} Department Policy",
        description=f"Standard permission policy for {department} department",
        policy_type='DEPARTMENT',
        target_department=department,
        priority=3,  # Medium priority
        allowed_device_types=allowed_devices,
        allowed_software=allowed_software,
        restricted_software=restricted_software or [],
        created_by=created_by
    )
    
    return policy


def create_position_policy(position: str, allowed_devices: List[str],
                         allowed_software: List[str], max_devices: Dict[str, int] = None,
                         priority: int = 2, created_by: Optional[User] = None) -> PermissionPolicy:
    """
    Create a position-based permission policy.
    
    Args:
        position: Target position name
        allowed_devices: List of allowed device types
        allowed_software: List of allowed software
        max_devices: Dictionary of device type to max count mapping
        priority: Policy priority (1=highest, 5=lowest)
        created_by: User creating the policy (optional)
    
    Returns:
        Created PermissionPolicy instance
    """
    policy = PermissionPolicy.objects.create(
        name=f"{position} Position Policy",
        description=f"Permission policy for {position} position",
        policy_type='POSITION',
        target_position=position,
        priority=priority,
        allowed_device_types=allowed_devices,
        allowed_software=allowed_software,
        max_devices_per_type=max_devices or {},
        created_by=created_by
    )
    
    return policy


def grant_temporary_access(employee: Employee, resource_type: str, resource_identifier: str,
                         days: int, reason: str, created_by: Optional[User] = None) -> PermissionOverride:
    """
    Grant temporary access to a resource for an employee.
    
    Args:
        employee: Target employee
        resource_type: Type of resource ('DEVICE' or 'SOFTWARE')
        resource_identifier: Identifier of the resource
        days: Number of days to grant access
        reason: Reason for granting access
        created_by: User creating the override (optional)
    
    Returns:
        Created PermissionOverride instance
    """
    from datetime import date, timedelta
    
    if resource_type not in ['DEVICE', 'SOFTWARE']:
        raise ValidationError("Resource type must be 'DEVICE' or 'SOFTWARE'")
    
    override = PermissionOverride.objects.create(
        employee=employee,
        override_type='GRANT',
        resource_type=resource_type,
        resource_identifier=resource_identifier,
        effective_from=date.today(),
        effective_until=date.today() + timedelta(days=days),
        reason=reason,
        created_by=created_by
    )
    
    return override


def revoke_access(employee: Employee, resource_type: str, resource_identifier: str,
                 reason: str, created_by: Optional[User] = None) -> PermissionOverride:
    """
    Revoke access to a resource for an employee.
    
    Args:
        employee: Target employee
        resource_type: Type of resource ('DEVICE' or 'SOFTWARE')
        resource_identifier: Identifier of the resource
        reason: Reason for revoking access
        created_by: User creating the override (optional)
    
    Returns:
        Created PermissionOverride instance
    """
    from datetime import date, timedelta
    
    if resource_type not in ['DEVICE', 'SOFTWARE']:
        raise ValidationError("Resource type must be 'DEVICE' or 'SOFTWARE'")
    
    override = PermissionOverride.objects.create(
        employee=employee,
        override_type='RESTRICT',
        resource_type=resource_type,
        resource_identifier=resource_identifier,
        effective_from=date.today(),
        effective_until=date.today() + timedelta(days=365),  # Long-term restriction
        reason=reason,
        created_by=created_by
    )
    
    return override


def bulk_update_department_permissions(old_department: str, new_department: str,
                                     updated_by: Optional[User] = None) -> int:
    """
    Update permissions for all employees when a department is renamed.
    
    Args:
        old_department: Old department name
        new_department: New department name
        updated_by: User performing the update (optional)
    
    Returns:
        Number of employees updated
    """
    employees = Employee.objects.filter(department=old_department, status='ACTIVE')
    count = 0
    
    for employee in employees:
        PermissionService.update_employee_permissions(
            employee=employee,
            old_department=old_department,
            old_position=employee.position,
            updated_by=updated_by
        )
        count += 1
    
    return count


def get_permission_conflicts(employee: Employee) -> List[Dict]:
    """
    Identify permission conflicts for an employee.
    
    Args:
        employee: Employee to check for conflicts
    
    Returns:
        List of conflict descriptions
    """
    conflicts = []
    
    # Get applicable policies and overrides
    policies = PermissionService.get_applicable_policies(employee)
    overrides = PermissionService.get_active_overrides(employee)
    
    # Check for conflicting policies
    for i, policy1 in enumerate(policies):
        for policy2 in policies[i+1:]:
            # Check for device type conflicts
            if policy1.allowed_device_types and policy2.allowed_device_types:
                conflict_devices = set(policy1.allowed_device_types) & set(policy2.allowed_device_types)
                if conflict_devices:
                    conflicts.append({
                        'type': 'POLICY_DEVICE_CONFLICT',
                        'description': f"Policies '{policy1.name}' and '{policy2.name}' both allow devices: {list(conflict_devices)}",
                        'policies': [policy1.name, policy2.name],
                        'resources': list(conflict_devices)
                    })
            
            # Check for software conflicts
            restricted1 = set(policy1.restricted_software)
            allowed2 = set(policy2.allowed_software)
            software_conflicts = restricted1 & allowed2
            
            if software_conflicts:
                conflicts.append({
                    'type': 'POLICY_SOFTWARE_CONFLICT',
                    'description': f"Policy '{policy1.name}' restricts software that '{policy2.name}' allows: {list(software_conflicts)}",
                    'policies': [policy1.name, policy2.name],
                    'resources': list(software_conflicts)
                })
    
    # Check for override conflicts with policies
    for override in overrides:
        for policy in policies:
            if override.resource_type == 'DEVICE':
                if (override.override_type == 'RESTRICT' and 
                    override.resource_identifier in policy.allowed_device_types):
                    conflicts.append({
                        'type': 'OVERRIDE_POLICY_CONFLICT',
                        'description': f"Override restricts '{override.resource_identifier}' but policy '{policy.name}' allows it",
                        'override_id': str(override.id),
                        'policy': policy.name,
                        'resource': override.resource_identifier
                    })
            
            elif override.resource_type == 'SOFTWARE':
                if (override.override_type == 'GRANT' and 
                    override.resource_identifier in policy.restricted_software):
                    conflicts.append({
                        'type': 'OVERRIDE_POLICY_CONFLICT',
                        'description': f"Override grants '{override.resource_identifier}' but policy '{policy.name}' restricts it",
                        'override_id': str(override.id),
                        'policy': policy.name,
                        'resource': override.resource_identifier
                    })
    
    return conflicts


def validate_policy_consistency(policy: PermissionPolicy) -> List[str]:
    """
    Validate that a policy is internally consistent.
    
    Args:
        policy: Policy to validate
    
    Returns:
        List of validation error messages
    """
    errors = []
    
    # Check for software in both allowed and restricted lists
    allowed_software = set(policy.allowed_software)
    restricted_software = set(policy.restricted_software)
    
    conflicts = allowed_software & restricted_software
    if conflicts:
        errors.append(f"Software appears in both allowed and restricted lists: {list(conflicts)}")
    
    # Check for reasonable device limits
    for device_type, max_count in policy.max_devices_per_type.items():
        if device_type not in policy.allowed_device_types:
            errors.append(f"Device limit set for '{device_type}' but device type is not in allowed list")
        
        if max_count <= 0:
            errors.append(f"Invalid device limit for '{device_type}': {max_count}")
    
    # Check for reasonable software limits
    for software, max_count in policy.max_licenses_per_software.items():
        if software in restricted_software:
            errors.append(f"License limit set for restricted software '{software}'")
        
        if max_count <= 0:
            errors.append(f"Invalid license limit for '{software}': {max_count}")
    
    return errors