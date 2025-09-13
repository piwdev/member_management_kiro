"""
Django admin configuration for device models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Device, DeviceAssignment


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin interface for Device model."""
    
    list_display = [
        'serial_number',
        'type',
        'manufacturer',
        'model',
        'status',
        'warranty_status_display',
        'current_assignment_display',
        'created_at'
    ]
    
    list_filter = [
        'type',
        'status',
        'manufacturer',
        'created_at',
        'warranty_expiry'
    ]
    
    search_fields = [
        'serial_number',
        'manufacturer',
        'model',
        'assignments__employee__name',
        'assignments__employee__employee_id'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'warranty_status_display',
        'current_assignment_display'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': (
                'id',
                'type',
                'manufacturer',
                'model',
                'serial_number'
            )
        }),
        ('購入・保証情報', {
            'fields': (
                'purchase_date',
                'warranty_expiry',
                'warranty_status_display'
            )
        }),
        ('ステータス', {
            'fields': (
                'status',
                'current_assignment_display'
            )
        }),
        ('追加情報', {
            'fields': (
                'specifications',
                'notes'
            ),
            'classes': ('collapse',)
        }),
        ('メタデータ', {
            'fields': (
                'created_by',
                'updated_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def warranty_status_display(self, obj):
        """Display warranty status with color coding."""
        status = obj.warranty_status
        colors = {
            'VALID': 'green',
            'EXPIRING_SOON': 'orange',
            'EXPIRED': 'red'
        }
        labels = {
            'VALID': '有効',
            'EXPIRING_SOON': '期限間近',
            'EXPIRED': '期限切れ'
        }
        
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(status, 'black'),
            labels.get(status, status)
        )
    warranty_status_display.short_description = '保証状況'
    
    def current_assignment_display(self, obj):
        """Display current assignment information."""
        assignment = obj.current_assignment
        if assignment:
            employee_url = reverse('admin:employees_employee_change', args=[assignment.employee.id])
            return format_html(
                '<a href="{}">{}</a> ({})',
                employee_url,
                assignment.employee.name,
                assignment.assigned_date
            )
        return '-'
    current_assignment_display.short_description = '現在の割当'
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by fields."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class DeviceAssignmentInline(admin.TabularInline):
    """Inline admin for device assignments."""
    
    model = DeviceAssignment
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    
    fields = [
        'employee',
        'assigned_date',
        'expected_return_date',
        'actual_return_date',
        'purpose',
        'status',
        'assigned_by',
        'returned_by'
    ]


@admin.register(DeviceAssignment)
class DeviceAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for DeviceAssignment model."""
    
    list_display = [
        'device',
        'employee',
        'assigned_date',
        'expected_return_date',
        'actual_return_date',
        'status',
        'days_assigned_display',
        'is_overdue'
    ]
    
    list_filter = [
        'status',
        'assigned_date',
        'expected_return_date',
        'device__type',
        'employee__department'
    ]
    
    search_fields = [
        'device__serial_number',
        'device__manufacturer',
        'device__model',
        'employee__name',
        'employee__employee_id',
        'purpose'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'days_assigned_display',
        'is_overdue'
    ]
    
    fieldsets = (
        ('割当情報', {
            'fields': (
                'id',
                'device',
                'employee',
                'purpose'
            )
        }),
        ('日程', {
            'fields': (
                'assigned_date',
                'expected_return_date',
                'actual_return_date',
                'days_assigned_display'
            )
        }),
        ('ステータス', {
            'fields': (
                'status',
                'is_overdue'
            )
        }),
        ('備考', {
            'fields': (
                'assignment_notes',
                'return_notes'
            ),
            'classes': ('collapse',)
        }),
        ('メタデータ', {
            'fields': (
                'assigned_by',
                'returned_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def days_assigned_display(self, obj):
        """Display number of days assigned."""
        return f"{obj.days_assigned}日"
    days_assigned_display.short_description = '割当日数'
    
    def save_model(self, request, obj, form, change):
        """Set assigned_by and returned_by fields."""
        if not change:
            obj.assigned_by = request.user
        if obj.actual_return_date and not obj.returned_by:
            obj.returned_by = request.user
        super().save_model(request, obj, form, change)


# Add inline to DeviceAdmin
DeviceAdmin.inlines = [DeviceAssignmentInline]
