"""
Admin configuration for dashboard app.
"""

from django.contrib import admin
from .models import ResourceRequest, ReturnRequest, Notification


@admin.register(ResourceRequest)
class ResourceRequestAdmin(admin.ModelAdmin):
    """Admin interface for resource requests."""
    
    list_display = [
        'employee', 'request_type', 'device_type', 'software_name',
        'status', 'priority', 'expected_start_date', 'created_at'
    ]
    
    list_filter = [
        'request_type', 'status', 'priority', 'created_at',
        'expected_start_date', 'employee__department'
    ]
    
    search_fields = [
        'employee__name', 'employee__employee_id',
        'device_type', 'software_name', 'purpose'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'approved_at',
        'fulfilled_at'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': (
                'id', 'request_type', 'employee', 'priority'
            )
        }),
        ('リソース詳細', {
            'fields': (
                'device_type', 'software_name', 'specifications'
            )
        }),
        ('申請内容', {
            'fields': (
                'purpose', 'business_justification', 'expected_usage_period',
                'expected_start_date', 'expected_end_date'
            )
        }),
        ('承認・処理', {
            'fields': (
                'status', 'approved_by', 'approved_at', 'rejection_reason'
            )
        }),
        ('完了情報', {
            'fields': (
                'fulfilled_device', 'fulfilled_license', 'fulfilled_by', 'fulfilled_at'
            )
        }),
        ('備考', {
            'fields': (
                'notes', 'admin_notes'
            )
        }),
        ('メタデータ', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'employee', 'approved_by', 'fulfilled_by',
            'fulfilled_device', 'fulfilled_license'
        )


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    """Admin interface for return requests."""
    
    list_display = [
        'employee', 'request_type', 'get_resource_name',
        'status', 'expected_return_date', 'created_at'
    ]
    
    list_filter = [
        'request_type', 'status', 'created_at',
        'expected_return_date', 'employee__department'
    ]
    
    search_fields = [
        'employee__name', 'employee__employee_id',
        'return_reason', 'device_assignment__device__serial_number',
        'license_assignment__license__software_name'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'processed_at'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': (
                'id', 'request_type', 'employee'
            )
        }),
        ('返却対象', {
            'fields': (
                'device_assignment', 'license_assignment'
            )
        }),
        ('返却詳細', {
            'fields': (
                'expected_return_date', 'return_reason', 'condition_notes'
            )
        }),
        ('処理状況', {
            'fields': (
                'status', 'processed_by', 'processed_at', 'actual_return_date'
            )
        }),
        ('備考', {
            'fields': (
                'notes', 'admin_notes'
            )
        }),
        ('メタデータ', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_resource_name(self, obj):
        """Get the name of the resource being returned."""
        if obj.device_assignment:
            return str(obj.device_assignment.device)
        elif obj.license_assignment:
            return str(obj.license_assignment.license)
        return '-'
    get_resource_name.short_description = 'リソース'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'employee', 'processed_by',
            'device_assignment__device',
            'license_assignment__license'
        )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for notifications."""
    
    list_display = [
        'employee', 'notification_type', 'title', 'priority',
        'status', 'scheduled_at', 'sent_at', 'created_at'
    ]
    
    list_filter = [
        'notification_type', 'priority', 'status', 'created_at',
        'scheduled_at', 'employee__department'
    ]
    
    search_fields = [
        'employee__name', 'employee__employee_id',
        'title', 'message'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'sent_at', 'read_at', 'dismissed_at'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': (
                'id', 'employee', 'notification_type', 'priority'
            )
        }),
        ('通知内容', {
            'fields': (
                'title', 'message'
            )
        }),
        ('関連オブジェクト', {
            'fields': (
                'related_license', 'related_device', 'related_request'
            )
        }),
        ('ステータス', {
            'fields': (
                'status', 'scheduled_at', 'sent_at', 'read_at', 'dismissed_at'
            )
        }),
        ('追加データ', {
            'fields': (
                'data',
            ),
            'classes': ('collapse',)
        }),
        ('メタデータ', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'employee', 'related_license', 'related_device', 'related_request'
        )