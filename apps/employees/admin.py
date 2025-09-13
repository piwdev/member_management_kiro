"""
Django admin configuration for employee models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Employee, EmployeeHistory


class EmployeeHistoryInline(admin.TabularInline):
    """Inline admin for employee history records."""
    
    model = EmployeeHistory
    extra = 0
    readonly_fields = ['change_type', 'field_name', 'old_value', 'new_value', 'changed_by', 'changed_at', 'notes']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Admin interface for Employee model."""
    
    list_display = [
        'employee_id', 'name', 'email', 'department', 'position', 
        'location_display', 'status_display', 'hire_date', 'is_active_display'
    ]
    
    list_filter = [
        'status', 'location', 'department', 'position', 'hire_date', 'created_at'
    ]
    
    search_fields = [
        'employee_id', 'name', 'name_kana', 'email', 'department', 'position'
    ]
    
    readonly_fields = [
        'id', 'is_active', 'full_name_with_kana', 'created_at', 'updated_at',
        'user_link', 'created_by_link', 'updated_by_link'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': (
                'id', 'employee_id', 'user_link', 'name', 'name_kana', 
                'full_name_with_kana', 'email'
            )
        }),
        ('組織情報', {
            'fields': ('department', 'position', 'location')
        }),
        ('雇用情報', {
            'fields': ('hire_date', 'termination_date', 'status', 'is_active')
        }),
        ('連絡先情報', {
            'fields': ('phone_number', 'emergency_contact_name', 'emergency_contact_phone')
        }),
        ('その他', {
            'fields': ('notes',)
        }),
        ('メタデータ', {
            'fields': (
                'created_at', 'updated_at', 'created_by_link', 'updated_by_link'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [EmployeeHistoryInline]
    
    ordering = ['employee_id']
    
    def location_display(self, obj):
        """Display location with Japanese name."""
        return obj.get_location_display()
    location_display.short_description = '勤務地'
    
    def status_display(self, obj):
        """Display status with color coding."""
        if obj.status == 'ACTIVE':
            color = 'green'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'ステータス'
    
    def is_active_display(self, obj):
        """Display active status with icon."""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ アクティブ</span>')
        else:
            return format_html('<span style="color: red;">✗ 非アクティブ</span>')
    is_active_display.short_description = '有効'
    
    def user_link(self, obj):
        """Link to related user account."""
        if obj.user:
            url = reverse('admin:authentication_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = 'ユーザーアカウント'
    
    def created_by_link(self, obj):
        """Link to user who created the employee."""
        if obj.created_by:
            url = reverse('admin:authentication_user_change', args=[obj.created_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.created_by.get_full_name() or obj.created_by.username)
        return '-'
    created_by_link.short_description = '作成者'
    
    def updated_by_link(self, obj):
        """Link to user who last updated the employee."""
        if obj.updated_by:
            url = reverse('admin:authentication_user_change', args=[obj.updated_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.updated_by.get_full_name() or obj.updated_by.username)
        return '-'
    updated_by_link.short_description = '更新者'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'user', 'created_by', 'updated_by'
        )
    
    def save_model(self, request, obj, form, change):
        """Set created_by or updated_by when saving."""
        if not change:  # Creating new object
            obj.created_by = request.user
        else:  # Updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EmployeeHistory)
class EmployeeHistoryAdmin(admin.ModelAdmin):
    """Admin interface for EmployeeHistory model."""
    
    list_display = [
        'employee_link', 'change_type_display', 'field_name', 
        'changed_by_link', 'changed_at'
    ]
    
    list_filter = [
        'change_type', 'changed_at', 'employee__department', 'employee__status'
    ]
    
    search_fields = [
        'employee__name', 'employee__employee_id', 'field_name', 
        'old_value', 'new_value', 'notes'
    ]
    
    readonly_fields = [
        'id', 'employee_link', 'change_type', 'field_name', 'old_value', 
        'new_value', 'changed_by_link', 'changed_at', 'notes'
    ]
    
    fieldsets = (
        ('変更情報', {
            'fields': (
                'id', 'employee_link', 'change_type', 'field_name'
            )
        }),
        ('変更内容', {
            'fields': ('old_value', 'new_value', 'notes')
        }),
        ('メタデータ', {
            'fields': ('changed_by_link', 'changed_at')
        })
    )
    
    ordering = ['-changed_at']
    
    def has_add_permission(self, request):
        """Disable manual creation of history records."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of history records."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deletion of history records."""
        return False
    
    def employee_link(self, obj):
        """Link to related employee."""
        if obj.employee:
            url = reverse('admin:employees_employee_change', args=[obj.employee.id])
            return format_html(
                '<a href="{}">{} ({})</a>', 
                url, 
                obj.employee.name, 
                obj.employee.employee_id
            )
        return '-'
    employee_link.short_description = '社員'
    
    def change_type_display(self, obj):
        """Display change type with color coding."""
        colors = {
            'CREATE': 'blue',
            'UPDATE': 'orange',
            'TERMINATION': 'red',
            'REACTIVATION': 'green',
            'DEPARTMENT_CHANGE': 'purple',
            'POSITION_CHANGE': 'brown',
            'LOCATION_CHANGE': 'teal',
        }
        color = colors.get(obj.change_type, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_change_type_display()
        )
    change_type_display.short_description = '変更種別'
    
    def changed_by_link(self, obj):
        """Link to user who made the change."""
        if obj.changed_by:
            url = reverse('admin:authentication_user_change', args=[obj.changed_by.id])
            return format_html(
                '<a href="{}">{}</a>', 
                url, 
                obj.changed_by.get_full_name() or obj.changed_by.username
            )
        return '-'
    changed_by_link.short_description = '変更者'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'employee', 'changed_by'
        )
