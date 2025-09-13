"""
Serializers for permission models.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PermissionPolicy, PermissionOverride, PermissionAuditLog
from apps.employees.models import Employee

User = get_user_model()


class PermissionPolicySerializer(serializers.ModelSerializer):
    """
    Serializer for PermissionPolicy model.
    """
    
    target_employee_name = serializers.CharField(
        source='target_employee.name',
        read_only=True
    )
    
    created_by_name = serializers.CharField(
        source='created_by.username',
        read_only=True
    )
    
    updated_by_name = serializers.CharField(
        source='updated_by.username',
        read_only=True
    )
    
    policy_type_display = serializers.CharField(
        source='get_policy_type_display',
        read_only=True
    )
    
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    
    is_currently_effective = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PermissionPolicy
        fields = [
            'id', 'name', 'description', 'policy_type', 'policy_type_display',
            'target_department', 'target_position', 'target_employee', 'target_employee_name',
            'priority', 'priority_display', 'allowed_device_types', 'max_devices_per_type',
            'allowed_software', 'restricted_software', 'max_licenses_per_software',
            'is_active', 'effective_from', 'effective_until',
            'auto_approve_requests', 'require_manager_approval',
            'is_currently_effective', 'created_at', 'updated_at',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def validate(self, data):
        """Validate policy data."""
        policy_type = data.get('policy_type')
        
        # Validate policy type specific requirements
        if policy_type == 'DEPARTMENT' and not data.get('target_department'):
            raise serializers.ValidationError({
                'target_department': '部署別ポリシーには対象部署の指定が必要です。'
            })
        
        if policy_type == 'POSITION' and not data.get('target_position'):
            raise serializers.ValidationError({
                'target_position': '役職別ポリシーには対象役職の指定が必要です。'
            })
        
        if policy_type == 'INDIVIDUAL' and not data.get('target_employee'):
            raise serializers.ValidationError({
                'target_employee': '個別ポリシーには対象社員の指定が必要です。'
            })
        
        # Validate effective dates
        effective_from = data.get('effective_from')
        effective_until = data.get('effective_until')
        
        if effective_until and effective_from and effective_from > effective_until:
            raise serializers.ValidationError({
                'effective_until': '有効終了日は有効開始日より後である必要があります。'
            })
        
        return data
    
    def create(self, validated_data):
        """Create permission policy with audit logging."""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        policy = super().create(validated_data)
        
        # Create audit log
        PermissionAuditLog.objects.create(
            action='POLICY_CREATED',
            details={
                'policy_id': str(policy.id),
                'policy_name': policy.name,
                'policy_type': policy.policy_type
            },
            performed_by=request.user if request else None
        )
        
        return policy
    
    def update(self, instance, validated_data):
        """Update permission policy with audit logging."""
        request = self.context.get('request')
        if request and request.user:
            validated_data['updated_by'] = request.user
        
        # Store old values for audit
        old_values = {
            'name': instance.name,
            'policy_type': instance.policy_type,
            'is_active': instance.is_active
        }
        
        policy = super().update(instance, validated_data)
        
        # Create audit log
        PermissionAuditLog.objects.create(
            action='POLICY_UPDATED',
            details={
                'policy_id': str(policy.id),
                'old_values': old_values,
                'new_values': {
                    'name': policy.name,
                    'policy_type': policy.policy_type,
                    'is_active': policy.is_active
                }
            },
            performed_by=request.user if request else None
        )
        
        return policy


class PermissionOverrideSerializer(serializers.ModelSerializer):
    """
    Serializer for PermissionOverride model.
    """
    
    employee_name = serializers.CharField(
        source='employee.name',
        read_only=True
    )
    
    employee_id = serializers.CharField(
        source='employee.employee_id',
        read_only=True
    )
    
    override_type_display = serializers.CharField(
        source='get_override_type_display',
        read_only=True
    )
    
    resource_type_display = serializers.CharField(
        source='get_resource_type_display',
        read_only=True
    )
    
    created_by_name = serializers.CharField(
        source='created_by.username',
        read_only=True
    )
    
    is_currently_effective = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PermissionOverride
        fields = [
            'id', 'employee', 'employee_name', 'employee_id',
            'override_type', 'override_type_display',
            'resource_type', 'resource_type_display', 'resource_identifier',
            'effective_from', 'effective_until', 'reason', 'notes', 'is_active',
            'is_currently_effective', 'created_at', 'updated_at',
            'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def validate(self, data):
        """Validate override data."""
        effective_from = data.get('effective_from')
        effective_until = data.get('effective_until')
        
        if effective_from and effective_until and effective_from > effective_until:
            raise serializers.ValidationError({
                'effective_until': '有効終了日は有効開始日より後である必要があります。'
            })
        
        return data
    
    def create(self, validated_data):
        """Create permission override with audit logging."""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        override = super().create(validated_data)
        
        # Create audit log
        PermissionAuditLog.objects.create(
            action='OVERRIDE_CREATED',
            employee=override.employee,
            resource_type=override.resource_type,
            resource_identifier=override.resource_identifier,
            details={
                'override_id': str(override.id),
                'override_type': override.override_type,
                'reason': override.reason
            },
            performed_by=request.user if request else None
        )
        
        return override


class PermissionAuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for PermissionAuditLog model (read-only).
    """
    
    employee_name = serializers.CharField(
        source='employee.name',
        read_only=True
    )
    
    employee_id = serializers.CharField(
        source='employee.employee_id',
        read_only=True
    )
    
    performed_by_name = serializers.CharField(
        source='performed_by.username',
        read_only=True
    )
    
    action_display = serializers.CharField(
        source='get_action_display',
        read_only=True
    )
    
    class Meta:
        model = PermissionAuditLog
        fields = [
            'id', 'action', 'action_display', 'employee', 'employee_name', 'employee_id',
            'resource_type', 'resource_identifier', 'result', 'details',
            'timestamp', 'performed_by', 'performed_by_name', 'ip_address', 'user_agent'
        ]
        read_only_fields = '__all__'


class EmployeePermissionSummarySerializer(serializers.Serializer):
    """
    Serializer for employee permission summary (read-only).
    """
    
    employee_id = serializers.CharField()
    employee_name = serializers.CharField()
    department = serializers.CharField()
    position = serializers.CharField()
    
    applicable_policies = PermissionPolicySerializer(many=True, read_only=True)
    active_overrides = PermissionOverrideSerializer(many=True, read_only=True)
    
    allowed_device_types = serializers.ListField(child=serializers.CharField(), read_only=True)
    restricted_device_types = serializers.ListField(child=serializers.CharField(), read_only=True)
    allowed_software = serializers.ListField(child=serializers.CharField(), read_only=True)
    restricted_software = serializers.ListField(child=serializers.CharField(), read_only=True)
    
    max_devices_per_type = serializers.DictField(read_only=True)
    max_licenses_per_software = serializers.DictField(read_only=True)
    
    auto_approve_requests = serializers.BooleanField(read_only=True)
    require_manager_approval = serializers.BooleanField(read_only=True)
