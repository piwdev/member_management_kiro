"""
Admin interface for permission models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import PermissionPolicy, PermissionOverride, PermissionAuditLog


@admin.register(PermissionPolicy)
class PermissionPolicyAdmin(admin.ModelAdmin):
    """
    Admin interface for PermissionPolicy model.
    """
    
    list_display = [
        'name', 'policy_type', 'target_info', 'priority', 
        'is_active', 'is_currently_effective', 'created_at'
    ]
    
    list_filter = [
        'policy_type', 'is_active', 'priority', 'target_department', 
        'target_position', 'created_at'
    ]
    
    search_fields = [
        'name', 'description', 'target_department', 'target_position',
        'target_employee__name', 'target_employee__employee_id'
    ]
    
    readonly_fields = [
        'id', 'is_currently_effective', 'created_at', 'updated_at',
        'created_by', 'updated_by'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'description', 'policy_type', 'priority', 'is_active')
        }),
        ('対象設定', {
            'fields': ('target_department', 'target_position', 'target_employee')
        }),
        ('端末権限', {
            'fields': ('allowed_device_types', 'max_devices_per_type'),
            'classes': ('collapse',)
        }),
        ('ソフトウェア権限', {
            'fields': ('allowed_software', 'restricted_software', 'max_licenses_per_software'),
            'classes': ('collapse',)
        }),
        ('有効期間', {
            'fields': ('effective_from', 'effective_until')
        }),
        ('承認設定', {
            'fields': ('auto_approve_requests', 'require_manager_approval'),
            'classes': ('collapse',)
        }),
        ('メタデータ', {
            'fields': ('id', 'is_currently_effective', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )
    
    def target_info(self, obj):
        """Display target information based on policy type."""
        if obj.policy_type == 'DEPARTMENT':
            return f"部署: {obj.target_department}"
        elif obj.policy_type == 'POSITION':
            return f"役職: {obj.target_position}"
        elif obj.policy_type == 'INDIVIDUAL':
            return f"社員: {obj.target_employee.name}" if obj.target_employee else "未設定"
        elif obj.policy_type == 'GLOBAL':
            return "全社共通"
        return "未設定"
    
    target_info.short_description = "対象"
    
    def is_currently_effective(self, obj):
        """Display current effectiveness status."""
        if obj.is_currently_effective:
            return format_html('<span style="color: green;">✓ 有効</span>')
        else:
            return format_html('<span style="color: red;">✗ 無効</span>')
    
    is_currently_effective.short_description = "現在の有効性"
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by fields."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PermissionOverride)
class PermissionOverrideAdmin(admin.ModelAdmin):
    """
    Admin interface for PermissionOverride model.
    """
    
    list_display = [
        'employee', 'override_type', 'resource_type', 'resource_identifier',
        'effective_from', 'effective_until', 'is_currently_effective', 'is_active'
    ]
    
    list_filter = [
        'override_type', 'resource_type', 'is_active', 'effective_from', 'effective_until'
    ]
    
    search_fields = [
        'employee__name', 'employee__employee_id', 'resource_identifier', 'reason'
    ]
    
    readonly_fields = [
        'id', 'is_currently_effective', 'created_at', 'updated_at', 'created_by'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('employee', 'override_type', 'resource_type', 'resource_identifier', 'is_active')
        }),
        ('有効期間', {
            'fields': ('effective_from', 'effective_until')
        }),
        ('詳細', {
            'fields': ('reason', 'notes')
        }),
        ('メタデータ', {
            'fields': ('id', 'is_currently_effective', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    def is_currently_effective(self, obj):
        """Display current effectiveness status."""
        if obj.is_currently_effective:
            return format_html('<span style="color: green;">✓ 有効</span>')
        else:
            return format_html('<span style="color: red;">✗ 無効</span>')
    
    is_currently_effective.short_description = "現在の有効性"
    
    def save_model(self, request, obj, form, change):
        """Set created_by field."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PermissionAuditLog)
class PermissionAuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for PermissionAuditLog model (read-only).
    """
    
    list_display = [
        'timestamp', 'action', 'employee', 'resource_type', 
        'resource_identifier', 'result', 'performed_by'
    ]
    
    list_filter = [
        'action', 'resource_type', 'result', 'timestamp'
    ]
    
    search_fields = [
        'employee__name', 'employee__employee_id', 'resource_identifier',
        'performed_by__username'
    ]
    
    readonly_fields = [
        'id', 'action', 'employee', 'resource_type', 'resource_identifier',
        'result', 'details', 'timestamp', 'performed_by', 'ip_address', 'user_agent'
    ]
    
    def has_add_permission(self, request):
        """Disable add permission for audit logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable change permission for audit logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable delete permission for audit logs."""
        return False
