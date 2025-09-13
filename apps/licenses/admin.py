from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import License, LicenseAssignment


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    """Admin interface for License model."""
    
    list_display = [
        'software_name',
        'license_type',
        'usage_display',
        'pricing_display',
        'expiry_status',
        'created_at',
    ]
    
    list_filter = [
        'pricing_model',
        'expiry_date',
        'created_at',
        'vendor_name',
    ]
    
    search_fields = [
        'software_name',
        'license_type',
        'vendor_name',
        'description',
    ]
    
    readonly_fields = [
        'id',
        'used_count',
        'usage_percentage',
        'is_fully_utilized',
        'is_expiring_soon',
        'is_expired',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': (
                'software_name',
                'license_type',
                'description',
                'vendor_name',
            )
        }),
        ('ライセンス数', {
            'fields': (
                'total_count',
                'available_count',
                'used_count',
                'usage_percentage',
                'is_fully_utilized',
            )
        }),
        ('有効期限', {
            'fields': (
                'expiry_date',
                'is_expiring_soon',
                'is_expired',
            )
        }),
        ('課金情報', {
            'fields': (
                'pricing_model',
                'unit_price',
                'purchase_date',
            )
        }),
        ('詳細情報', {
            'fields': (
                'license_key',
                'usage_conditions',
                'notes',
            ),
            'classes': ('collapse',),
        }),
        ('メタデータ', {
            'fields': (
                'id',
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def usage_display(self, obj):
        """Display usage information with color coding."""
        percentage = obj.usage_percentage
        color = 'red' if percentage >= 90 else 'orange' if percentage >= 70 else 'green'
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            color,
            obj.used_count,
            obj.total_count,
            round(percentage, 1)
        )
    usage_display.short_description = '利用状況'
    
    def pricing_display(self, obj):
        """Display pricing information."""
        return f"¥{obj.unit_price:,} ({obj.get_pricing_model_display()})"
    pricing_display.short_description = '価格'
    
    def expiry_status(self, obj):
        """Display expiry status with color coding."""
        if obj.is_expired:
            return format_html('<span style="color: red;">期限切れ</span>')
        elif obj.is_expiring_soon():
            return format_html('<span style="color: orange;">期限間近</span>')
        else:
            return format_html('<span style="color: green;">有効</span>')
    expiry_status.short_description = '有効期限状況'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'created_by',
            'updated_by'
        )


@admin.register(LicenseAssignment)
class LicenseAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for LicenseAssignment model."""
    
    list_display = [
        'license_software_name',
        'employee_name',
        'assigned_date',
        'start_date',
        'end_date',
        'status_display',
        'assigned_by',
    ]
    
    list_filter = [
        'status',
        'assigned_date',
        'start_date',
        'license__software_name',
        'employee__department',
        'employee__location',
    ]
    
    search_fields = [
        'license__software_name',
        'employee__name',
        'employee__employee_id',
        'purpose',
    ]
    
    readonly_fields = [
        'id',
        'is_active',
        'is_expiring_soon',
        'calculate_usage_days',
        'created_at',
        'updated_at',
        'revoked_at',
    ]
    
    fieldsets = (
        ('割当情報', {
            'fields': (
                'license',
                'employee',
                'purpose',
            )
        }),
        ('期間', {
            'fields': (
                'assigned_date',
                'start_date',
                'end_date',
                'calculate_usage_days',
            )
        }),
        ('ステータス', {
            'fields': (
                'status',
                'is_active',
                'is_expiring_soon',
            )
        }),
        ('取り消し情報', {
            'fields': (
                'revoked_by',
                'revoked_at',
            ),
            'classes': ('collapse',),
        }),
        ('詳細情報', {
            'fields': (
                'notes',
            ),
            'classes': ('collapse',),
        }),
        ('メタデータ', {
            'fields': (
                'id',
                'created_at',
                'updated_at',
                'assigned_by',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def license_software_name(self, obj):
        """Display license software name with link."""
        url = reverse('admin:licenses_license_change', args=[obj.license.pk])
        return format_html('<a href="{}">{}</a>', url, obj.license.software_name)
    license_software_name.short_description = 'ソフトウェア'
    
    def employee_name(self, obj):
        """Display employee name with link."""
        url = reverse('admin:employees_employee_change', args=[obj.employee.pk])
        return format_html('<a href="{}">{}</a>', url, obj.employee.name)
    employee_name.short_description = '社員'
    
    def status_display(self, obj):
        """Display status with color coding."""
        colors = {
            'ACTIVE': 'green',
            'EXPIRED': 'red',
            'REVOKED': 'orange',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'ステータス'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'license',
            'employee',
            'assigned_by',
            'revoked_by'
        )
    
    actions = ['revoke_assignments']
    
    def revoke_assignments(self, request, queryset):
        """Admin action to revoke selected assignments."""
        count = 0
        for assignment in queryset.filter(status='ACTIVE'):
            try:
                assignment.revoke(revoked_by=request.user, notes="管理者による一括取り消し")
                count += 1
            except Exception as e:
                self.message_user(request, f"割当 {assignment} の取り消しに失敗しました: {e}", level='ERROR')
        
        if count > 0:
            self.message_user(request, f"{count}件の割当を取り消しました。")
    
    revoke_assignments.short_description = "選択された割当を取り消し"
